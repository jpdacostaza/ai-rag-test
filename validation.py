"""
Input validation utilities for the FastAPI application.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, validator, Field
from fastapi import HTTPException
import re
import bleach

class ValidationError(Exception):
    """Custom validation error."""
    pass

class SecureInput(BaseModel):
    """Base model for secure input validation."""
    
    @validator('*', pre=True)
    def sanitize_strings(cls, v):
        """Sanitize string inputs to prevent XSS."""
        if isinstance(v, str):
            # Basic XSS prevention
            v = bleach.clean(v, tags=[], attributes={}, strip=True)
            # Prevent common injection patterns
            dangerous_patterns = [
                r'<script.*?>.*?</script>',
                r'javascript:',
                r'on\w+\s*=',
                r'data:text/html',
            ]
            for pattern in dangerous_patterns:
                v = re.sub(pattern, '', v, flags=re.IGNORECASE)
        return v

class ChatValidation(SecureInput):
    """Validation for chat requests."""
    message: str = Field(..., min_length=1, max_length=10000)
    user_id: Optional[str] = Field(None, max_length=100)
    conversation_id: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()
    
    @validator('user_id', 'conversation_id', 'model')
    def validate_ids(cls, v):
        if v is not None:
            # Allow only alphanumeric, hyphens, and underscores
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('IDs can only contain alphanumeric characters, hyphens, and underscores')
        return v

class DocumentValidation(SecureInput):
    """Validation for document uploads."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=1000000)  # 1MB limit
    user_id: str = Field(..., max_length=100)
    tags: Optional[List[str]] = Field(None, description="List of tags for the document")
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            # Limit to 10 tags maximum
            if len(v) > 10:
                raise ValueError("Maximum 10 tags allowed")
            # Validate each tag
            for tag in v:
                if not isinstance(tag, str) or len(tag) > 50:
                    raise ValueError('Each tag must be a string with max 50 characters')
                if not re.match(r'^[a-zA-Z0-9_-]+$', tag):
                    raise ValueError('Tags can only contain alphanumeric characters, hyphens, and underscores')
        return v

class SearchValidation(SecureInput):
    """Validation for search requests."""
    query: str = Field(..., min_length=1, max_length=500)
    user_id: str = Field(..., max_length=100)
    limit: Optional[int] = Field(10, ge=1, le=100)
    offset: Optional[int] = Field(0, ge=0)
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty or whitespace')
        return v.strip()

class ModelValidation(SecureInput):
    """Validation for model requests."""
    model_name: str = Field(..., min_length=1, max_length=100)
    
    @validator('model_name')
    def validate_model_name(cls, v):
        # Allow only safe model name patterns
        if not re.match(r'^[a-zA-Z0-9._:-]+$', v):
            raise ValueError('Model name contains invalid characters')
        return v

def validate_file_upload(filename: str, content_type: str, file_size: int) -> None:
    """Validate file upload parameters."""
    max_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_size:
        raise ValidationError(f'File size exceeds maximum limit of {max_size} bytes')

    allowed_extensions = {'.pdf', '.txt', '.docx', '.md', '.json'}
    file_ext = f".{filename.rsplit('.', 1)[-1].lower()}" if '.' in filename else ''
    if file_size == 0:
        raise ValidationError('File cannot be empty')
    if file_ext not in allowed_extensions:
        raise ValidationError(f'File extension {file_ext} is not allowed')

    allowed_content_types = {
        'application/pdf',
        'text/plain',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/markdown',
        'application/json'
    }
    if content_type not in allowed_content_types:
        raise ValidationError(f'Content type {content_type} is not allowed')

def validate_api_key(api_key: str) -> bool:
    """Validate API key format."""
    if not api_key:
        return False
    
    # Basic API key validation (adjust as needed)
    if len(api_key) < 10 or len(api_key) > 200:
        return False
    
    # Check for basic structure (adjust pattern as needed)
    if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
        return False
    
    return True

def sanitize_output(data: Any) -> Any:
    """Sanitize output data to prevent information leakage."""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Hide sensitive keys
            if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                sanitized[key] = '***'
            else:
                sanitized[key] = sanitize_output(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_output(item) for item in data]
    elif isinstance(data, str):
        # Basic output sanitization
        return bleach.clean(data, tags=[], attributes={}, strip=True)
    else:
        return data

# Rate limiting helpers
def check_rate_limit(user_id: str, endpoint: str, limit: int = 100) -> bool:
    """Check if user has exceeded rate limit for endpoint."""
    # This is a placeholder - implement with Redis or similar
    # For now, always return True (not rate limited)
    return True

def log_security_event(event_type: str, details: str, user_id: Optional[str] = None):
    """Log security-related events."""
    from human_logging import log_service_status
    log_service_status("SECURITY", "warning", f"{event_type}: {details} (user: {user_id})")
