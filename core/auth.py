"""
Unified Authentication Manager
=============================

This module consolidates all authentication logic into a single, secure,
and consistent implementation to eliminate duplicate code and security inconsistencies.
"""

import re
import uuid
import hashlib
import hmac
import time
from typing import Dict, Any, Optional, Tuple, List
from config.config_unified import Config
from core.security import InputValidator, sanitize_user_input
from core.unified_logging import get_logger, log_service_status

class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass

class UnifiedAuthManager:
    """
    Unified authentication manager that consolidates all authentication logic.
    Replaces multiple duplicate implementations throughout the codebase.
    """
    
    def __init__(self, debug: bool = None):
        self.config = Config.get_instance()
        self.debug = debug if debug is not None else self.config.security.enable_debug
        # in-memory rate limit tracking: {user_id: [timestamps]}
        self._rate_limit_cache: Dict[str, List[float]] = {}
        self.logger = get_logger("auth")
    
    def log(self, message: str, level: str = "INFO"):
        """Log messages via unified logger when debug enabled."""
        if not self.debug:
            return
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "DEBUG":
            self.logger.debug(message)
        else:
            self.logger.info(message)
    
    def validate_uuid(self, user_id: str) -> bool:
        """Validate UUID format using centralized validation."""
        return InputValidator.validate_uuid(user_id)
    
    def validate_email(self, email: str) -> bool:
        """Validate email format using centralized validation."""
        return InputValidator.validate_email(email)
    
    def validate_user_id(self, user_id: str) -> bool:
        """Validate user ID using centralized validation."""
        return InputValidator.validate_user_id(user_id)
    
    def extract_user_from_request(self, body: Dict[str, Any], user_param: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Extract user information from request with strict validation.
        Consolidates all user extraction logic.
        """
        user_data = {}
        user_id = None
        
        # Method 1: From user parameter (OpenWebUI pipeline style)
        if user_param and isinstance(user_param, dict):
            user_id = self._extract_from_user_object(user_param)
            if user_id:
                user_data = user_param
                if self.debug:
                    self.log(f"[OK] User ID from parameter: {user_id}")
                return user_id, user_data
        
        # Method 2: From __user__ object in body (most reliable)
        if "__user__" in body and isinstance(body["__user__"], dict):
            user_obj = body["__user__"]
            user_id = self._extract_from_user_object(user_obj)
            if user_id:
                user_data = user_obj
                if self.debug:
                    self.log(f"[OK] User ID from __user__ object: {user_id}")
                return user_id, user_data
        
        # Method 3: From direct user_id field
        user_id = body.get("user_id")
        if user_id and isinstance(user_id, str):
            candidate = sanitize_user_input(user_id.strip())
            if self.validate_user_id(candidate):
                if self.debug:
                    self.log(f"[OK] User ID from body field: {candidate}")
                return candidate, user_data
        
        # Method 4: From user object in body
        if "user" in body and isinstance(body["user"], dict):
            user_obj = body["user"]
            user_id = self._extract_from_user_object(user_obj)
            if user_id:
                user_data = user_obj
                if self.debug:
                    self.log(f"[OK] User ID from user object: {user_id}")
                return user_id, user_data
        
        if self.debug:
            self.log("[FAIL] No valid user ID found in request")
        
        return None, user_data
    
    def _extract_from_user_object(self, user_obj: Dict[str, Any]) -> Optional[str]:
        """Extract user ID from user object with priority ordering."""
        if not isinstance(user_obj, dict):
            return None
        
        # Priority order: id (UUID) > email > username > name
        priority_fields = ["id", "email", "username", "name"]
        
        for field in priority_fields:
            value = user_obj.get(field)
            if value and isinstance(value, str):
                value = sanitize_user_input(value.strip())
                if self.validate_user_id(value):
                    return value
        
        return None
    
    def authenticate_user_strict(self, body: Dict[str, Any], user_param: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Authenticate user with STRICT validation - NO fallbacks.
        This is the primary authentication method that should be used everywhere.
        """
        
        # Extract user information
        user_id, user_data = self.extract_user_from_request(body, user_param)
        
        if not user_id:
            if self.debug:
                self.log("[FAIL] AUTHENTICATION FAILED: No valid user ID found")
            return None, {}
        
        # Strict validation
        if not self._validate_user_data(user_data):
            if self.debug:
                self.log(f"[FAIL] AUTHENTICATION FAILED: Invalid user data for user {user_id}")
            return None, {}
        
        # Rate limiting check
        if not self._check_rate_limit(user_id):
            if self.debug:
                self.log(f"[FAIL] AUTHENTICATION FAILED: Rate limit exceeded for user {user_id}")
            return None, {}
        
        # Success
        if self.debug:
            self.log(f"[OK] AUTHENTICATION SUCCESS: {user_id}")
            if user_data:
                email = user_data.get("email", "Unknown")
                name = user_data.get("name", "Unknown")
                role = user_data.get("role", "user")
                self.log(f" User Profile: {name} ({email}) - Role: {role}")
        
        return user_id, user_data
    
    def _validate_user_data(self, user_data: Dict[str, Any]) -> bool:
        """Validate user data structure and content."""
        if not user_data:
            return True  # Empty user data is acceptable if we have a valid user_id
        
        # If email is present, it must be valid
        if "email" in user_data:
            email = user_data["email"]
            if email and not self.validate_email(email):
                return False
        
        # If id is present, it must be valid
        if "id" in user_data:
            user_id = user_data["id"]
            if user_id and not self.validate_user_id(user_id):
                return False
        
        return True
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check rate limiting for user (simple sliding window)."""
        if not self.config.security.enable_rate_limiting:
            return True

        current_time = time.time()
        window_size = 60  # seconds
        max_requests = self.config.security.max_requests_per_minute
        cutoff_time = current_time - window_size

        # Prune old timestamps and empty keys
        for uid, timestamps in list(self._rate_limit_cache.items()):
            pruned = [t for t in timestamps if t > cutoff_time]
            if pruned:
                self._rate_limit_cache[uid] = pruned
            else:
                # remove empty user key to prevent unbounded growth
                self._rate_limit_cache.pop(uid, None)

        user_requests = self._rate_limit_cache.get(user_id, [])
        if len(user_requests) >= max_requests:
            return False
        user_requests.append(current_time)
        self._rate_limit_cache[user_id] = user_requests
        return True
    
    def validate_session_consistency(self, user_id: str, body: Dict[str, Any]) -> bool:
        """Validate that the user session is consistent."""
        try:
            # Check if user_id appears consistently in the request
            found_ids = []
            
            # Check __user__ object
            if "__user__" in body and isinstance(body["__user__"], dict):
                user_obj_id = body["__user__"].get("id")
                if user_obj_id:
                    found_ids.append(user_obj_id)
            
            # Check direct user_id
            direct_id = body.get("user_id")
            if direct_id:
                found_ids.append(direct_id)
            
            # Check user object
            if "user" in body and isinstance(body["user"], dict):
                user_obj_id = body["user"].get("id")
                if user_obj_id:
                    found_ids.append(user_obj_id)
            
            # Validate consistency
            unique_ids = set(found_ids)
            if len(unique_ids) <= 1 and (not unique_ids or user_id in unique_ids):
                if self.debug:
                    self.log(f"[OK] Session consistency validated for user {user_id}")
                return True
            else:
                if self.debug:
                    self.log(f"[FAIL] Session inconsistency detected: found {unique_ids}, expected {user_id}")
                return False
        
        except Exception as e:
            if self.debug:
                self.log(f"[FAIL] Session validation error: {e}", "ERROR")
            return False
    
    def generate_session_token(self, user_id: str, user_data: Dict[str, Any]) -> str:
        """Generate a secure session token for the user."""
        timestamp = str(int(time.time()))
        payload = f"{user_id}:{timestamp}:{user_data.get('email', '')}"
        
        # Create HMAC signature
        signature = hmac.new(
            self.config.security.jwt_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{payload}:{signature}"
    
    def validate_session_token(self, token: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Validate a session token and return user info if valid.

        Format: user_id:timestamp:email(optional):hmac
        """
        try:
            parts = token.split(':', 3)
            if len(parts) != 4:
                return None
            user_id, timestamp_str, email, signature = parts
            # basic sanity
            if not self.validate_user_id(user_id):
                return None
            try:
                ts_int = int(timestamp_str)
            except ValueError:
                return None

            payload = f"{user_id}:{timestamp_str}:{email}"
            expected_signature = hmac.new(
                self.config.security.jwt_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(signature, expected_signature):
                return None
            # configurable max age (default 24h)
            max_age = getattr(self.config.security, 'session_token_ttl_seconds', 86400)
            if (time.time() - ts_int) > max_age:
                return None
            user_data = {"id": user_id}
            if email:
                user_data["email"] = email
            return user_id, user_data
        except Exception as e:
            if self.debug:
                self.log(f"[FAIL] Token validation error: {e}", "ERROR")
            return None
    
    def get_user_context_summary(self, user_data: Dict[str, Any]) -> str:
        """Generate a summary of user context for logging."""
        if not user_data:
            return "No user context available"
        
        parts = []
        if "name" in user_data:
            parts.append(f"Name: {user_data['name']}")
        if "email" in user_data:
            parts.append(f"Email: {user_data['email']}")
        if "role" in user_data:
            parts.append(f"Role: {user_data['role']}")
        
        return " | ".join(parts) if parts else "Limited user context"
    
    def clear_rate_limit_cache(self, user_id: Optional[str] = None):
        """Clear rate limit cache for specific user or all users."""
        if user_id:
            self._rate_limit_cache.pop(user_id, None)
        else:
            self._rate_limit_cache.clear()

# Global authentication manager instance
_auth_manager = None

def get_auth_manager() -> UnifiedAuthManager:
    """Get the global authentication manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = UnifiedAuthManager()
    return _auth_manager

def authenticate_request(body: Dict[str, Any], user_param: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Authenticate a request using the unified authentication system.
    This function should replace all duplicate authentication calls throughout the codebase.
    """
    auth_manager = get_auth_manager()
    return auth_manager.authenticate_user_strict(body, user_param)

def validate_user_session(user_id: str, body: Dict[str, Any]) -> bool:
    """Validate user session consistency."""
    auth_manager = get_auth_manager()
    return auth_manager.validate_session_consistency(user_id, body)
