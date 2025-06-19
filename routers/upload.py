"""
File upload and processing endpoints for the FastAPI LLM backend.
Handles document uploads, processing, and integration with RAG system.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
from rag import rag_processor
from human_logging import log_api_request, log_service_status
from error_handler import log_error
from error_handler import get_user_friendly_message

# Create router for upload endpoints
upload_router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_MIME_TYPES = [
    "text/plain",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/markdown",
    "text/x-python",
    "application/json",
]

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def is_file_type_allowed(file: UploadFile) -> bool:
    """Validate file content type and extension."""
    return file.content_type in ALLOWED_MIME_TYPES

@upload_router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    description: Optional[str] = Form(None)
):
    """Upload and process a document for RAG integration."""
    request_id = os.urandom(8).hex() # Generate a unique request ID
    log_api_request("POST", "/upload/document", 202, 0) # Log accepted request

    try:
        # Validate file size
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Validate file type
        if not is_file_type_allowed(file):
            raise HTTPException(
                status_code=415,
                detail=f"File type ''{file.content_type}'' not supported."
            )
        
        # Process document with RAG system
        result = await rag_processor.process_document(file, user_id)
        
        log_service_status(
            "API", "ready", 
            f"Document uploaded: {file.filename} ({result.get('chunks_processed', 0)} chunks)"
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Document uploaded and processed successfully",
                "data": result
            }
        )
        
    except HTTPException as http_exc:
        log_error(http_exc, "upload_document", request_id)
        raise
    except Exception as e:
        log_error(e, "upload_document", request_id)
        raise HTTPException(
            status_code=500,
            detail=get_user_friendly_message(e, "upload")
        )

@upload_router.get("/formats")
async def get_supported_formats():
    """Get list of supported file formats for upload."""
    return {
        "supported_mime_types": ALLOWED_MIME_TYPES,
        "max_file_size_mb": MAX_FILE_SIZE // (1024*1024),
        "description": "Supported file formats for document upload and processing"
    }

@upload_router.post("/search")
async def search_documents(
    query: str = Form(...),
    user_id: str = Form(...),
    limit: int = Form(5, ge=1, le=50) # Add validation for limit
):
    """Search through uploaded documents using semantic search."""
    request_id = os.urandom(8).hex()
    log_api_request("POST", "/upload/search", 202, 0)

    try:
        results = await rag_processor.semantic_search(query, user_id, limit)
        
        log_service_status(
            "API", "ready", 
            f"Document search: ''{query}'' returned {len(results)} results"
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
        log_error(e, "search_documents", request_id)
        raise HTTPException(
            status_code=500,
            detail=get_user_friendly_message(e, "search")
        )