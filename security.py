"""
Security middleware and configuration for the FastAPI application.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from typing import Dict, Any
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""

    def __init__(self, app, calls: int = 100, period: int = 60):
        """TODO: Add proper docstring for __init__."""
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, Dict[str, Any]] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        if client_ip not in self.clients:
            self.clients[client_ip] = {"calls": 0, "reset_time": current_time + self.period}

        client_data = self.clients[client_ip]

        if current_time > client_data["reset_time"]:
            client_data["calls"] = 0
            client_data["reset_time"] = current_time + self.period

        if client_data["calls"] >= self.calls:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "Rate limit exceeded", "retry_after": int(client_data["reset_time"] - current_time)},
            )

        client_data["calls"] += 1
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(self.calls - client_data["calls"])
        response.headers["X-RateLimit-Reset"] = str(int(client_data["reset_time"]))

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log requests for monitoring and debugging."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")

        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} - {process_time:.4f}s")

        response.headers["X-Process-Time"] = str(process_time)

        return response


def configure_security(app: FastAPI):
    """Configure security middleware for the FastAPI app."""

    # CORS configuration
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Trusted hosts (only in production)
    if os.getenv("ENVIRONMENT") == "production":
        trusted_hosts = os.getenv("TRUSTED_HOSTS", "localhost").split(",")
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Rate limiting (configurable)
    rate_limit_calls = int(os.getenv("RATE_LIMIT_CALLS", "100"))
    rate_limit_period = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    app.add_middleware(RateLimitMiddleware, calls=rate_limit_calls, period=rate_limit_period)

    # Request logging
    if os.getenv("LOG_REQUESTS", "true").lower() == "true":
        app.add_middleware(RequestLoggingMiddleware)

    logger.info("Security middleware configured successfully")


def validate_environment():
    """Validate required environment variables with fallback to config defaults."""
    from config import REDIS_HOST, CHROMA_HOST, DEFAULT_MODEL

    # Check if essential services are configured (either via env vars or config defaults)
    configurations = {"REDIS_HOST": REDIS_HOST, "CHROMA_HOST": CHROMA_HOST, "DEFAULT_MODEL": DEFAULT_MODEL}

    missing_configs = []
    for config_name, config_value in configurations.items():
        if not config_value:
            missing_configs.append(config_name)

    if missing_configs:
        raise ValueError(f"Missing required configurations: {', '.join(missing_configs)}")

    logger.info("Environment validation passed")
    logger.info(f"Using Redis: {REDIS_HOST}")
    logger.info(f"Using ChromaDB: {CHROMA_HOST}")
    logger.info(f"Using Model: {DEFAULT_MODEL}")
