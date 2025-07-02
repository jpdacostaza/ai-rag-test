"""
RAG (Retrieval-Augmented Generation) implementation for document processing and semantic search.
Handles document ingestion, chunking, embedding, and retrieval for enhanced LLM responses.
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter

from database_manager import db_manager
from database_manager import get_embedding, index_document_chunks, retrieve_user_memory
from error_handler import MemoryErrorHandler, safe_execute, log_error
from human_logging import log_service_status


# RAG configuration constants
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
            separators=["\n\n", "\n", " ", ""],
        )

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
        try:
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
                
            # Check if file type is supported (basic check for text-based files)
            supported_extensions = ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.csv', '.xml', '.log']
            file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
            if file_ext and file_ext not in supported_extensions:
                logging.warning(f"[RAG] Potentially unsupported file type: {file_ext}")
            
            # Helper function for file reading with error handling
            async def read_file_content():
                """Read and decode file content"""
                content = await file.read()
                return content.decode("utf-8")
                
            # Read file content with error handling
            text = await safe_execute(
                read_file_content,
                fallback_value=None,
                error_handler=lambda e: log_error(e, f"Failed to read file {file.filename}")
            )
            
            if text is None:
                log_service_status("RAG", "error", f"Failed to read content from {file.filename}")
                return {
                    "document_id": None,
                    "filename": file.filename,
                    "chunks_processed": 0,
                    "total_chunks": 0,
                    "status": "failed",
                    "error": "Failed to read document content",
                }

            # Split into chunks with error handling
            chunks = await safe_execute(
                lambda: self.text_splitter.split_text(text),
                fallback_value=[],
                error_handler=lambda e: log_error(e, f"Failed to split text from {file.filename}")
            )

            if not chunks:
                log_service_status("RAG", "error", f"No chunks created from {file.filename}")
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
                    chunks=chunks,
                )
            
            # Use safe_execute for the indexing operation
            success = await safe_execute(
                index_document,
                fallback_value=False,
                error_handler=lambda e: log_error(e, f"Failed to index chunks for {file.filename}")
            )

            success_count = len(chunks) if success else 0

            log_service_status(
                "RAG",
                "ready" if success else "error",
                f"Processed {file.filename}: {success_count}/{len(chunks)} chunks stored",
            )

            return {
                "document_id": document_id,
                "filename": file.filename,
                "chunks_processed": success_count,
                "total_chunks": len(chunks),
                "status": "success" if success else "failed",
            }

        except Exception as e:
            error_context = f"Document processing for file {file.filename}"
            log_service_status("RAG", "error", f"Document processing error: {str(e)}")
            MemoryErrorHandler.handle_memory_error(e, "document_processing", user_id)
            log_error(e, error_context, user_id=user_id)
            
            # Return user-friendly error message
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Document processing failed",
                    "reason": str(e),
                    "filename": file.filename,
                }
            )

    async def semantic_search(self, query: str, user_id: str, limit: int = DEFAULT_SEARCH_LIMIT) -> List[Dict[str, Any]]:
        """
        Perform semantic search across user's documents.
        
        Args:
            query (str): The search query text
            user_id (str): The ID of the user whose documents to search
            limit (int, optional): Maximum number of results to return. Defaults to 5.
            
        Returns:
            List[Dict[str, Any]]: A list of document chunks matching the query
            
        Raises:
            HTTPException: If semantic search operation fails
        """
        try:
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
        
        async def get_query_embedding():
            """Helper function to get query embedding using safe execution"""
            return get_embedding(db_manager, query)
            
        async def retrieve_similar_documents(embedding):
            """Helper function to retrieve similar documents using safe execution"""
            return retrieve_user_memory(db_manager, user_id, embedding, limit)
            
        # Get query embedding with error handling
        query_embedding = await safe_execute(
            get_query_embedding,
            fallback_value=None,
            error_handler=lambda e: log_error(e, f"Failed to get embedding for query: {query[:50]}...")
        )
        
        # Check if embedding is valid - avoid NumPy array truth value errors
        embedding_valid = False
        
        if query_embedding is not None:
            if hasattr(query_embedding, "size"):
                # For NumPy arrays, check size safely
                try:
                    embedding_valid = query_embedding.size > 0
                except ValueError:
                    embedding_valid = False
            elif hasattr(query_embedding, "__len__"):
                embedding_valid = len(query_embedding) > 0
        
        if not embedding_valid:
            log_service_status("RAG", "warning", "Could not generate embedding for search query")
            logging.warning("[RAG] Embedding is None or empty")
            return []
        
        # Retrieve similar documents with error handling
        results = await safe_execute(
            lambda: retrieve_similar_documents(query_embedding),
            fallback_value=[],
            error_handler=lambda e: log_error(e, f"Failed to retrieve documents for user: {user_id}")
        )
        
        # Log success status
        log_service_status(
            "RAG", 
            "ready", 
            f"Found {len(results)} relevant documents for query: {query[:50]}..."
        )
        return results
            
        except Exception as e:
            error_context = f"Semantic search for query '{query[:30]}...'"
            log_service_status("RAG", "error", f"Semantic search error: {str(e)}")
            log_error(e, error_context, user_id=user_id)
            
            # Return empty results instead of raising exception to avoid breaking the chat flow
            logging.error(f"[RAG] Semantic search failed: {str(e)}")
            return []


# Global RAG processor instance
rag_processor = RAGProcessor()
