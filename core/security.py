"""
Enhanced Input Validation and Sanitization
==========================================

This module provides comprehensive input validation and sanitization
to prevent security vulnerabilities like XSS, SQL injection, and other attacks.
"""

import re
import html
import json
import uuid
import os
import time
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logging (guard against duplicate handlers if unified logging already initialized)
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Note: bleach and markupsafe should be added to requirements.txt
try:
    import bleach
    from markupsafe import Markup
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False

class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

class InputSanitizer:
    """Sanitizes user input to prevent security vulnerabilities."""
    
    # Allowed HTML tags for memory content
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'code', 'pre',
        'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
    ]
    
    # Allowed HTML attributes
    ALLOWED_ATTRIBUTES = {
        '*': ['class'],
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'width', 'height']
    }
    
    @classmethod
    def sanitize_html(cls, content: str) -> str:
        """Sanitize HTML content to prevent XSS attacks."""
        if not content:
            return ""
        
        if BLEACH_AVAILABLE:
            # Use bleach to clean HTML if available
            cleaned = bleach.clean(
                content,
                tags=cls.ALLOWED_TAGS,
                attributes=cls.ALLOWED_ATTRIBUTES,
                strip=True
            )
            return cleaned
        else:
            # Fallback to simple HTML escaping
            return html.escape(content)
    
    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """Sanitize plain text content."""
        if not text:
            return ""
        
        # HTML escape to prevent XSS
        escaped = html.escape(text)
        
        # Remove null bytes and other dangerous characters
        cleaned = escaped.replace('\x00', '').replace('\r\n', '\n')
        
        return cleaned
    
    @classmethod
    def sanitize_json(cls, data: Any) -> Any:
        """Recursively sanitize JSON data."""
        if isinstance(data, dict):
            return {cls.sanitize_text(str(k)): cls.sanitize_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.sanitize_json(item) for item in data]
        elif isinstance(data, str):
            return cls.sanitize_text(data)
        else:
            return data

