"""
RAG (Retrieval-Augmented Generation) implementation for document processing and semantic search.
Handles document ingestion, chunking, embedding, and retrieval for enhanced LLM responses.
"""

from typing import Any
from typing import Dict
from typing import List

from fastapi import HTTPException
from fastapi import UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter

from database import db_manager
from database import get_embedding
from database import index_document_chunks
from database import retrieve_user_memory
from error_handler import MemoryErrorHandler
from human_logging import log_service_status


class RAGProcessor:
    """Handles document processing and semantic search for RAG implementation."""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    async def process_document(self, file: UploadFile, user_id: str) -> Dict[str, Any]:
        """Process uploaded document and store in vector database."""
        try:
            # Read file content
            content = await file.read()
            text = content.decode("utf-8")

            # Split into chunks
            chunks = self.text_splitter.split_text(text)

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
            document_id = "{user_id}_{file.filename}_{hash(text)}"

            success = index_document_chunks(
                db_manager=db_manager,
                user_id=user_id,
                doc_id=document_id,
                name=file.filename,
                chunks=chunks,
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
            log_service_status("RAG", "error", "Document processing error: {str(e)}")
            MemoryErrorHandler.handle_memory_error(e, "document_processing", user_id)
            raise HTTPException(status_code=500, detail="Document processing failed: {str(e)}")

    async def semantic_search(
        self, query: str, user_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Perform semantic search across user's documents."""
        try:
            # Get query embedding
            query_embedding = get_embedding(db_manager, query)
            if not query_embedding:
                return []

            # Retrieve similar documents
            results = retrieve_user_memory(db_manager, user_id, query_embedding, limit)

            log_service_status(
                "RAG", "ready", "Found {len(results)} relevant documents for query: {query[:50]}..."
            )

            return results

        except Exception as e:
            MemoryErrorHandler.handle_memory_error(e, "semantic_search", user_id)
            return []


# Global RAG processor instance
rag_processor = RAGProcessor()
