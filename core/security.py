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
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
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
