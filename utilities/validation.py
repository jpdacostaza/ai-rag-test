"""
Input validation utilities for database operations.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, validator
import re


class DatabaseConfig(BaseModel):
    """Validation model for database configuration."""

    redis_host: str
    redis_port: int
    chroma_host: Optional[str]
    chroma_port: Optional[int]

    @validator("redis_port", "chroma_port")
    def validate_port(cls, v):
        """
        Validate that port numbers are within valid range (1-65535).
        
        Args:
            v (int, optional): The port number to validate
            
        Returns:
            int: The validated port number
            
        Raises:
            ValueError: If port number is not between 1 and 65535
        """
        if v is not None and not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v

    @validator("redis_host", "chroma_host")
    def validate_host(cls, v):
        """
        Validate host names for database connections.
        
        Args:
            v (str, optional): The hostname to validate
            
        Returns:
            str: The validated hostname
            
        Raises:
            ValueError: If hostname is not a string or has invalid format
        """
        if v is not None:
            if not isinstance(v, str):
                raise ValueError("Host must be a string")
            if v != "localhost" and not re.match(r"^[\w.-]+$", v):
                raise ValueError("Invalid host format")
        return v


class ChatMessage(BaseModel):
    """Validation model for chat messages."""

    content: str
    metadata: Dict[str, Any]
    timestamp: Optional[float]

    @validator("content")
    def validate_content(cls, v):
        """
        Validate chat message content.
        
        Args:
            v (str): The content string to validate
            
        Returns:
            str: The validated content string
            
        Raises:
            ValueError: If content is empty or exceeds 32KB size limit
        """
        if not v or len(v.strip()) == 0:
            raise ValueError("Content cannot be empty")
        if len(v) > 32768:  # 32KB limit
            raise ValueError("Content too large")
        return v

    @validator("metadata")
    def validate_metadata(cls, v):
        """
        Validate chat message metadata.
        
        Args:
            v (Dict[str, Any]): The metadata dictionary to validate
            
        Returns:
            Dict[str, Any]: The validated metadata dictionary
            
        Raises:
            ValueError: If metadata is not a dictionary or exceeds 16KB size limit
        """
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        # Check metadata size
        if len(str(v)) > 16384:  # 16KB limit
            raise ValueError("Metadata too large")
        return v


def validate_query_params(query: str, limit: Optional[int] = None, filters: Optional[Dict[str, Any]] = None) -> None:
    """Validate query parameters."""
    if not query or len(query.strip()) == 0:
        raise ValueError("Query cannot be empty")
    if len(query) > 32768:  # 32KB limit
        raise ValueError("Query too large")

    if limit is not None:
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("Limit must be a positive integer")
        if limit > 1000:
            raise ValueError("Limit too large")

    if filters is not None:
        if not isinstance(filters, dict):
            raise ValueError("Filters must be a dictionary")
        if len(str(filters)) > 16384:  # 16KB limit
            raise ValueError("Filters too large")
