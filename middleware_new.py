"""
Middleware Module for FastAPI Backend
Handles request/response middleware including authentication, logging, and security
"""

import time
import json
from typing import Set, List, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from human_logging import log_api_request, log_service_status
from authentication import auth_manager

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware that validates API keys for protected endpoints
    """
    
    def __init__(self, app, skip_auth_paths: Optional[Set[str]] = None):
        super().__init__(app)
        # Paths that don't require authentication
        self.skip_auth_paths = skip_auth_paths or {
            "/health",
            "/health/",
            "/health/detailed",
            "/health/storage", 
            "/docs",
            "/docs/",            "/openapi.json",
            "/redoc",
            "/favicon.ico",
            "/"        }
        log_service_status("MIDDLEWARE", "ready", f"Authentication middleware initialized with {len(self.skip_auth_paths)} skip paths")
    
    async def dispatch(self, request: Request, call_next):
        """
        Process each request through authentication middleware
        
        Args:
            request: FastAPI Request object
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response: HTTP response
        """
        start_time = time.time()
        
        # Debug logging to verify middleware is being called
        print("DEBUG: Authentication middleware dispatch() called")
        print(f"🔐 AUTH MIDDLEWARE: Processing {request.method} {request.url.path}")
        log_service_status("AUTH", "debug", f"🔐 Processing {request.method} {request.url.path}")
        
        # Check if this path should skip authentication
        if self._should_skip_auth(request):
            response = await call_next(request)
            self._log_request(request, response, start_time, auth_skipped=True)
            return response
        
        # Extract API key from request
        api_key = self._extract_api_key_from_request(request)
        
        # Validate API key
        if not auth_manager.validate_api_key(api_key):
            # Create authentication error response
            error_response = JSONResponse(
                status_code=401,
                content=auth_manager.create_auth_error_response()
            )
            self._log_request(request, error_response, start_time, auth_failed=True)
            return error_response
        
        # Authentication successful, proceed with request
        response = await call_next(request)
        self._log_request(request, response, start_time, auth_success=True, api_key=api_key)
        return response
    
    def _should_skip_auth(self, request: Request) -> bool:
        """
        Determine if authentication should be skipped for this request
        
        Args:
            request: FastAPI Request object
            
        Returns:
            bool: True if auth should be skipped
        """
        path = request.url.path
        method = request.method
        
        # Skip auth for OPTIONS requests (CORS)
        if method == "OPTIONS":
            return True
            
        # Skip auth for specific paths
        for skip_path in self.skip_auth_paths:
            if path.startswith(skip_path):
                return True
                
        return False
    
    def _extract_api_key_from_request(self, request: Request) -> Optional[str]:
        """
        Extract API key from request headers or query parameters
        
        Args:
            request: FastAPI Request object
            
        Returns:
            str or None: Extracted API key
        """
        # Try Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
            
        # Try query parameter
        api_key_param = request.query_params.get("api_key")
        if api_key_param:
            return api_key_param
            
        return None
    
    def _log_request(self, request: Request, response: Response, start_time: float, 
                    auth_skipped: bool = False, auth_failed: bool = False, 
                    auth_success: bool = False, api_key: Optional[str] = None):
        """
        Log request details with authentication information
        
        Args:
            request: FastAPI Request object
            response: FastAPI Response object  
            start_time: Request start time
            auth_skipped: Whether auth was skipped
            auth_failed: Whether auth failed
            auth_success: Whether auth succeeded
            api_key: API key used (if any)
        """
        duration_ms = (time.time() - start_time) * 1000
        
        # Create log entry
        log_details = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "auth_status": "skipped" if auth_skipped else ("failed" if auth_failed else ("success" if auth_success else "unknown")),
        }
        
        if api_key and auth_success:
            log_details["api_key_prefix"] = api_key[:10] + "..."
            
        # Log with appropriate level
        if auth_failed:
            log_service_status("AUTH", "warning", f"❌ {request.method} {request.url.path} → {response.status_code} (auth failed)")
        elif auth_success:
            log_service_status("AUTH", "success", f"✅ {request.method} {request.url.path} → {response.status_code} (authenticated)")
        else:
            log_api_request(request.method, request.url.path, response.status_code, duration_ms)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request logging middleware for comprehensive request/response logging
    """
    
    def __init__(self, app):
        super().__init__(app)
        log_service_status("MIDDLEWARE", "ready", "Request logging middleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """
        Log all requests and responses
        
        Args:
            request: FastAPI Request object
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response: HTTP response
        """
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log request
        log_api_request(
            request.method, 
            request.url.path, 
            response.status_code, 
            duration_ms
        )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware to add security-related HTTP headers
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY", 
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
        }
        log_service_status("MIDDLEWARE", "ready", f"Security headers middleware initialized with {len(self.security_headers)} headers")
    
    async def dispatch(self, request: Request, call_next):
        """
        Add security headers to responses
        
        Args:
            request: FastAPI Request object
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response: HTTP response with security headers
        """
        response = await call_next(request)
        
        # Add security headers
        for header_name, header_value in self.security_headers.items():
            response.headers[header_name] = header_value
            
        return response


def setup_middleware(app):
    """
    Set up all middleware for the FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    # Add middleware in reverse order (last added = first executed)
    
    # 3. Security headers (applied last, closest to response)
    app.add_middleware(SecurityHeadersMiddleware)
    log_service_status("MIDDLEWARE", "ready", "Security headers middleware added")
    
    # 2. Request logging 
    app.add_middleware(RequestLoggingMiddleware)
    log_service_status("MIDDLEWARE", "ready", "Request logging middleware added")
    
    # 1. Authentication (applied first, closest to request)
    app.add_middleware(AuthenticationMiddleware)
    log_service_status("MIDDLEWARE", "ready", "Authentication middleware added")
    
    log_service_status("MIDDLEWARE", "ready", "All middleware successfully configured")
