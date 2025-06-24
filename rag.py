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
                    "total_chunks": 0,                    "status": "failed",
                    "error": "No chunks created from document",
                }

            # Store chunks with embeddings in a single batch operation
            document_id = f"{user_id}_{file.filename}_{hash(text)}"

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
            log_service_status("RAG", "error", f"Document processing error: {str(e)}")
            MemoryErrorHandler.handle_memory_error(e, "document_processing", user_id)
            raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

    async def semantic_search(
        self, query: str, user_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Perform semantic search across user's documents."""
        
        # CRITICAL DEBUG: Add this at the very start
        import sys
        sys.stderr.write(f"🚨🚨🚨 [RAG] semantic_search CALLED with query='{query}', user_id='{user_id}'\n")
        sys.stderr.flush()
        
        import logging
        
        # Force log to file as well as stdout
        with open('/tmp/rag_debug.log', 'a') as f:
            f.write(f"🔍 [RAG] semantic_search called with query='{query}', user_id='{user_id}', limit={limit}\n")
            f.flush()
        
        logging.critical(f"🔍 [RAG] semantic_search called with query='{query}', user_id='{user_id}', limit={limit}")
        try:
            with open('/tmp/rag_debug.log', 'a') as f:
                f.write(f"🔍 [RAG] About to call get_embedding...\n")
                f.flush()
            
            logging.critical(f"🔍 [RAG] About to call get_embedding...")
            # Get query embedding
            query_embedding = get_embedding(db_manager, query)
            
            with open('/tmp/rag_debug.log', 'a') as f:
                f.write(f"🔍 [RAG] get_embedding returned: {type(query_embedding)}\n")
                f.flush()
            
            logging.critical(f"🔍 [RAG] get_embedding returned: {type(query_embedding)}")
            
            # Check if embedding is valid - avoid NumPy array truth value errors
            embedding_valid = True
            if query_embedding is None:
                embedding_valid = False
            elif hasattr(query_embedding, 'size'):
                # For NumPy arrays, check size safely
                try:
                    embedding_valid = query_embedding.size > 0
                except ValueError:
                    # Handle NumPy array truth value error
                    embedding_valid = False
            elif hasattr(query_embedding, '__len__'):
                embedding_valid = len(query_embedding) > 0
            else:
                embedding_valid = False
                
            if not embedding_valid:
                log_service_status("RAG", "warning", "Could not generate embedding for search query")
                with open('/tmp/rag_debug.log', 'a') as f:
                    f.write(f"❌ [RAG] Embedding is None or empty\n")
                    f.flush()
                logging.critical(f"❌ [RAG] Embedding is None or empty")
                return []

            with open('/tmp/rag_debug.log', 'a') as f:
                f.write(f"🔍 [RAG] About to call retrieve_user_memory...\n")
                f.flush()
            
            logging.critical(f"🔍 [RAG] About to call retrieve_user_memory...")
            # Retrieve similar documents
            results = retrieve_user_memory(db_manager, user_id, query_embedding, limit)
            
            with open('/tmp/rag_debug.log', 'a') as f:
                f.write(f"🔍 [RAG] retrieve_user_memory returned: {len(results)} results\n")
                f.flush()
            
            logging.critical(f"🔍 [RAG] retrieve_user_memory returned: {len(results)} results")

            log_service_status(
                "RAG", "ready", f"Found {len(results)} relevant documents for query: {query[:50]}..."
            )

            return results

        except Exception as e:
            import traceback
            error_msg = f"❌ [RAG] Exception caught in semantic_search: {type(e).__name__}: {e}"
            traceback_str = traceback.format_exc()
            
            with open('/tmp/rag_debug.log', 'a') as f:
                f.write(f"{error_msg}\n")
                f.write(f"❌ [RAG] Full traceback:\n{traceback_str}\n")
                f.flush()
            
            logging.critical(error_msg)
            logging.critical(f"❌ [RAG] Full traceback:\n{traceback_str}")
            log_service_status("RAG", "error", f"{error_msg}\nTraceback: {traceback_str}")
            MemoryErrorHandler.handle_memory_error(e, "semantic_search", user_id)
            return []


# Global RAG processor instance
rag_processor = RAGProcessor()
