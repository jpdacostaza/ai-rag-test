"""
HTTP Response Caching Middleware
===============================

Provides intelligent caching for HTTP responses based on route patterns and content types.
Supports ETags, conditional requests, and configurable cache strategies.
"""

import hashlib
import json
import time
from typing import Dict, Optional, Set, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from core.unified_logging import get_logger
from utilities.cache_manager import CacheManager

logger = get_logger(__name__)

class HTTPCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware for caching HTTP responses with intelligent cache strategies.
    """
    
    def __init__(
        self, 
        app,
        default_ttl: int = 300,  # 5 minutes
        max_cache_size: int = 1000,
        cache_get_only: bool = True,
        exclude_paths: Optional[Set[str]] = None
    ):
        super().__init__(app)
        self.logger = get_logger(__name__)
        self.cache = CacheManager[Dict](max_size=max_cache_size)
        self.default_ttl = default_ttl
        self.cache_get_only = cache_get_only
        self.exclude_paths = exclude_paths or {
            '/health', '/metrics', '/admin', '/auth'
        }
        
        # Route-specific cache configurations
        self.route_cache_config = {
            '/api/models': {'ttl': 3600, 'cache_headers': True},
            '/api/tools': {'ttl': 1800, 'cache_headers': True},
            '/api/functions': {'ttl': 1800, 'cache_headers': True},
            '/chat': {'ttl': 0, 'cache_headers': False},  # No caching for chat
            '/memory': {'ttl': 300, 'cache_headers': True},
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with response caching."""
        
        # Skip caching for non-GET requests if configured
        if self.cache_get_only and request.method != 'GET':
            return await call_next(request)
        
        # Skip caching for excluded paths
        path = request.url.path
        if any(excluded in path for excluded in self.exclude_paths):
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Check for cached response
        cached_response = self.cache.get(cache_key)
        if cached_response and self._is_cache_valid(cached_response):
            self.logger.debug(f"HTTP cache hit for {path}")
            return self._create_response_from_cache(cached_response, request)
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses
        if self._should_cache_response(request, response):
            await self._cache_response(cache_key, request, response)
        
        # Add cache headers
        self._add_cache_headers(response, request)
        
        return response
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request."""
        # Include method, path, and relevant query parameters
        key_parts = [
            request.method,
            str(request.url.path),
            str(sorted(request.query_params.items()))
        ]
        
        # Include user context if available (for user-specific caching)
        if hasattr(request.state, 'user_id'):
            key_parts.append(f"user:{request.state.user_id}")
        
        key_string = '|'.join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    def _should_cache_response(self, request: Request, response: Response) -> bool:
        """Determine if response should be cached."""
        # Only cache successful responses
        if response.status_code != 200:
            return False
        
        # Check route-specific configuration
        path = request.url.path
        route_config = self._get_route_config(path)
        
        # Don't cache if TTL is 0
        if route_config.get('ttl', self.default_ttl) == 0:
            return False
        
        return True
    
    def _cache_response(self, cache_key: str, request: Request, response: Response):
        """Cache the response."""
        try:
            # Read response body
            body = b""
            if hasattr(response, 'body'):
                body = response.body
            elif hasattr(response, 'body_iterator'):
                # For streaming responses, this is more complex
                # For now, skip caching streaming responses
                return
            
            # Get route configuration
            route_config = self._get_route_config(request.url.path)
            ttl = route_config.get('ttl', self.default_ttl)
            
            # Create cache entry
            cache_entry = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': body,
                'timestamp': time.time(),
                'ttl': ttl,
                'content_type': response.headers.get('content-type', 'application/json')
            }
            
            self.cache.set(cache_key, cache_entry)
            self.logger.debug(f"Cached response for {request.url.path} (TTL: {ttl}s)")
            
        except Exception as e:
            self.logger.warning(f"Failed to cache response: {e}")
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cached entry is still valid."""
        age = time.time() - cache_entry['timestamp']
        return age < cache_entry['ttl']
    
    def _create_response_from_cache(self, cache_entry: Dict, request: Request) -> Response:
        """Create response from cached entry."""
        headers = cache_entry['headers'].copy()
        
        # Add cache-related headers
        age = int(time.time() - cache_entry['timestamp'])
        headers['Age'] = str(age)
        headers['X-Cache'] = 'HIT'
        
        # Handle ETags for conditional requests
        etag = cache_entry.get('etag')
        if etag and request.headers.get('if-none-match') == etag:
            return Response(status_code=304, headers=headers)
        
        return Response(
            content=cache_entry['body'],
            status_code=cache_entry['status_code'],
            headers=headers
        )
    
    def _add_cache_headers(self, response: Response, request: Request):
        """Add cache-related headers to response."""
        route_config = self._get_route_config(request.url.path)
        
        if route_config.get('cache_headers', True):
            # Add ETag for content validation
            if hasattr(response, 'body') and response.body:
                etag = hashlib.md5(response.body).hexdigest()[:16]
                response.headers['ETag'] = f'"{etag}"'
            
            # Add cache control headers
            ttl = route_config.get('ttl', self.default_ttl)
            if ttl > 0:
                response.headers['Cache-Control'] = f'public, max-age={ttl}'
            else:
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
        # Always add cache status
        if 'X-Cache' not in response.headers:
            response.headers['X-Cache'] = 'MISS'
    
    def _get_route_config(self, path: str) -> Dict:
        """Get caching configuration for specific route."""
        # Check for exact match first
        if path in self.route_cache_config:
            return self.route_cache_config[path]
        
        # Check for pattern matches
        for pattern, config in self.route_cache_config.items():
            if pattern in path:
                return config
        
        # Return default configuration
        return {'ttl': self.default_ttl, 'cache_headers': True}


class ETagMiddleware(BaseHTTPMiddleware):
    """
    Lightweight middleware for ETag-based conditional requests.
    Useful when full response caching is not needed.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add ETag for successful GET responses
        if request.method == 'GET' and response.status_code == 200:
            if hasattr(response, 'body') and response.body:
                etag = hashlib.md5(response.body).hexdigest()[:16]
                response.headers['ETag'] = f'"{etag}"'
                
                # Check if client has current version
                client_etag = request.headers.get('if-none-match')
                if client_etag == f'"{etag}"':
                    return Response(status_code=304)
        
        return response
