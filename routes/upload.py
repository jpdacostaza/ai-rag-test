"""
File upload and processing endpoints for the FastAPI LLM backend.
Handles document uploads, processing, and integration with RAG system.
"""

import logging
import os
from typing import Optional, Dict, Any

from fastapi import APIRouter
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.error_handler import get_user_friendly_message
from core.error_handler import log_error
from utilities.simple_error_handling import handle_api_errors, handle_errors
from core.logging_config import log_api_request, log_service_status
from utilities.rag import rag_processor
from services.dependencies import get_memory_service


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
@handle_api_errors("upload_document")
async def upload_document(
    file: UploadFile = File(...), user_id: str = Form(...), description: Optional[str] = Form(None)
):
    """Upload and process a document for RAG integration."""
    request_id = os.urandom(8).hex()  # Generate a unique request ID
    log_api_request("POST", "/upload/document", 202, 0)  # Log accepted request

    # Validate file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")

    # Validate file type
    if not is_file_type_allowed(file):
        raise HTTPException(status_code=415, detail=f"File type '{file.content_type}' not supported.")

    # Process document with RAG system
    result = await rag_processor.process_document(file, user_id)

    log_service_status(
        "API",
        "ready",
        f"Document uploaded: {file.filename} ({result.get('chunks_processed', 0)} chunks)")

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": "Document uploaded and processed successfully",
            "data": result,
        })


@upload_router.get("/formats")
async def get_supported_formats():
    """Get list of supported file formats for upload."""
    return {
        "supported_mime_types": ALLOWED_MIME_TYPES,
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "description": "Supported file formats for document upload and processing",
    }


@upload_router.post("/search")
@handle_api_errors("search_documents")
async def search_documents(
    query: str = Form(...),
    user_id: str = Form(...),
    limit: int = Form(5, ge=1, le=50),  # Add validation for limit
    memory_service=Depends(get_memory_service)
):
    """
    Search through uploaded documents using semantic search.
    
    Args:
        query: The search query text
        user_id: ID of the user whose documents to search
        limit: Maximum number of results to return (between 1 and 50)
        
    Returns:
        JSONResponse with search results
        
    Raises:
        HTTPException: If search fails
    """
    request_id = os.urandom(8).hex()
    log_api_request("POST", "/upload/search", 202, 0)
    
    logging.info(f"[UPLOAD] Search requested with query='{query}', user_id='{user_id}', limit={limit}")

    results = await rag_processor.semantic_search(query, user_id, limit, memory_service)
    
    log_service_status("API", "ready", f"Document search: '{query}' returned {len(results)} results")

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "query": query,
            "results_count": len(results),
            "results": results,
        })


# JSON-based endpoints for testing compatibility


class DocumentUploadJSON(BaseModel):
    """
    Schema for JSON-based document upload.
    
    This class defines the expected JSON structure for document upload requests,
    including content, user identification, and optional metadata.
    """

    content: str = Field(..., min_length=1, description="Document content")
    user_id: str = Field(..., description="User ID for isolation")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class DocumentSearchJSON(BaseModel):
    """
    Schema for JSON-based document search requests.
    
    This class defines the expected JSON structure for document search requests,
    including query text, user identification, and optional result limit.
    """

    query: str = Field(..., min_length=1, description="Search query")
    user_id: str = Field(..., description="User ID for isolation")
    limit: Optional[int] = Field(default=5, ge=1, le=20, description="Number of results")


@upload_router.post("/document_json")
@handle_api_errors("upload_document_json")
async def upload_document_json(upload: DocumentUploadJSON):
    """Upload document via JSON payload for testing."""
    # Create a temporary file from the content
    import tempfile
    import io

    # Create a file-like object from the content
    content_bytes = upload.content.encode("utf-8")
    file_obj = io.BytesIO(content_bytes)

    # Create a mock UploadFile object
    class MockUploadFile:
        """TODO: Add proper docstring for MockUploadFile class."""

        def __init__(self, content: bytes, filename: str):
            """TODO: Add proper docstring for __init__."""
            self.file = io.BytesIO(content)
            self.filename = filename
            self.content_type = "text/plain"
            self.size = len(content)

        async def read(self) -> bytes:
            return self.file.getvalue()

    mock_file = MockUploadFile(content_bytes, "uploaded_document.txt")

    # Call the existing file upload function
    result = await upload_document(
        file=mock_file,  # type: ignore
        user_id=upload.user_id,
        description=(upload.metadata or {}).get("description", "JSON uploaded document"))

    return result


@upload_router.post("/search_json")
@handle_api_errors("search_documents_json")
async def search_documents_json(search: DocumentSearchJSON, memory_service=Depends(get_memory_service)):
    """Search documents via JSON payload for testing."""
    # Call the existing search function
    results = await rag_processor.semantic_search(search.query, search.user_id, search.limit or 5, memory_service)
    
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "query": search.query,
            "results_count": len(results),
            "results": results,
        })
