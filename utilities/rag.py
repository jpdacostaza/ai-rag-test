"""
RAG (Retrieval-Augmented Generation) implementation for document processing and semantic search.
Handles document ingestion, chunking, embedding, and retrieval for enhanced LLM responses.
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Import feature registry for better dependency tracking
from utilities.feature_registry import feature_registry, register_import_attempt

# Register PDF processing capability
PDF_PROCESSING_AVAILABLE = register_import_attempt(
    "pdf_processing",
    lambda: __import__("PyPDF2"),
    "PDF document processing for RAG ingestion"
)

from services.database_manager import db_manager
from services.database_manager import get_embedding, index_document_chunks
from core.error_handler import log_error
from utilities.simple_error_handling import handle_api_errors
from core.logging_config import get_logger

logger = get_logger(__name__)
from utilities.error_patterns import handle_service_errors, handle_api_errors, ErrorHandlerConfig

# Register memory service availability
MEMORY_SERVICE_AVAILABLE = register_import_attempt(
    "memory_service",
    lambda: __import__("services.memory_service", fromlist=["MemoryService"]),
    "Enhanced memory service for conversation tracking"
)


# RAG configuration constants
# ARM64-optimized settings for Orange Pi 5 Plus and similar devices
import os

# Check if running on ARM64 with optimization flag
ARM64_OPTIMIZED = os.getenv("ARM64_OPTIMIZED", "false").lower() == "true"

if ARM64_OPTIMIZED:
    # Smaller chunks for faster processing on ARM64
    DEFAULT_CHUNK_SIZE = 600
    DEFAULT_CHUNK_OVERLAP = 50
    DEFAULT_SEARCH_LIMIT = 2
    MAX_SEARCH_LIMIT = 10
    logger.info("[RAG] ARM64 optimizations enabled - smaller chunks and reduced limits")
else:
    # Standard settings for x86_64
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200
    DEFAULT_SEARCH_LIMIT = 5
    MAX_SEARCH_LIMIT = 50


class RAGProcessor:
    """
    Handles document processing and semantic search for RAG implementation.
    
    This class provides methods for processing uploaded documents, splitting them
    into chunks, embedding those chunks, storing them in a vector database, and
    retrieving relevant information based on semantic similarity to queries.
    """

    def __init__(self):
        """
        Initialize the RAG processor with a text splitter for document chunking.
        
        The text splitter uses recursive character splitting with a chunk size of 1000
        characters and an overlap of 200 characters to ensure context is preserved
        across chunks.
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=DEFAULT_CHUNK_SIZE,
            chunk_overlap=DEFAULT_CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""])

    @handle_api_errors(
        operation_name="extract_pdf_text")
    def extract_pdf_text(self, file_content: bytes) -> str:
        """
        Extract text from PDF file content.
        
        Args:
            file_content (bytes): The PDF file content as bytes
            
        Returns:
            str: Extracted text from the PDF
            
        Raises:
            Exception: If PDF text extraction fails
        """
        if not PDF_PROCESSING_AVAILABLE:
            raise Exception("PDF processing not available - PyPDF2 not installed")
        
        import io
        import PyPDF2  # Import here after availability check
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page_text
            except Exception as e:
                logging.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                continue
        
        if not text.strip():
            raise Exception("No text could be extracted from PDF")
            
        return text.strip()

    @handle_api_errors(
        operation_name="extract_file_content")
    async def extract_file_content(self, file: UploadFile) -> str:
        """
        Extract text content from uploaded file based on file type.
        
        Args:
            file (UploadFile): The uploaded file
            
        Returns:
            str: Extracted text content
            
        Raises:
            Exception: If content extraction fails
        """
        file_content = await file.read()
        
        # Reset file position for potential re-reading
        await file.seek(0)
        
        # Handle PDF files
        if file.content_type == "application/pdf":
            return self.extract_pdf_text(file_content)
        
        # Handle text-based files (default)
        try:
            return file_content.decode("utf-8")
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                return file_content.decode("latin-1")
            except Exception as e:
                raise Exception(f"Failed to decode text file: {str(e)}")

    @handle_api_errors(
        operation_name="process_document")
    async def process_document(self, file: UploadFile, user_id: str) -> Dict[str, Any]:
        """
        Process uploaded document and store in vector database.
        
        Args:
            file (UploadFile): The uploaded file to process
            user_id (str): The ID of the user uploading the document
            
        Returns:
            Dict[str, Any]: Dictionary containing processing results and status
            
        Raises:
            HTTPException: If document processing fails
        """
        # Basic file validation
        if not file.filename:
            return {
                "document_id": None,
                "filename": "unknown",
                "chunks_processed": 0,
                "total_chunks": 0,
                "status": "failed",
                "error": "Missing filename",
            }
            
        # Check if file type is supported
        supported_extensions = ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.csv', '.xml', '.log', '.pdf']
        file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        # Log file type for debugging
        logging.info(f"[RAG] Processing file: {file.filename}, content_type: {file.content_type}, extension: {file_ext}")
        
        if file_ext and file_ext not in supported_extensions:
            logging.warning(f"[RAG] Potentially unsupported file type: {file_ext}")

        # Extract content based on file type
        text = await self.extract_file_content(file)
        logging.info(f"[RAG] Extracted {len(text)} characters from {file.filename}")

        # Split into chunks with error handling
        try:
            chunks = self.text_splitter.split_text(text)
        except Exception as e:
            log_error(e, f"Failed to split text from {file.filename}")
            chunks = []

        if not chunks:
            logger.error(f"No chunks created from {file.filename}")
            return {
                "document_id": None,
                "filename": file.filename,
                "chunks_processed": 0,
                "total_chunks": 0,
                "status": "failed",
                "error": "No chunks created from document",
            }

        # Store chunks with embeddings in a single batch operation
        # Use a more consistent ID generation method than hash()
        content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:10]
        document_id = f"{user_id}_{file.filename}_{content_hash}"

        async def index_document():
            """Helper function to index document chunks using safe execution"""
            return index_document_chunks(
                db_manager=db_manager,
                user_id=user_id,
                doc_id=document_id,
                name=file.filename,
                chunks=chunks)
        
        # Index chunks with error handling
        try:
            success = await index_document()
        except Exception as e:
            log_error(e, f"Failed to index chunks for {file.filename}")
            success = False

        success_count = len(chunks) if success else 0

        # If this appears to be a resume/CV, also save it to memory system
        if success and self._is_resume_document(file.filename, text):
            await self._save_resume_to_memory(user_id, text, file.filename)

        if success:
            logger.info(f"Processed {file.filename}: {success_count}/{len(chunks)} chunks stored")
        else:
            logger.error(f"Processed {file.filename}: {success_count}/{len(chunks)} chunks stored")

        return {
            "document_id": document_id,
            "filename": file.filename,
            "chunks_processed": success_count,
            "total_chunks": len(chunks),
            "status": "success" if success else "failed",
        }

    @handle_api_errors(
        operation_name="semantic_search")
    async def semantic_search(self, query: str, user_id: str, limit: int = DEFAULT_SEARCH_LIMIT, memory_service=None) -> List[Dict[str, Any]]:
        """
        Perform semantic search across user's documents.
        
        Args:
            query (str): The search query text
            user_id (str): The ID of the user whose documents to search
            limit (int, optional): Maximum number of results to return. Defaults to 5.
            memory_service: Optional new memory service instance
            
        Returns:
            List[Dict[str, Any]]: A list of document chunks matching the query
            
        Raises:
            HTTPException: If semantic search operation fails
        """
        # Input validation
        if not query or not query.strip():
            logging.warning("[RAG] Empty query received in semantic_search")
            return []
            
        if not user_id:
            logging.warning("[RAG] Empty user_id received in semantic_search")
            return []
            
        # Normalize limit
        limit = max(1, min(limit, MAX_SEARCH_LIMIT))  # Keep limit between 1 and MAX_SEARCH_LIMIT
            
        logging.info(f"[RAG] semantic_search called with query='{query}', user_id='{user_id}', limit={limit}")
        
        # Try unified memory service (with built-in fallback handling)
        if memory_service:
            logger.info("Using unified memory service for semantic search")
            try:
                memories = await memory_service.get_relevant_memories(
                    user_id=user_id,
                    context=query,
                    max_memories=limit
                )
                
                # Convert to RAG format
                results = []
                for memory in memories:
                    results.append({
                        "document": memory.content,
                        "metadata": memory.metadata or {},
                        "distance": 1.0 - (memory.relevance_score or 0.0)  # Convert relevance to distance
                    })
                
                logger.info(f"Found {len(results)} relevant documents using unified memory service")
                return results
                
            except Exception as e:
                logger.error(f"Unified memory service failed: {e}")
                return []
        else:
            logger.warning("Memory service not available for semantic search")
            return []

    def _is_resume_document(self, filename: str, content: str) -> bool:
        """
        Detect if the document appears to be a resume/CV.
        
        Args:
            filename (str): The filename
            content (str): The document content
            
        Returns:
            bool: True if this appears to be a resume
        """
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        # Check filename for resume indicators
        resume_filename_keywords = ['resume', 'cv', 'curriculum']
        if any(keyword in filename_lower for keyword in resume_filename_keywords):
            return True
        
        # Check content for resume indicators
        resume_content_keywords = [
            'experience', 'education', 'skills', 'work history',
            'employment', 'career', 'qualifications', 'achievements',
            'professional summary', 'objective', 'contact information'
        ]
        
        keyword_count = sum(1 for keyword in resume_content_keywords if keyword in content_lower)
        
        # If we find multiple resume keywords, it's likely a resume
        return keyword_count >= 3

    @handle_service_errors(
        operation_name="save_resume_to_memory",
        config=ErrorHandlerConfig(
            max_retries=1,
            log_traceback=True)
    )
    async def _save_resume_to_memory(self, user_id: str, content: str, filename: str):
        """
        Save resume content to the memory system.
        
        Args:
            user_id (str): The user ID
            content (str): The resume content
            filename (str): The filename
        """
        # Import adaptive learning system
        from adaptive_learning import adaptive_learning_system
        
        # Extract key sections from resume
        resume_summary = self._extract_resume_summary(content)
        
        # Save to memory with metadata
        metadata = {
            "type": "resume",
            "filename": filename,
            "processed_at": "auto_extracted"
        }
        
        logger.info(f"Saving resume {filename} to memory for user {user_id}")
        
        document_id = await adaptive_learning_system.add_document_to_memory(
            user_id=user_id,
            document_content=resume_summary,
            metadata=metadata
        )
        
        logger.info(f"Resume {filename} saved to memory with ID: {document_id}")

    def _extract_resume_summary(self, content: str) -> str:
        """
        Extract key information from resume content for memory storage.
        
        Args:
            content (str): The full resume content
            
        Returns:
            str: Summarized key information from the resume
        """
        lines = content.split('\n')
        summary_parts = []
        
        # Try to extract name (usually in first few lines)
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            if line and len(line) < 50 and not any(char.isdigit() for char in line[:10]):
                # Likely a name if it's short, near the top, and doesn't start with numbers
                if not any(keyword in line.lower() for keyword in ['email', '@', 'phone', 'address', 'linkedin']):
                    summary_parts.append(f"Name: {line}")
                    break
        
        # Extract contact information
        for line in lines[:20]:  # Check first 20 lines for contact info
            line = line.strip()
            if '@' in line and '.' in line:  # Email
                summary_parts.append(f"Email: {line}")
            elif 'phone' in line.lower() or (any(char.isdigit() for char in line) and len([c for c in line if c.isdigit()]) >= 7):
                summary_parts.append(f"Phone: {line}")
        
        # Extract sections
        current_section = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line is a section header
            if self._is_section_header(line):
                current_section = line.lower()
            elif current_section:
                # Add content from important sections
                if any(section in current_section for section in ['experience', 'work', 'employment', 'education', 'skills']):
                    if len(line) > 10 and len(summary_parts) < 20:  # Limit summary length
                        summary_parts.append(f"{current_section.title()}: {line}")
        
        return "\n".join(summary_parts[:15])  # Limit to first 15 key points

    def _is_section_header(self, line: str) -> bool:
        """Check if a line appears to be a section header."""
        line_lower = line.lower()
        headers = [
            'experience', 'work experience', 'employment', 'career',
            'education', 'academic background', 'qualifications',
            'skills', 'technical skills', 'core competencies',
            'achievements', 'accomplishments', 'awards',
            'contact', 'contact information', 'personal details'
        ]
        
        return any(header in line_lower for header in headers) and len(line) < 50


# Global RAG processor instance
rag_processor = RAGProcessor()
