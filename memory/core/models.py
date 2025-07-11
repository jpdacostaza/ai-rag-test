"""
Memory Data Models
==================

Pydantic models for memory operations.
"""

import os
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class MemoryConfig(BaseModel):
    """Configuration for memory operations."""
    
    # API Configuration
    api_url: str = "http://memory_api:8080"
    timeout: float = 10.0
    
    # Memory Settings
    max_memories: int = 5
    relevance_threshold: float = float(os.getenv('MEMORY_RETRIEVAL_THRESHOLD', '0.001'))
    
    # Learning Settings
    auto_store_enabled: bool = True
    auto_store_threshold: int = 3
    
    # Debug
    debug_enabled: bool = False


class MemoryQuery(BaseModel):
    """Query for retrieving memories."""
    
    user_id: str = Field(..., description="User identifier")
    query_text: str = Field(..., description="Query text for similarity search")
    limit: int = Field(default=5, description="Maximum number of memories to retrieve")
    threshold: float = Field(default=float(os.getenv('MEMORY_RETRIEVAL_THRESHOLD', '0.001')), description="Minimum relevance threshold")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")


class MemoryRecord(BaseModel):
    """Represents a memory record."""
    
    id: Optional[str] = None
    user_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    relevance_score: Optional[float] = None
    timestamp: Optional[datetime] = None
    source: str = "system"


class MemoryResponse(BaseModel):
    """Response from memory operations."""
    
    success: bool
    memories: List[MemoryRecord] = []
    total_count: int = 0
    message: Optional[str] = None
    error: Optional[str] = None


class LearningInteraction(BaseModel):
    """Represents a learning interaction to be stored."""
    
    user_id: str
    conversation_id: str
    user_message: str
    assistant_response: str
    timestamp: float
    source: str = "openwebui"
    metadata: Optional[Dict[str, Any]] = None