class InputValidator:
    """Validates various types of input data."""
    
    # Security patterns to reject
    DANGEROUS_PATTERNS = [
        r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',  # Script tags
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',  # Event handlers
        r'eval\s*\(',  # eval() calls
        r'exec\s*\(',  # exec() calls
        r'setTimeout\s*\(',  # setTimeout calls
        r'setInterval\s*\(',  # setInterval calls
        r'document\.',  # DOM access
        r'window\.',  # Window access
        r'XMLHttpRequest',  # AJAX requests
        r'fetch\s*\(',  # Fetch API
    ]
    
    @classmethod
    def validate_user_id(cls, user_id: str) -> bool:
        """Validate user ID format and security."""
        if not user_id or not isinstance(user_id, str):
            return False
        
        user_id = user_id.strip()
        
        # Check length
        if len(user_id) < 3 or len(user_id) > 256:
            return False
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, user_id, re.IGNORECASE):
                return False
        
        # Check for valid patterns
        valid_patterns = [
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',  # UUID
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',  # Email
            r'^[a-zA-Z0-9][a-zA-Z0-9._-]{2,}[a-zA-Z0-9]$'  # Username
        ]
        
        return any(re.match(pattern, user_id, re.IGNORECASE) for pattern in valid_patterns)
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email format with enhanced security checks."""
        if not email or not isinstance(email, str):
            return False
        
        email = email.strip().lower()
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, email, re.IGNORECASE):
                return False
        
        # Strict email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False
        
        # Additional security checks
        parts = email.split('@')
        if len(parts) != 2:
            return False
        
        local, domain = parts
        
        # Check local part
        if len(local) > 64 or not local:
            return False
        
        # Check domain part
        if len(domain) > 255 or not domain:
            return False
        
        # Check for dangerous domain patterns
        dangerous_domains = ['localhost', '127.0.0.1', '0.0.0.0', 'example.com', 'test.com']
        if any(dangerous in domain for dangerous in dangerous_domains):
            return False
        
        return True
    
    @classmethod
    def validate_message_content(cls, content: str, max_length: int = 10000) -> bool:
        """Validate message content for security and length."""
        if not content or not isinstance(content, str):
            return False
        
        # Check length
        if len(content) > max_length:
            return False
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return False
        
        # Check for excessive control characters
        control_char_count = sum(1 for char in content if ord(char) < 32 and char not in '\n\r\t')
        if control_char_count > len(content) * 0.1:  # More than 10% control characters
            return False
        
        return True
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Validate URL format and security."""
        if not url or not isinstance(url, str):
            return False
        
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Only allow http and https
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check for dangerous patterns in URL
            for pattern in cls.DANGEROUS_PATTERNS:
                if re.search(pattern, url, re.IGNORECASE):
                    return False
            
            # Check for localhost/internal IPs in production
            dangerous_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '10.', '192.168.', '172.']
            if any(dangerous in parsed.netloc for dangerous in dangerous_hosts):
                return False
            
            return True
            
        except Exception:
            return False
    
    @classmethod
    def validate_uuid(cls, uuid_str: str) -> bool:
        """Validate UUID format."""
        if not uuid_str or not isinstance(uuid_str, str):
            return False
        
        try:
            uuid.UUID(uuid_str)
            return True
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def validate_json_structure(cls, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate JSON structure has required fields."""
        if not isinstance(data, dict):
            return False
        
        for field in required_fields:
            if field not in data:
                return False
        
        return True

class SecurityValidator:
    """Advanced security validation for requests."""
    
    @classmethod
    def validate_request_headers(cls, headers: Dict[str, str]) -> List[str]:
        """Validate request headers for security issues."""
        issues = []
        
        # Check Content-Type
        content_type = headers.get('content-type', '').lower()
        if content_type and 'application/json' not in content_type:
            issues.append("Invalid Content-Type header")
        
        # Check for dangerous headers
        dangerous_headers = ['x-forwarded-for', 'x-real-ip', 'x-cluster-client-ip']
        for header in dangerous_headers:
            if header in headers:
                issues.append(f"Potentially dangerous header: {header}")
        
        return issues
    
    @classmethod
    def validate_rate_limit(cls, user_id: str, current_requests: int, max_requests: int) -> bool:
        """Validate rate limiting for user."""
        return current_requests <= max_requests
    
    @classmethod
    def detect_injection_attempt(cls, content: str) -> bool:
        """Detect potential injection attempts."""
        # Skip overly large payloads to avoid regex performance issues
        if not content or len(content) > 32768:
            return False
        injection_patterns = [
            r'(\bUNION\b.*\bSELECT\b)',  # SQL injection
            r'(\bDROP\b.*\bTABLE\b)',  # SQL injection
            r'(\bINSERT\b.*\bINTO\b)',  # SQL injection
            r'(\bDELETE\b.*\bFROM\b)',  # SQL injection
            r'(<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>)',  # XSS
            r'(javascript:)',  # XSS
            r'(\bon\w+\s*=)',  # XSS event handlers
            r'(\$\{.*\})',  # Template injection
            r'(<%.*%>)',  # Template injection
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False

# Utility functions for easy access
def sanitize_user_input(content: str) -> str:
    """Sanitize user input content."""
    return InputSanitizer.sanitize_text(content)

def validate_user_data(user_data: Dict[str, Any]) -> bool:
    """Validate user data structure and content."""
    required_fields = ['id', 'email']
    
    if not InputValidator.validate_json_structure(user_data, required_fields):
        return False
    
    if not InputValidator.validate_user_id(user_data['id']):
        return False
    
    if not InputValidator.validate_email(user_data['email']):
        return False
    
    return True

def is_safe_content(content: str) -> bool:
    """Check if content is safe from security perspective."""
    if not InputValidator.validate_message_content(content):
        return False
    
    if SecurityValidator.detect_injection_attempt(content):
        return False
    
    return True


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add common security headers to every response."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        response = await call_next(request)
        headers = response.headers
        # Core MIME sniffing + framing protections
        headers["X-Content-Type-Options"] = "nosniff"
        headers["X-Frame-Options"] = "DENY"
        # Transport security (1 year, include subdomains)
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Content Security Policy with optional nonce support (env: CSP_NONCE_ENABLED=true)
        # Build dynamic connect-src list (allow self + configured service endpoints)
        connect_hosts = {"'self'"}
        for var in ("OLLAMA_BASE_URL", "CHROMA_HOST", "REDIS_HOST"):
            val = os.getenv(var)
            if val:
                # Extract scheme+host
                host = val.replace("http://", "").replace("https://", "").split('/')[0]
                if host:
                    connect_hosts.add(host)
        csp_base = "default-src 'self'; object-src 'none'; base-uri 'self'; connect-src " + ' '.join(sorted(connect_hosts))
        if os.getenv("CSP_NONCE_ENABLED", "false").lower() == "true":
            # Generate a simple random nonce per request
            import secrets
            nonce = secrets.token_urlsafe(16)
            # Attach nonce to request state for downstream template usage if needed
            if hasattr(request, 'state'):
                request.state.csp_nonce = nonce
            csp = csp_base + f"; script-src 'self' 'nonce-{nonce}'"
        else:
            csp = csp_base + "; script-src 'self'"
        headers["Content-Security-Policy"] = csp
        # Lock down powerful features we don't use yet
        headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        # Limit referrer leakage
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
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
        allow_headers=["*"])

    # Trusted hosts (only in production)
    if os.getenv("ENVIRONMENT") == "production":
        trusted_hosts = os.getenv("TRUSTED_HOSTS", "localhost").split(",")
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Rate limiting now managed centrally in main.py using middleware.rate_limit_middleware.RateLimitMiddleware

    # Request logging
    if os.getenv("LOG_REQUESTS", "true").lower() == "true":
        app.add_middleware(RequestLoggingMiddleware)

    logger.info("Security middleware configured successfully")


## NOTE: Legacy side-effectful validate_environment removed in favor of pure variant below.
def validate_environment() -> dict:
    """Collect environment + config values without side effects.

    Returns a dict of resolved settings; never raises (logs only).
    """
    info: dict = {"status": "ok"}
    try:
        from config.config_unified import Config
        config = Config.get_instance()
        info.update({
            "redis_host": os.getenv("REDIS_HOST") or config.database.redis_host,
            "chroma_host": os.getenv("CHROMA_HOST") or config.database.chroma_host,
            "default_model": os.getenv("DEFAULT_MODEL") or config.model.default_model,
            "ollama_base_url": os.getenv("OLLAMA_BASE_URL") or config.model.ollama_base_url,
        })
    except Exception as e:  # pragma: no cover
        info["status"] = "error"
        info["error"] = str(e)
    return info

def perform_environment_validation():  # retained for backward compatibility
    result = validate_environment()
    if result.get("status") == "ok":
        logger.info(
            "Environment validated: Redis=%s Chroma=%s Model=%s Ollama=%s",
            result.get("redis_host"), result.get("chroma_host"), result.get("default_model"), result.get("ollama_base_url")
        )
    else:
        logger.warning("Environment validation encountered issue: %s", result.get("error"))
    return result

def _validate_url_format(url: str) -> bool:
    """Validate URL format for configuration."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False
