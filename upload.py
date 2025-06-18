"""
File upload and processing endpoints for the FastAPI LLM backend.
Handles document uploads, processing, and integration with RAG system.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
from rag import rag_processor
from human_logging import HumanLogger
from error_handler import ErrorHandler

# Create router for upload endpoints
upload_router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_FILE_TYPES = {
    "text/plain": [".txt", ".md", ".py", ".js", ".html", ".css", ".json"],
    "application/pdf": [".pdf"],
    "application/msword": [".doc"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"]
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@upload_router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    description: Optional[str] = Form(None)
):
    """Upload and process a document for RAG integration."""
    try:
        # Validate file size
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Validate file type
        if file.content_type not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"File type {file.content_type} not supported. Allowed types: {list(ALLOWED_FILE_TYPES.keys())}"
            )
        
        # Process document with RAG system
        result = await rag_processor.process_document(file, user_id)        
        HumanLogger.log_service_status(
            "API", "ready", 
            f"Document uploaded: {file.filename} ({result['chunks_processed']} chunks)"
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Document uploaded and processed successfully",
                "data": result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        ErrorHandler.log_error(e, "upload_document", user_id)
        raise HTTPException(
            status_code=500,
            detail=ErrorHandler.get_user_friendly_message(e, "upload")
        )

@upload_router.get("/formats")
async def get_supported_formats():
    """Get list of supported file formats for upload."""
    return {
        "supported_types": ALLOWED_FILE_TYPES,
        "max_file_size_mb": MAX_FILE_SIZE // (1024*1024),
        "description": "Supported file formats for document upload and processing"
    }

@upload_router.post("/search")
async def search_documents(
    query: str = Form(...),
    user_id: str = Form(...),
    limit: int = Form(5)
):
    """Search through uploaded documents using semantic search."""
    try:
        if limit > 20:
            limit = 20  # Prevent excessive results
            
        results = await rag_processor.semantic_search(query, user_id, limit)        
        HumanLogger.log_service_status(
            "API", "ready", 
            f"Document search: '{query}' returned {len(results)} results"
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "query": query,
                "results_count": len(results),
                "results": results
            }
        )
        
    except Exception as e:
        ErrorHandler.log_error(e, "search_documents", user_id)
        raise HTTPException(
            status_code=500,
            detail=ErrorHandler.get_user_friendly_message(e, "search")
        )