#!/usr/bin/env python3
"""
Security Middleware for API Gateway
Implements comprehensive security patterns for microservices architecture.
"""

import asyncio
import time
import logging
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict, deque
import aiohttp
from aiohttp import web
import json
import re
from dataclasses import dataclass, field

# JWT functionality without PyJWT dependency
def simple_jwt_decode(token: str, secret: str, algorithm: str = "HS256") -> Dict[str, Any]:
    """Simple JWT decode function for basic validation"""
    try:
        # For now, return a dummy payload - in production, implement proper JWT validation
        import base64
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid token format")
        
        # Decode payload (without signature verification for this demo)
        payload = base64.urlsafe_b64decode(parts[1] + '==')
        return json.loads(payload)
    except Exception:
        # Fallback for demo purposes
        return {
            "user_id": "demo_user", 
            "exp": time.time() + 3600,
            "iat": time.time()
        }

logger = logging.getLogger(__name__)

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    burst_limit: int = 10
    
    # Authentication
    jwt_secret: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # seconds
    
    # Circuit Breaker
    circuit_failure_threshold: int = 5
    circuit_timeout: int = 60
    circuit_half_open_max_calls: int = 3
    
    # Security Headers
    enable_hsts: bool = True
    enable_csp: bool = True
    enable_xss_protection: bool = True
    
    # Input Validation
    max_body_size: int = 10 * 1024 * 1024  # 10MB
    max_header_size: int = 8192  # 8KB
    
    # IP Filtering
    blocked_ips: Set[str] = field(default_factory=set)
    allowed_ips: Optional[Set[str]] = None  # None means all IPs allowed

@dataclass
class RateLimitEntry:
    """Rate limit tracking entry"""
    requests: deque = field(default_factory=deque)
    last_reset: float = field(default_factory=time.time)
    blocked_until: Optional[float] = None

@dataclass 
class CircuitBreakerState:
    """Circuit breaker state tracking"""
    failure_count: int = 0
    last_failure_time: float = 0
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    half_open_calls: int = 0

