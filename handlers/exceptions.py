"""
Global exception handlers for the FastAPI application.
"""

import uuid
import traceback
from datetime import datetime
from typing import Callable, Optional
import os

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from human_logging import log_service_status


class CustomHTTPException(Exception):
    """Custom HTTP exception with additional context."""

    def __init__(self, status_code: int, detail: str, error_code: Optional[str] = None):
        """TODO: Add proper docstring for __init__."""
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code or "custom_error"


def create_exception_handlers() -> list[tuple[type, Callable]]:
    """Create and return all exception handlers."""
    return [
        (StarletteHTTPException, http_exception_handler),
        (RequestValidationError, validation_exception_handler),
        (CustomHTTPException, custom_http_exception_handler),
        (ValueError, value_error_handler),
        (KeyError, key_error_handler),
        (TimeoutError, timeout_error_handler),
        (Exception, general_exception_handler),
    ]


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
                "timestamp": datetime.now().isoformat(),
            }
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors with detailed information."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
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
                "timestamp": datetime.now().isoformat(),
            }
        },
    )


async def custom_http_exception_handler(request: Request, exc: CustomHTTPException) -> JSONResponse:
    """Handle custom HTTP exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    log_service_status("CUSTOM_ERROR", "warning", f"Custom error [{request_id}]: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "custom_error",
                "code": exc.status_code,
                "error_code": exc.error_code,
                "message": exc.detail,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
            }
        },
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    log_service_status("VALUE_ERROR", "warning", f"Value error [{request_id}]: {str(exc)}")

    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "type": "value_error",
                "code": 400,
                "message": str(exc),
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
            }
        },
    )


async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
    """Handle KeyError exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    log_service_status("KEY_ERROR", "warning", f"Key error [{request_id}]: {str(exc)}")

    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "type": "key_error",
                "code": 400,
                "message": f"Missing required key: {str(exc)}",
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
            }
        },
    )


async def timeout_error_handler(request: Request, exc: TimeoutError) -> JSONResponse:
    """Handle timeout exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    log_service_status("TIMEOUT_ERROR", "warning", f"Timeout error [{request_id}]: {str(exc)}")

    return JSONResponse(
        status_code=504,
        content={
            "error": {
                "type": "timeout_error",
                "code": 504,
                "message": "Request timed out",
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors with proper logging."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Log full traceback for debugging
    error_details = traceback.format_exc()
    log_service_status("INTERNAL_ERROR", "error", f"Unhandled exception [{request_id}]: {str(exc)}\n{error_details}")

    # Don't expose internal errors in production
    is_production = os.getenv("ENVIRONMENT") == "production"
    error_message = "An internal server error occurred" if is_production else str(exc)

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error",
                "code": 500,
                "message": error_message,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "debug_info": None if is_production else error_details[:500],  # Truncate for safety
            }
        },
    )
