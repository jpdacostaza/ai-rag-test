"""
Authentication dependencies for FastAPI endpoints
This provides API key validation as a dependency injection alternative to middleware
"""

from fastapi import HTTPException, Header, Query, Depends
from typing import Optional, Annotated
import os
from human_logging import log_api_request

def validate_api_key_func(api_key: Optional[str] = None) -> bool:
    """Validate API key - checks against environment variable or default test key"""
    if not api_key:
        return False
    
    # Get valid API keys from environment or use default test keys
    valid_keys = [
        os.getenv("API_KEY", "f2b985dd-219f-45b1-a90e-170962cc7082"),  # Test key
        "dev-api-key-12345",  # Development key
        "f2b985dd-219f-45b1-a90e-170962cc7082",  # Explicit test key
    ]
    return api_key in valid_keys

async def get_api_key_from_header_or_query(
    authorization: Annotated[Optional[str], Header()] = None,
    api_key: Annotated[Optional[str], Query()] = None
) -> str:
    """
    Dependency to extract and validate API key from Authorization header or query parameter
    """
    # Extract API key from Authorization header
    extracted_key = None
    
    if authorization and authorization.startswith("Bearer "):
        extracted_key = authorization[7:]  # Remove "Bearer " prefix
    elif api_key:
        extracted_key = api_key
      # Validate API key
    if not validate_api_key_func(extracted_key):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Unauthorized",
                "message": "Valid API key required. Use Authorization: Bearer <api_key> or ?api_key=<api_key>",
                "valid_test_key": "f2b985dd-219f-45b1-a90e-170962cc7082"
            }
        )
    
    return extracted_key or ""  # Return validated key or empty string

# Dependency for protected endpoints
RequireAuth = Depends(get_api_key_from_header_or_query)
