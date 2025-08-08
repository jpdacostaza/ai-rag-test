"""
User Authentication and Session Management
==========================================

Handles user authentication, session validation, and user context management.
"""

import re
import uuid
from typing import Dict, Any, Optional, Tuple


class UserAuthManager:
    """Manages user authentication and session validation."""
    
    def __init__(self, debug: bool = True):
        self.debug = debug
    
    def log(self, message: str, level: str = "INFO"):
        """Log messages with consistent formatting."""
        print(f"[USER AUTH {level}] {message}")
    
    def validate_uuid(self, user_id: str) -> bool:
        """Validate UUID format or persistent session format."""
        try:
            uuid.UUID(user_id)
            return True
        except (ValueError, TypeError):
            # Accept persistent session format for zero-config setups
            if isinstance(user_id, str) and (
                user_id.startswith("persistent_user_") or 
                user_id.startswith("browser_session_") or
                user_id == "anonymous-user"
            ):
                return True
            return False
    
    def extract_user_from_body(self, body: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
        """Extract user information from request body."""
        user_data = {}
        user_id = None
        
        # Method 1: Direct __user__ object (most reliable)
        if "__user__" in body and isinstance(body["__user__"], dict):
            user_obj = body["__user__"]
            user_id = user_obj.get("id")
            user_data = user_obj
            
            if self.debug:
                self.log(f"[SEARCH] DEBUG: Received __user__ object: {user_obj}")
            
            if user_id and self.validate_uuid(user_id):
                if self.debug:
                    self.log(f"[OK] Valid UUID format: {user_id}")
                return user_id, user_data
        
        # Method 2: Direct user_id field
        user_id = body.get("user_id")
        if user_id and self.validate_uuid(user_id):
            if self.debug:
                self.log(f"[OK] Found valid user_id in body: {user_id}")
            return user_id, user_data
        
        # Method 3: Extract from messages metadata
        messages = body.get("messages", [])
        for message in messages:
            if isinstance(message, dict):
                # Check message metadata
                if "user_id" in message and self.validate_uuid(message["user_id"]):
                    user_id = message["user_id"]
                    if self.debug:
                        self.log(f"[OK] Found user_id in message metadata: {user_id}")
                    return user_id, user_data
                
                # Check for user info in content
                content = message.get("content", "")
                if isinstance(content, str):
                    uuid_match = re.search(r"user[_\s]*id[:\s]*([a-f0-9-]{36})", content, re.IGNORECASE)
                    if uuid_match:
                        extracted_id = uuid_match.group(1)
                        if self.validate_uuid(extracted_id):
                            user_id = extracted_id
                            if self.debug:
                                self.log(f"[OK] Extracted user_id from content: {user_id}")
                            return user_id, user_data
        
        # Method 4: Check top-level body fields
        for key, value in body.items():
            if isinstance(value, str) and self.validate_uuid(value):
                if "user" in key.lower():
                    user_id = value
                    if self.debug:
                        self.log(f"[OK] Found user_id in field {key}: {user_id}")
                    return user_id, user_data
        
        if self.debug:
            self.log("[FAIL] No valid user_id found in request")
        
        return None, user_data
    
    def authenticate_user(self, body: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
        """Authenticate user and extract user context."""
        user_id, user_data = self.extract_user_from_body(body)
        
        if not user_id:
            if self.debug:
                self.log("[FAIL] USER AUTHENTICATION FAILED: No valid user_id found")
            return None, {}
        
        if self.debug:
            self.log(f"[OK] USER AUTHENTICATED: {user_id}")
            if user_data:
                name = user_data.get("name", "Unknown")
                email = user_data.get("email", "Unknown")
                role = user_data.get("role", "Unknown")
                self.log(f" User Profile: {name} ({email}) - Role: {role}")
        
        return user_id, user_data
    
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
            
            # Check messages
            messages = body.get("messages", [])
            for message in messages:
                if isinstance(message, dict) and "user_id" in message:
                    found_ids.append(message["user_id"])
            
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
