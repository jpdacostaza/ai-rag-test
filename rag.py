"""
RAG (Retrieval-Augmented Generation) implementation for document processing and semantic search.
Handles document ingestion, chunking, embedding, and retrieval for enhanced LLM responses.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
from database import db_manager, index_user_document, retrieve_user_memory, get_embedding
from human_logging import HumanLogger
from error_handler import MemoryErrorHandler, safe_execute

class RAGProcessor:
    """Handles document processing and semantic search for RAG implementation."""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
    async def process_document(self, file: UploadFile, user_id: str) -> Dict[str, Any]:
        """Process uploaded document and store in vector database."""
        try:
            # Read file content
            content = await file.read()
            text = content.decode('utf-8')
            
            # Split into chunks
            chunks = self.text_splitter.split_text(text)
            
            if not chunks:
                HumanLogger.log_service_status("RAG", "error", f"No chunks created from {file.filename}")
                return {
                    "document_id": None,
                    "filename": file.filename,
                    "chunks_processed": 0,
                    "total_chunks": 0,
                    "status": "failed",
                    "error": "No chunks created from document"
                }
            
            # Store chunks with embeddings
            document_id = f"{user_id}_{file.filename}_{hash(text)}"
            
            success_count = 0
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                try:
                    success = index_user_document(
                        db_manager=db_manager,
                        user_id=user_id,
                        doc_id=chunk_id,
                        name=file.filename,
                        text=chunk
                    )
                    if success:
                        success_count += 1
                    else:
                        HumanLogger.log_service_status("RAG", "error", f"Failed to index chunk {i} for {file.filename}")
                except Exception as e:
                    HumanLogger.log_service_status("RAG", "error", f"Exception indexing chunk {i}: {str(e)}")
            
            HumanLogger.log_service_status(
                "RAG", "ready", 
                f"Processed {file.filename}: {success_count}/{len(chunks)} chunks stored"
            )
            
            return {
                "document_id": document_id,
                "filename": file.filename,
                "chunks_processed": success_count,
                "total_chunks": len(chunks),
                "status": "success" if success_count == len(chunks) else "partial" if success_count > 0 else "failed"
            }
            
        except Exception as e:
            HumanLogger.log_service_status("RAG", "error", f"Document processing error: {str(e)}")
            MemoryErrorHandler.handle_memory_error(e, "document_processing", user_id)
            raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")
    
    async def semantic_search(self, query: str, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search across user's documents."""
        try:
            # Get query embedding
            query_embedding = get_embedding(db_manager, query)
            if not query_embedding:
                return []
            
            # Retrieve similar documents
            results = retrieve_user_memory(db_manager, user_id, query_embedding, limit)
            
            HumanLogger.log_service_status(
                "RAG", "ready", 
                f"Found {len(results)} relevant documents for query: {query[:50]}..."
            )
            
            return results
            
        except Exception as e:
            MemoryErrorHandler.handle_memory_error(e, "semantic_search", user_id)
            return []

# Global RAG processor instance
rag_processor = RAGProcessor()
