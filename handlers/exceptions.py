"""
Global exception handlers for the FastAPI application.
"""
import uuid
from datetime import datetime
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from human_logging import log_service_status

def create_exception_handlers() -> list[tuple[type, Callable]]:
    """Create and return all exception handlers."""
    
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle HTTP exceptions with structured responses."""
        log_service_status("HTTP_ERROR", "warning", f"HTTP {exc.status_code}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "code": exc.status_code,
                    "message": exc.detail,
                    "timestamp": datetime.now().isoformat()
                }
            }
        )

    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle request validation errors with detailed information."""
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        log_service_status("VALIDATION_ERROR", "warning", f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "validation_error",
                    "code": 422,
                    "message": "Request validation failed",
                    "details": exc.errors(),
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
        )

    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected errors with proper logging."""
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        log_service_status("INTERNAL_ERROR", "error", f"Unhandled exception [{request_id}]: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_error",
                    "code": 500,
                    "message": "An internal server error occurred",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
        )

    return [
        (StarletteHTTPException, http_exception_handler),
        (RequestValidationError, validation_exception_handler),
        (Exception, general_exception_handler),
    ]
