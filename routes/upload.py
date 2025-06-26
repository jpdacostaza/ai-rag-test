"""
Enhanced upload routes supporting both JSON and file upload endpoints.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, File, Form, UploadFile
from pydantic import BaseModel, Field

from database_manager import db_manager, get_embedding
from database import index_user_document, retrieve_user_memory
from human_logging import log_service_status

# Create router for upload endpoints
upload_router = APIRouter(prefix="/upload", tags=["upload"])


# Pydantic models for JSON endpoints
class DocumentUpload(BaseModel):
    """TODO: Add proper docstring for DocumentUpload class."""

    content: str = Field(..., min_length=1, description="Document content")
    user_id: str = Field(..., description="User ID for isolation")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class DocumentSearch(BaseModel):
    """TODO: Add proper docstring for DocumentSearch class."""

    query: str = Field(..., min_length=1, description="Search query")
    user_id: str = Field(..., description="User ID for isolation")
    limit: Optional[int] = Field(default=5, ge=1, le=20, description="Number of results")


# JSON-based document upload endpoint
@upload_router.post("/document")
async def upload_document_json(upload: DocumentUpload) -> Dict[str, Any]:
    """Upload and process a document via JSON payload."""
    try:
        log_service_status("upload", "info", f"Document upload request from user: {upload.user_id}")

        # Create document metadata
        doc_metadata = upload.metadata or {}
        doc_metadata.update(
            {
                "upload_timestamp": datetime.now().isoformat(),
                "content_length": len(upload.content),
                "content_type": "text/plain",
            }
        )

        # Generate document ID
        doc_id = f"doc_{upload.user_id}_{int(datetime.now().timestamp())}"

        # Store the document
        try:
            chunks_stored = index_user_document(
                db_manager=db_manager,
                user_id=upload.user_id,
                doc_id=doc_id,
                name="uploaded_document",
                text=upload.content,
            )

            if not chunks_stored:
                log_service_status("upload", "warning", f"Document indexing returned False for user {upload.user_id}")

        except Exception as index_error:
            log_service_status("upload", "error", f"Failed to index document: {str(index_error)}")
            raise HTTPException(status_code=500, detail=f"Document indexing failed: {str(index_error)}")

        log_service_status(
            "upload", "info", f"Document uploaded successfully: {chunks_stored} chunks for user {upload.user_id}"
        )

        return {
            "status": "success",
            "message": "Document uploaded and processed successfully",
            "document_id": doc_id,
            "chunks_stored": chunks_stored,
            "content_length": len(upload.content),
            "user_id": upload.user_id,
        }

    except Exception as e:
        log_service_status("upload", "error", f"Document upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


# JSON-based document search endpoint
@upload_router.post("/search")
async def search_documents_json(search: DocumentSearch) -> Dict[str, Any]:
    """Search documents via JSON payload."""
    try:
        log_service_status("upload", "info", f"Document search request from user: {search.user_id}")

        # Get embedding for the search query
        try:
            query_embedding = await get_embedding(search.query)
        except Exception as embedding_error:
            log_service_status("upload", "error", f"Failed to generate embedding: {str(embedding_error)}")
            return {
                "status": "error",
                "query": search.query,
                "results": [],
                "count": 0,
                "user_id": search.user_id,
                "message": "Failed to generate embedding for query",
            }

        if not query_embedding:
            log_service_status("upload", "warning", f"Empty embedding generated for query: {search.query}")
            return {
                "status": "success",
                "query": search.query,
                "results": [],
                "count": 0,
                "user_id": search.user_id,
                "message": "Could not generate embedding for query",
            }

        # Retrieve relevant documents using the database manager
        try:
            results = retrieve_user_memory(
                db_manager=db_manager,
                user_id=search.user_id,
                query_embedding=query_embedding,
                n_results=search.limit or 5,
            )
        except Exception as retrieval_error:
            log_service_status("upload", "error", f"Failed to retrieve memories: {str(retrieval_error)}")
            raise HTTPException(status_code=500, detail=f"Memory retrieval failed: {str(retrieval_error)}")

        if not results:
            return {"status": "success", "query": search.query, "results": [], "count": 0, "user_id": search.user_id}

        # Format results for the response
        formatted_results = []
        for result in results:
            formatted_result = {
                "content": result.get("document", ""),
                "metadata": result.get("metadata", {}),
                "relevance_score": 1.0 - result.get("distance", 1.0) if "distance" in result else 0.5,
            }
            formatted_results.append(formatted_result)

        log_service_status(
            "upload", "info", f"Search completed: {len(formatted_results)} results for user {search.user_id}"
        )

        return {
            "status": "success",
            "query": search.query,
            "results": formatted_results,
            "count": len(formatted_results),
            "user_id": search.user_id,
        }

    except Exception as e:
        log_service_status("upload", "error", f"Document search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search documents: {str(e)}")


# File upload endpoint (keeping the existing functionality for file uploads)
@upload_router.post("/file")
async def upload_file(file: UploadFile = File(...), user_id: str = Form(...), description: Optional[str] = Form(None)):
    """Upload and process a file."""
    try:
        # Read file content
        content = await file.read()

        # Convert to text based on file type
        if file.content_type == "text/plain":
            text_content = content.decode("utf-8")
        elif file.content_type == "application/json":
            text_content = content.decode("utf-8")
        else:
            # For other file types, you might want to use specialized libraries
            text_content = content.decode("utf-8", errors="ignore")

        # Create upload object and reuse the JSON endpoint logic
        upload_data = DocumentUpload(
            content=text_content,
            user_id=user_id,
            metadata={
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": len(content),
                "description": description or "",
            },
        )

        return await upload_document_json(upload_data)

    except Exception as e:
        log_service_status("upload", "error", f"File upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


# Health check for upload service
@upload_router.get("/health")
async def upload_health() -> Dict[str, Any]:
    """Check upload service health."""
    try:
        # Simple health check
        return {
            "status": "healthy",
            "service": "upload",
            "database_connected": db_manager is not None,
            "endpoints": [
                "POST /upload/document (JSON)",
                "POST /upload/search (JSON)",
                "POST /upload/file (multipart)",
                "GET /upload/health",
            ],
        }
    except Exception as e:
        return {"status": "unhealthy", "service": "upload", "error": str(e)}


# Get supported formats
@upload_router.get("/formats")
async def get_supported_formats() -> Dict[str, Any]:
    """Get supported formats and limits."""
    return {
        "json_endpoints": {
            "POST /upload/document": "Direct JSON content upload",
            "POST /upload/search": "JSON-based document search",
        },
        "file_endpoints": {"POST /upload/file": "Multipart file upload"},
        "supported_content_types": ["text/plain", "application/json", "text/markdown"],
        "limits": {"max_content_length": 1000000, "max_search_results": 20},  # 1MB for JSON content
    }
