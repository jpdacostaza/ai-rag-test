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
from core.error_response import build_error
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.unified_logging import log_service_status


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
    return build_error(
        code="http_error",
        message=exc.detail,
        status=exc.status_code,
        details={"timestamp": datetime.now().isoformat()},
        retryable=False,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors with detailed information."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    log_service_status("VALIDATION_ERROR", "warning", f"Validation error: {exc.errors()}")
    return build_error(
        code="validation_error",
        message="Request validation failed",
        status=422,
        details={"errors": exc.errors(), "request_id": request_id, "timestamp": datetime.now().isoformat()},
        retryable=False,
    )


async def custom_http_exception_handler(request: Request, exc: CustomHTTPException) -> JSONResponse:
    """Handle custom HTTP exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    log_service_status("CUSTOM_ERROR", "warning", f"Custom error [{request_id}]: {exc.detail}")

    return build_error(
        code=exc.error_code or "custom_error",
        message=exc.detail,
        status=exc.status_code,
        details={"request_id": request_id, "timestamp": datetime.now().isoformat()},
        retryable=False,
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    log_service_status("VALUE_ERROR", "warning", f"Value error [{request_id}]: {str(exc)}")

    return build_error(
        code="value_error",
        message=str(exc),
        status=400,
        details={"request_id": request_id, "timestamp": datetime.now().isoformat()},
        retryable=False,
    )


async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
    """Handle KeyError exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    log_service_status("KEY_ERROR", "warning", f"Key error [{request_id}]: {str(exc)}")

    return build_error(
        code="key_error",
        message=f"Missing required key: {str(exc)}",
        status=400,
        details={"request_id": request_id, "timestamp": datetime.now().isoformat()},
        retryable=False,
    )


async def timeout_error_handler(request: Request, exc: TimeoutError) -> JSONResponse:
    """Handle timeout exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    log_service_status("TIMEOUT_ERROR", "warning", f"Timeout error [{request_id}]: {str(exc)}")

    return build_error(
        code="timeout_error",
        message="Request timed out",
        status=504,
        details={"request_id": request_id, "timestamp": datetime.now().isoformat()},
        retryable=True,
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

    return build_error(
        code="internal_error",
        message=error_message,
        status=500,
        details={
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "debug_info": None if is_production else error_details[:500],
        },
        retryable=False,
    )
