"""
File upload and processing endpoints for the FastAPI LLM backend.
Handles document uploads, processing, and integration with RAG system.
"""

import os
from typing import Optional, Dict, Any

from fastapi import APIRouter
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from error_handler import get_user_friendly_message
from error_handler import log_error
from human_logging import log_api_request
from human_logging import log_service_status
from rag import rag_processor

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
    file: UploadFile = File(...), user_id: str = Form(...), description: Optional[str] = Form(None)
):
    """Upload and process a document for RAG integration."""
    request_id = os.urandom(8).hex()  # Generate a unique request ID
    log_api_request("POST", "/upload/document", 202, 0)  # Log accepted request

    try:
        # Validate file size
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB",
            )

        # Validate file type
        if not is_file_type_allowed(file):
            raise HTTPException(status_code=415, detail=f"File type '{file.content_type}' not supported.")

        # Process document with RAG system
        result = await rag_processor.process_document(file, user_id)

        log_service_status(
            "API",
            "ready",
            f"Document uploaded: {file.filename} ({result.get('chunks_processed', 0)} chunks)",
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Document uploaded and processed successfully",
                "data": result,
            },
        )

    except HTTPException as http_exc:
        log_error(http_exc, "upload_document", request_id)
        raise
    except Exception as e:
        log_service_status("UPLOAD", "error", f"Error in upload_document: {e}")
        log_error(e, "upload_document", request_id)
        raise HTTPException(status_code=500, detail=get_user_friendly_message(e, "upload"))


@upload_router.get("/formats")
async def get_supported_formats():
    """Get list of supported file formats for upload."""
    return {
        "supported_mime_types": ALLOWED_MIME_TYPES,
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "description": "Supported file formats for document upload and processing",
    }


@upload_router.post("/search")
async def search_documents(
    query: str = Form(...),
    user_id: str = Form(...),
    limit: int = Form(5, ge=1, le=50),  # Add validation for limit
):
    """Search through uploaded documents using semantic search."""

    # CRITICAL DEBUG: Add at the very start
    import sys

    sys.stderr.write(f"🚨🚨🚨 [UPLOAD] search_documents ENDPOINT CALLED with query='{query}'\n")
    sys.stderr.flush()

    request_id = os.urandom(8).hex()
    log_api_request("POST", "/upload/search", 202, 0)

    # Add debug logging at the upload endpoint level
    import logging

    with open("/tmp/upload_debug.log", "a") as f:
        f.write(f"🔍 [UPLOAD] search_documents called with query='{query}', user_id='{user_id}', limit={limit}\n")
        f.write(f"🔍 [UPLOAD] rag_processor type: {type(rag_processor)}\n")
        f.write(f"🔍 [UPLOAD] About to call rag_processor.semantic_search...\n")
        f.flush()

    logging.critical(f"🔍 [UPLOAD] search_documents called with query='{query}', user_id='{user_id}', limit={limit}")
    logging.critical(f"🔍 [UPLOAD] rag_processor type: {type(rag_processor)}")

    try:
        with open("/tmp/upload_debug.log", "a") as f:
            f.write(f"🔍 [UPLOAD] Calling semantic_search...\n")
            f.flush()

        results = await rag_processor.semantic_search(query, user_id, limit)

        with open("/tmp/upload_debug.log", "a") as f:
            f.write(f"🔍 [UPLOAD] semantic_search returned {len(results)} results\n")
            f.flush()

        log_service_status("API", "ready", f"Document search: '{query}' returned {len(results)} results")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "query": query,
                "results_count": len(results),
                "results": results,
                "debug_message": "THIS IS FROM MY MODIFIED UPLOAD.PY",
            },
        )

    except Exception as e:
        log_service_status("UPLOAD", "error", f"Error in search_documents: {e}")
        with open("/tmp/upload_debug.log", "a") as f:
            f.write(f"❌ [UPLOAD] Exception in search_documents: {type(e).__name__}: {e}\n")
            f.flush()

        log_error(e, "search_documents", request_id)
        raise HTTPException(status_code=500, detail=get_user_friendly_message(e, "search"))


# JSON-based endpoints for testing compatibility


class DocumentUploadJSON(BaseModel):
    """TODO: Add proper docstring for DocumentUploadJSON class."""

    content: str = Field(..., min_length=1, description="Document content")
    user_id: str = Field(..., description="User ID for isolation")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class DocumentSearchJSON(BaseModel):
    """TODO: Add proper docstring for DocumentSearchJSON class."""

    query: str = Field(..., min_length=1, description="Search query")
    user_id: str = Field(..., description="User ID for isolation")
    limit: Optional[int] = Field(default=5, ge=1, le=20, description="Number of results")


@upload_router.post("/document_json")
async def upload_document_json(upload: DocumentUploadJSON):
    """Upload document via JSON payload for testing."""
    try:
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
            description=(upload.metadata or {}).get("description", "JSON uploaded document"),
        )

        return result

    except Exception as e:
        log_service_status("UPLOAD", "error", f"Error in upload_document_json: {e}")
        raise HTTPException(status_code=500, detail=get_user_friendly_message(e, "upload"))


@upload_router.post("/search_json")
async def search_documents_json(search: DocumentSearchJSON):
    """Search documents via JSON payload for testing."""
    try:
        # Call the existing search function
        result = await search_documents(query=search.query, user_id=search.user_id, limit=search.limit or 5)

        return result

    except Exception as e:
        log_service_status("UPLOAD", "error", f"Error in search_documents_json: {e}")
        raise HTTPException(status_code=500, detail=get_user_friendly_message(e, "search"))