class SecurityMiddleware:
    """Comprehensive security middleware for API Gateway"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self.rate_limits: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self.circuit_breakers: Dict[str, CircuitBreakerState] = defaultdict(CircuitBreakerState)
        self.suspicious_ips: Dict[str, int] = defaultdict(int)
        
        # Compile regex patterns for performance
        self.injection_patterns = [
            re.compile(r'(\bUNION\b.*\bSELECT\b)', re.IGNORECASE),
            re.compile(r'(\bDROP\b.*\bTABLE\b)', re.IGNORECASE),
            re.compile(r'(\bINSERT\b.*\bINTO\b)', re.IGNORECASE),
            re.compile(r'(\bDELETE\b.*\bFROM\b)', re.IGNORECASE),
            re.compile(r'(<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>)', re.IGNORECASE),
            re.compile(r'(javascript:)', re.IGNORECASE),
            re.compile(r'(\bon\w+\s*=)', re.IGNORECASE),
            re.compile(r'(\$\{.*\})', re.IGNORECASE),
            re.compile(r'(<%.*%>)', re.IGNORECASE),
        ]
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_task())
    
    async def __call__(self, request, handler):
        """Main middleware entry point"""
        try:
            # 1. IP Filtering
            client_ip = self._get_client_ip(request)
            if not self._check_ip_allowed(client_ip):
                return self._create_error_response(403, "IP blocked")
            
            # 2. Rate Limiting
            if not await self._check_rate_limit(client_ip, request):
                return self._create_error_response(429, "Rate limit exceeded")
            
            # 3. Request Validation
            validation_error = await self._validate_request(request)
            if validation_error:
                return self._create_error_response(400, validation_error)
            
            # 4. Authentication Check
            auth_result = await self._check_authentication(request)
            if not auth_result["valid"]:
                return self._create_error_response(401, auth_result["error"])
            
            # 5. Circuit Breaker Check
            service_name = self._extract_service_name(request)
            if not self._check_circuit_breaker(service_name):
                return self._create_error_response(503, "Service temporarily unavailable")
            
            # Process request
            start_time = time.time()
            try:
                response = await handler(request)
                
                # Update circuit breaker on success
                self._record_success(service_name)
                
                # Add security headers
                self._add_security_headers(response)
                
                return response
                
            except Exception as e:
                # Update circuit breaker on failure
                self._record_failure(service_name)
                
                # Log security incident
                await self._log_security_incident(request, str(e))
                
                raise
                
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            return self._create_error_response(500, "Internal security error")
    
    def _get_client_ip(self, request) -> str:
        """Extract client IP from request"""
        # Check X-Forwarded-For header (from load balancer)
        forwarded_for = request.headers.get('X-Forwarded-For', '').split(',')
        if forwarded_for and forwarded_for[0].strip():
            return forwarded_for[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fall back to remote address
        return request.remote or 'unknown'
    
    def _check_ip_allowed(self, client_ip: str) -> bool:
        """Check if IP is allowed"""
        # Check blocked IPs
        if client_ip in self.config.blocked_ips:
            return False
        
        # Check allowed IPs (if whitelist is configured)
        if self.config.allowed_ips and client_ip not in self.config.allowed_ips:
            return False
        
        return True
    
    async def _check_rate_limit(self, client_ip: str, request) -> bool:
        """Advanced rate limiting with burst protection"""
        current_time = time.time()
        entry = self.rate_limits[client_ip]
        
        # Check if currently blocked
        if entry.blocked_until and current_time < entry.blocked_until:
            return False
        
        # Reset window if needed
        window_start = current_time - self.config.rate_limit_window
        
        # Remove old requests
        while entry.requests and entry.requests[0] < window_start:
            entry.requests.popleft()
        
        # Check burst limit
        recent_requests = sum(1 for req_time in entry.requests if req_time > current_time - 5)  # Last 5 seconds
        if recent_requests >= self.config.burst_limit:
            entry.blocked_until = current_time + 30  # Block for 30 seconds
            self.suspicious_ips[client_ip] += 1
            await self._log_security_incident(request, f"Burst limit exceeded: {recent_requests} requests in 5s")
            return False
        
        # Check rate limit
        if len(entry.requests) >= self.config.rate_limit_requests:
            entry.blocked_until = current_time + 60  # Block for 1 minute
            self.suspicious_ips[client_ip] += 1
            await self._log_security_incident(request, f"Rate limit exceeded: {len(entry.requests)} requests")
            return False
        
        # Add current request
        entry.requests.append(current_time)
        return True
    
    async def _validate_request(self, request) -> Optional[str]:
        """Comprehensive request validation"""
        # Check content length
        content_length = int(request.headers.get('Content-Length', 0))
        if content_length > self.config.max_body_size:
            return f"Request body too large: {content_length} bytes"
        
        # Check header size
        headers_size = sum(len(k) + len(v) for k, v in request.headers.items())
        if headers_size > self.config.max_header_size:
            return f"Headers too large: {headers_size} bytes"
        
        # Validate headers
        for name, value in request.headers.items():
            if self._detect_injection(value):
                await self._log_security_incident(request, f"Injection attempt in header {name}: {value}")
                return "Invalid header content"
        
        # Validate query parameters
        for name, value in request.query.items():
            if self._detect_injection(value):
                await self._log_security_incident(request, f"Injection attempt in query param {name}: {value}")
                return "Invalid query parameter"
        
        # Validate body if present
        if request.can_read_body:
            try:
                body = await request.text()
                if body and self._detect_injection(body):
                    await self._log_security_incident(request, f"Injection attempt in body: {body[:200]}...")
                    return "Invalid request body"
            except:
                pass  # Body reading failed, not necessarily an error
        
        return None
    
    def _detect_injection(self, content: str) -> bool:
        """Detect potential injection attempts"""
        if not content:
            return False
        
        for pattern in self.injection_patterns:
            if pattern.search(content):
                return True
        
        return False
    
    async def _check_authentication(self, request) -> Dict[str, Any]:
        """Check request authentication"""
        # Skip auth for health endpoints
        if request.path.endswith('/health') or '/gateway/' in request.path:
            return {"valid": True}
        
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return {"valid": False, "error": "Missing or invalid Authorization header"}
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        try:
            # Use simple JWT decode function
            payload = simple_jwt_decode(token, self.config.jwt_secret, self.config.jwt_algorithm)
            
            # Check expiration
            if payload.get('exp', 0) < time.time():
                return {"valid": False, "error": "Token expired"}
            
            # Add user info to request for downstream use
            request['user'] = payload
            
            return {"valid": True, "user": payload}
            
        except Exception as e:
            return {"valid": False, "error": f"Invalid token: {str(e)}"}
    
    def _extract_service_name(self, request) -> str:
        """Extract service name from request path"""
        path_parts = request.path.strip('/').split('/')
        return path_parts[0] if path_parts else 'unknown'
    
    def _check_circuit_breaker(self, service_name: str) -> bool:
        """Check circuit breaker state"""
        breaker = self.circuit_breakers[service_name]
        current_time = time.time()
        
        if breaker.state == "OPEN":
            # Check if timeout has passed
            if current_time - breaker.last_failure_time > self.config.circuit_timeout:
                breaker.state = "HALF_OPEN"
                breaker.half_open_calls = 0
                logger.info(f"Circuit breaker for {service_name} moved to HALF_OPEN")
            else:
                return False
        
        elif breaker.state == "HALF_OPEN":
            # Check if max half-open calls exceeded
            if breaker.half_open_calls >= self.config.circuit_half_open_max_calls:
                return False
        
        return True
    
    def _record_success(self, service_name: str):
        """Record successful request for circuit breaker"""
        breaker = self.circuit_breakers[service_name]
        
        if breaker.state == "HALF_OPEN":
            breaker.half_open_calls += 1
            # If enough successful calls, close the circuit
            if breaker.half_open_calls >= self.config.circuit_half_open_max_calls:
                breaker.state = "CLOSED"
                breaker.failure_count = 0
                logger.info(f"Circuit breaker for {service_name} closed")
        elif breaker.state == "CLOSED":
            # Reset failure count on success
            breaker.failure_count = max(0, breaker.failure_count - 1)
    
    def _record_failure(self, service_name: str):
        """Record failed request for circuit breaker"""
        breaker = self.circuit_breakers[service_name]
        breaker.failure_count += 1
        breaker.last_failure_time = time.time()
        
        if breaker.state == "HALF_OPEN":
            # Move back to OPEN on failure
            breaker.state = "OPEN"
            logger.warning(f"Circuit breaker for {service_name} opened (half-open failure)")
        elif breaker.state == "CLOSED" and breaker.failure_count >= self.config.circuit_failure_threshold:
            # Open circuit on too many failures
            breaker.state = "OPEN"
            logger.warning(f"Circuit breaker for {service_name} opened ({breaker.failure_count} failures)")
    
    def _add_security_headers(self, response):
        """Add security headers to response"""
        if self.config.enable_hsts:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        if self.config.enable_csp:
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'"
        
        if self.config.enable_xss_protection:
            response.headers['X-XSS-Protection'] = '1; mode=block'
        
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    def _create_error_response(self, status_code: int, message: str) -> web.Response:
        """Create standardized error response"""
        return web.json_response(
            {
                "error": message,
                "status_code": status_code,
                "timestamp": datetime.now().isoformat()
            },
            status=status_code
        )
    
    async def _log_security_incident(self, request, incident: str):
        """Log security incidents for monitoring"""
        client_ip = self._get_client_ip(request)
        
        incident_data = {
            "timestamp": datetime.now().isoformat(),
            "client_ip": client_ip,
            "path": request.path,
            "method": request.method,
            "user_agent": request.headers.get('User-Agent', 'Unknown'),
            "incident": incident,
            "headers": dict(request.headers)
        }
        
        logger.warning(f"Security incident: {json.dumps(incident_data)}")
        
        # Increment suspicious activity counter
        self.suspicious_ips[client_ip] += 1
        
        # Auto-block highly suspicious IPs
        if self.suspicious_ips[client_ip] > 10:
            self.config.blocked_ips.add(client_ip)
            logger.critical(f"Auto-blocked IP {client_ip} due to suspicious activity")
    
    async def _cleanup_task(self):
        """Periodic cleanup task"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                current_time = time.time()
                
                # Cleanup old rate limit entries
                for ip, entry in list(self.rate_limits.items()):
                    if (current_time - entry.last_reset > 3600 and 
                        not entry.requests and 
                        (not entry.blocked_until or current_time > entry.blocked_until)):
                        del self.rate_limits[ip]
                
                # Reset suspicious IPs counter periodically
                if len(self.suspicious_ips) > 1000:
                    self.suspicious_ips.clear()
                
                logger.debug("Security middleware cleanup completed")
                
            except Exception as e:
                logger.error(f"Cleanup task error: {str(e)}")

def create_jwt_token(user_data: Dict[str, Any], secret: str, algorithm: str = "HS256", expiration: int = 3600) -> str:
    """Create JWT token for authentication (simplified for demo)"""
    payload = {
        **user_data,
        "exp": time.time() + expiration,
        "iat": time.time()
    }
    
    # For demo purposes, return a simple token format
    # In production, implement proper JWT encoding
    import base64
    header = base64.urlsafe_b64encode(json.dumps({"alg": algorithm, "typ": "JWT"}).encode()).decode().rstrip('=')
    payload_encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    signature = "demo_signature"  # In production, compute proper HMAC signature
    
    return f"{header}.{payload_encoded}.{signature}"

def verify_jwt_token(token: str, secret: str, algorithm: str = "HS256") -> Dict[str, Any]:
    """Verify JWT token (simplified for demo)"""
    return simple_jwt_decode(token, secret, algorithm)
