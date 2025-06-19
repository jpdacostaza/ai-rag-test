"""
Authentication Module for FastAPI Backend
Handles API key validation, user authentication, and security functions
"""

import os
import hashlib
import secrets
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from human_logging import log_api_request, log_service_status

class AuthenticationManager:
    """Centralized authentication management"""
    
    def __init__(self):
        self.valid_api_keys = self._load_api_keys()
        self.failed_attempts = {}  # Track failed authentication attempts
        self.rate_limits = {}      # Track rate limiting per API key
        
    def _load_api_keys(self) -> List[str]:
        """Load valid API keys from environment and defaults"""
        keys = [
            os.getenv("API_KEY", "f2b985dd-219f-45b1-a90e-170962cc7082"),  # Primary test key
            os.getenv("DEV_API_KEY", "dev-api-key-12345"),                 # Development key
            "f2b985dd-219f-45b1-a90e-170962cc7082",                        # Explicit test key
            "production-api-key-2025",                                      # Production placeholder
        ]
        
        # Remove duplicates and None values
        valid_keys = list(set(filter(None, keys)))
        log_service_status("AUTH", "ready", f"Loaded {len(valid_keys)} valid API keys")
        return valid_keys
    
    def validate_api_key(self, api_key: Optional[str]) -> bool:
        """
        Validate an API key against known valid keys
        
        Args:
            api_key: The API key to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not api_key:
            return False
            
        # Check against valid keys
        is_valid = api_key in self.valid_api_keys
        
        if is_valid:
            log_service_status("AUTH", "success", f"Valid API key used: {api_key[:10]}...")
        else:
            log_service_status("AUTH", "warning", f"Invalid API key attempted: {api_key[:10] if api_key else 'None'}...")
            self._track_failed_attempt(api_key)
            
        return is_valid
    
    def _track_failed_attempt(self, api_key: Optional[str]):
        """Track failed authentication attempts for security monitoring"""
        key = api_key[:10] if api_key else "anonymous"
        now = datetime.now()
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = []
            
        self.failed_attempts[key].append(now)
        
        # Clean old attempts (older than 1 hour)
        cutoff = now - timedelta(hours=1)
        self.failed_attempts[key] = [
            attempt for attempt in self.failed_attempts[key] 
            if attempt > cutoff
        ]
        
        # Log if too many failed attempts
        if len(self.failed_attempts[key]) > 5:
            log_service_status("AUTH", "error", f"Multiple failed auth attempts from key: {key}")
    
    def extract_api_key(self, authorization: Optional[str] = None, api_key_param: Optional[str] = None) -> Optional[str]:
        """
        Extract API key from various sources
        
        Args:
            authorization: Authorization header value
            api_key_param: API key from query parameter
            
        Returns:
            str or None: Extracted API key
        """
        # Try Authorization header first (Bearer token)
        if authorization and authorization.startswith("Bearer "):
            return authorization[7:]  # Remove "Bearer " prefix
            
        # Try query parameter
        if api_key_param:
            return api_key_param
            
        return None
    
    def create_auth_error_response(self) -> Dict[str, Any]:
        """Create standardized authentication error response"""
        return {
            "error": "Unauthorized",
            "message": "Valid API key required. Use Authorization: Bearer <api_key> or ?api_key=<api_key>",
            "valid_test_key": "f2b985dd-219f-45b1-a90e-170962cc7082",
            "documentation": "/docs"
        }
    
    def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics for monitoring"""
        return {
            "valid_keys_count": len(self.valid_api_keys),
            "failed_attempts_last_hour": sum(len(attempts) for attempts in self.failed_attempts.values()),
            "monitored_keys": list(self.failed_attempts.keys()),
            "last_check": datetime.now().isoformat()
        }

# Global authentication manager instance
auth_manager = AuthenticationManager()

def validate_api_key(api_key: Optional[str] = None) -> bool:
    """
    Convenience function for API key validation
    
    Args:
        api_key: The API key to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return auth_manager.validate_api_key(api_key)

def extract_api_key_from_request(authorization: Optional[str] = None, api_key_param: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to extract API key from request
    
    Args:
        authorization: Authorization header value
        api_key_param: API key from query parameter
        
    Returns:
        str or None: Extracted API key
    """
    return auth_manager.extract_api_key(authorization, api_key_param)

def create_auth_exception() -> HTTPException:
    """
    Create a standardized authentication HTTPException
    
    Returns:
        HTTPException: 401 Unauthorized with proper details
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=auth_manager.create_auth_error_response()
    )
