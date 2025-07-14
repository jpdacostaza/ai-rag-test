"""
Enhanced Memory Service - Advanced Memory Management with AI Integration
=======================================================================

This module provides an enhanced memory service with advanced features including:
- AI-powered memory categorization and tagging
- Semantic clustering and relationship mapping
- Intelligent memory lifecycle management
- Advanced retrieval with context-aware ranking
- Memory analytics and insights
- Performance optimization with intelligent caching

ENHANCED FEATURES:
- Automatic memory categorization using LLM analysis
- Semantic similarity clustering for related memories
- Memory importance scoring and lifecycle management
- Context-aware retrieval with relevance ranking
- Memory analytics for user behavior insights
- Intelligent pre-loading and caching strategies
- Memory compression and archival automation

USAGE:
    from services.memory_service_enhanced import EnhancedMemoryService
    
    # Get enhanced memory service
    memory_service = EnhancedMemoryService()
    
    # Store with automatic categorization
    await memory_service.store_enhanced_memory(
        user_id="user123",
        content="User discussed project planning strategies",
        context={"topic": "project_management", "sentiment": "positive"}
    )
    
    # Intelligent retrieval with context awareness
    memories = await memory_service.get_contextual_memories(
        user_id="user123",
        query="project planning",
        context_weights={"recency": 0.3, "relevance": 0.5, "importance": 0.2}
    )
"""

import asyncio
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional, Union, Set, Tuple
from abc import ABC, abstractmethod
import hashlib
import numpy as np
from collections import defaultdict, Counter

# Import base services
from services.memory_service import MemoryService, MemoryEntry, MemoryMetadata
from services.llm_service import LLMService
from services.vector_service import VectorService
from services.redis_service import RedisService  # Using redis service for caching
from utilities.structured_logging import get_structured_logger

logger = get_structured_logger(__name__)


class MemoryCategory(Enum):
    """Enhanced memory categories with AI-driven classification."""
    PERSONAL = "personal"          # Personal information, preferences
    TECHNICAL = "technical"        # Technical discussions, code, solutions
    PROJECT = "project"           # Project-related conversations
    LEARNING = "learning"         # Educational content, explanations
    CREATIVE = "creative"         # Creative discussions, brainstorming
    PROBLEM_SOLVING = "problem_solving"  # Problem resolution, debugging
    SOCIAL = "social"             # Social interactions, casual chat
    REFERENCE = "reference"       # Facts, documentation, references
    FEEDBACK = "feedback"         # User feedback, preferences
    CONTEXT = "context"           # Background context, settings


class MemoryImportance(Enum):
    """Memory importance levels for lifecycle management."""
    CRITICAL = 5      # Never archive, always accessible
    HIGH = 4         # Long retention, prioritized retrieval
    MEDIUM = 3       # Standard retention, normal retrieval
    LOW = 2          # Short retention, deprioritized
    ARCHIVE = 1      # Archived, accessible but not actively retrieved


@dataclass
class EnhancedMemory:
    """Enhanced memory structure with advanced metadata."""
    id: str
    user_id: str
    content: str
    timestamp: datetime
    category: MemoryCategory
    importance: MemoryImportance
    tags: Set[str] = field(default_factory=set)
    embedding: Optional[List[float]] = None
    related_memory_ids: Set[str] = field(default_factory=set)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    sentiment_score: Optional[float] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 1.0
    compression_ratio: Optional[float] = None
    original_size: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "importance": self.importance.value,
            "tags": list(self.tags),
            "embedding": self.embedding,
            "related_memory_ids": list(self.related_memory_ids),
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "sentiment_score": self.sentiment_score,
            "context_data": self.context_data,
            "confidence_score": self.confidence_score,
            "compression_ratio": self.compression_ratio,
            "original_size": self.original_size
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnhancedMemory":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            category=MemoryCategory(data["category"]),
            importance=MemoryImportance(data["importance"]),
            tags=set(data.get("tags", [])),
            embedding=data.get("embedding"),
            related_memory_ids=set(data.get("related_memory_ids", [])),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None,
            sentiment_score=data.get("sentiment_score"),
            context_data=data.get("context_data", {}),
            confidence_score=data.get("confidence_score", 1.0),
            compression_ratio=data.get("compression_ratio"),
            original_size=data.get("original_size", 0)
        )


@dataclass
class MemoryCluster:
    """Represents a cluster of related memories."""
    id: str
    name: str
    description: str
    memory_ids: Set[str]
    centroid_embedding: List[float]
    coherence_score: float
    last_updated: datetime
    category: MemoryCategory
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "memory_ids": list(self.memory_ids),
            "centroid_embedding": self.centroid_embedding,
            "coherence_score": self.coherence_score,
            "last_updated": self.last_updated.isoformat(),
            "category": self.category.value
        }


@dataclass
class MemoryAnalytics:
    """Memory analytics and insights."""
    user_id: str
    total_memories: int
    category_distribution: Dict[MemoryCategory, int]
    importance_distribution: Dict[MemoryImportance, int]
    average_access_frequency: float
    most_accessed_categories: List[MemoryCategory]
    memory_growth_trend: List[Tuple[datetime, int]]
    cluster_count: int
    average_cluster_size: float
    generated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "total_memories": self.total_memories,
            "category_distribution": {cat.value: count for cat, count in self.category_distribution.items()},
            "importance_distribution": {imp.value: count for imp, count in self.importance_distribution.items()},
            "average_access_frequency": self.average_access_frequency,
            "most_accessed_categories": [cat.value for cat in self.most_accessed_categories],
            "memory_growth_trend": [(dt.isoformat(), count) for dt, count in self.memory_growth_trend],
            "cluster_count": self.cluster_count,
            "average_cluster_size": self.average_cluster_size,
            "generated_at": self.generated_at.isoformat()
        }


class EnhancedMemoryService:
    """Enhanced memory service with AI-powered features."""
    
    def __init__(
        self,
        base_memory_service: MemoryService,
        llm_service: LLMService,
        vector_service: VectorService,
        redis_service: RedisService  # Using redis service for caching
    ):
        self.base_memory_service = base_memory_service
        self.llm_service = llm_service
        self.vector_service = vector_service
        self.redis_service = redis_service  # Using redis service for caching
        self.logger = get_structured_logger(__name__)
        
        # Configuration
        self.clustering_threshold = 0.75
        self.max_cluster_size = 50
        self.importance_decay_days = 30
        self.archive_threshold_days = 90
        
    async def store_enhanced_memory(
        self,
        user_id: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> EnhancedMemory:
        """Store memory with enhanced AI analysis."""
        try:
            # Generate unique ID
            memory_id = hashlib.md5(f"{user_id}_{content}_{datetime.now().isoformat()}".encode()).hexdigest()
            
            # AI-powered categorization and analysis
            analysis_tasks = await asyncio.gather(
                self._categorize_memory(content, context),
                self._analyze_sentiment(content),
                self._extract_tags(content),
                self._calculate_importance(content, context),
                return_exceptions=True
            )
            
            category = analysis_tasks[0] if not isinstance(analysis_tasks[0], Exception) else MemoryCategory.CONTEXT
            sentiment = analysis_tasks[1] if not isinstance(analysis_tasks[1], Exception) else 0.0
            tags = analysis_tasks[2] if not isinstance(analysis_tasks[2], Exception) else set()
            importance = analysis_tasks[3] if not isinstance(analysis_tasks[3], Exception) else MemoryImportance.MEDIUM
            
            # Generate embedding for similarity search
            embedding = await self.vector_service.get_embedding(content)
            
            # Create enhanced memory
            enhanced_memory = EnhancedMemory(
                id=memory_id,
                user_id=user_id,
                content=content,
                timestamp=datetime.now(),
                category=category,
                importance=importance,
                tags=tags,
                embedding=embedding,
                sentiment_score=sentiment,
                context_data=context or {},
                original_size=len(content.encode('utf-8'))
            )
            
            # Store in base memory service
            base_memory_entry = MemoryEntry(
                content=content,
                metadata=MemoryMetadata(
                    user_id=user_id,
                    timestamp=enhanced_memory.timestamp,
                    source="enhanced_memory",
                    importance=enhanced_memory.importance.value,
                    memory_type="enhanced",
                    context=enhanced_memory.context_data,
                    conversation_id=None,
                    explicit=True
                )
            )
            
            await self.base_memory_service.store_memory(base_memory_entry)
            
            # Update clusters asynchronously
            asyncio.create_task(self._update_memory_clusters(user_id, enhanced_memory))
            
            # Cache for quick access
            await self.redis_service.setex(
                f"enhanced_memory:{memory_id}",
                3600,  # 1 hour TTL
                json.dumps(enhanced_memory.to_dict())
            )
            
            self.logger.info(
                "Enhanced memory stored",
                extra={
                    "memory_id": memory_id,
                    "user_id": user_id,
                    "category": category.value,
                    "importance": importance.value,
                    "tags_count": len(tags)
                }
            )
            
            return enhanced_memory
            
        except Exception as e:
            self.logger.error(f"Failed to store enhanced memory: {e}")
            raise
    
    async def get_contextual_memories(
        self,
        user_id: str,
        query: str,
        context_weights: Optional[Dict[str, float]] = None,
        limit: int = 10,
        categories: Optional[List[MemoryCategory]] = None
    ) -> List[EnhancedMemory]:
        """Retrieve memories with context-aware ranking."""
        try:
            # Default context weights
            if context_weights is None:
                context_weights = {
                    "recency": 0.2,
                    "relevance": 0.4,
                    "importance": 0.2,
                    "access_frequency": 0.1,
                    "sentiment": 0.1
                }
            
            # Get base memories
            base_memories = await self.base_memory_service.get_memories(
                user_id=user_id,
                query=query,
                limit=limit * 3  # Get more for filtering
            )
            
            if not base_memories:
                return []
            
            # Convert to enhanced memories
            enhanced_memories = []
            for base_memory in base_memories:
                if hasattr(base_memory, 'metadata') and base_memory.metadata:
                    try:
                        enhanced_memory = EnhancedMemory.from_dict(base_memory.metadata)
                        enhanced_memories.append(enhanced_memory)
                    except Exception as e:
                        self.logger.warning(f"Failed to convert memory to enhanced: {e}")
                        continue
            
            # Filter by categories if specified
            if categories:
                enhanced_memories = [
                    mem for mem in enhanced_memories 
                    if mem.category in categories
                ]
            
            # Generate query embedding for relevance scoring
            query_embedding = await self.vector_service.get_embedding(query)
            
            # Score and rank memories
            scored_memories = []
            for memory in enhanced_memories:
                score = await self._calculate_contextual_score(
                    memory, query_embedding, context_weights
                )
                scored_memories.append((memory, score))
            
            # Sort by score and return top results
            scored_memories.sort(key=lambda x: x[1], reverse=True)
            
            # Update access tracking
            result_memories = [mem for mem, _ in scored_memories[:limit]]
            await self._update_access_tracking(result_memories)
            
            self.logger.info(
                "Retrieved contextual memories",
                extra={
                    "user_id": user_id,
                    "query": query,
                    "returned_count": len(result_memories),
                    "total_scored": len(scored_memories)
                }
            )
            
            return result_memories
            
        except Exception as e:
            self.logger.error(f"Failed to get contextual memories: {e}")
            return []
    
    async def get_memory_analytics(self, user_id: str) -> MemoryAnalytics:
        """Generate comprehensive memory analytics."""
        try:
            # Get all user memories
            all_memories = await self.base_memory_service.get_memories(
                user_id=user_id,
                limit=1000  # Large limit for analytics
            )
            
            if not all_memories:
                return MemoryAnalytics(
                    user_id=user_id,
                    total_memories=0,
                    category_distribution={},
                    importance_distribution={},
                    average_access_frequency=0.0,
                    most_accessed_categories=[],
                    memory_growth_trend=[],
                    cluster_count=0,
                    average_cluster_size=0.0,
                    generated_at=datetime.now()
                )
            
            # Convert to enhanced memories
            enhanced_memories = []
            for base_memory in all_memories:
                if hasattr(base_memory, 'metadata') and base_memory.metadata:
                    try:
                        enhanced_memory = EnhancedMemory.from_dict(base_memory.metadata)
                        enhanced_memories.append(enhanced_memory)
                    except Exception:
                        continue
            
            # Calculate distributions
            category_dist = Counter(mem.category for mem in enhanced_memories)
            importance_dist = Counter(mem.importance for mem in enhanced_memories)
            
            # Calculate access frequency
            total_access = sum(mem.access_count for mem in enhanced_memories)
            avg_access_freq = total_access / len(enhanced_memories) if enhanced_memories else 0
            
            # Most accessed categories
            category_access = defaultdict(int)
            for mem in enhanced_memories:
                category_access[mem.category] += mem.access_count
            
            most_accessed = sorted(
                category_access.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Memory growth trend (last 30 days)
            growth_trend = []
            for i in range(30):
                date = datetime.now() - timedelta(days=i)
                count = len([
                    mem for mem in enhanced_memories
                    if mem.timestamp.date() == date.date()
                ])
                growth_trend.append((date, count))
            
            # Get cluster information
            clusters = await self._get_user_clusters(user_id)
            cluster_count = len(clusters)
            avg_cluster_size = (
                sum(len(cluster.memory_ids) for cluster in clusters) / cluster_count
                if cluster_count > 0 else 0.0
            )
            
            analytics = MemoryAnalytics(
                user_id=user_id,
                total_memories=len(enhanced_memories),
                category_distribution=dict(category_dist),
                importance_distribution=dict(importance_dist),
                average_access_frequency=avg_access_freq,
                most_accessed_categories=[cat for cat, _ in most_accessed],
                memory_growth_trend=growth_trend,
                cluster_count=cluster_count,
                average_cluster_size=avg_cluster_size,
                generated_at=datetime.now()
            )
            
            # Cache analytics
            await self.redis_service.setex(
                f"memory_analytics:{user_id}",
                3600,  # 1 hour TTL
                json.dumps(analytics.to_dict())
            )
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to generate memory analytics: {e}")
            raise
    
    async def optimize_memory_storage(self, user_id: str) -> Dict[str, Any]:
        """Optimize memory storage through compression and archival."""
        try:
            # Get user memories
            all_memories = await self.base_memory_service.get_memories(
                user_id=user_id,
                limit=1000
            )
            
            optimization_stats = {
                "processed_memories": 0,
                "archived_memories": 0,
                "compressed_memories": 0,
                "space_saved_bytes": 0,
                "clusters_updated": 0
            }
            
            for base_memory in all_memories:
                if not (hasattr(base_memory, 'metadata') and base_memory.metadata):
                    continue
                
                try:
                    enhanced_memory = EnhancedMemory.from_dict(base_memory.metadata)
                    optimization_stats["processed_memories"] += 1
                    
                    # Check for archival (old, low importance, rarely accessed)
                    days_old = (datetime.now() - enhanced_memory.timestamp).days
                    if (days_old > self.archive_threshold_days and 
                        enhanced_memory.importance == MemoryImportance.LOW and
                        enhanced_memory.access_count < 2):
                        
                        enhanced_memory.importance = MemoryImportance.ARCHIVE
                        optimization_stats["archived_memories"] += 1
                    
                    # Compress large, infrequently accessed memories
                    if (len(enhanced_memory.content) > 1000 and
                        enhanced_memory.access_count < 5 and
                        enhanced_memory.compression_ratio is None):
                        
                        compressed_content = await self._compress_memory_content(enhanced_memory.content)
                        if len(compressed_content) < len(enhanced_memory.content):
                            space_saved = len(enhanced_memory.content) - len(compressed_content)
                            enhanced_memory.compression_ratio = len(compressed_content) / len(enhanced_memory.content)
                            optimization_stats["compressed_memories"] += 1
                            optimization_stats["space_saved_bytes"] += space_saved
                    
                    # Update memory
                    updated_memory_entry = MemoryEntry(
                        content=base_memory.content,
                        metadata=MemoryMetadata(
                            user_id=base_memory.user_id,
                            timestamp=base_memory.timestamp,
                            source="enhanced_memory_optimized",
                            importance=enhanced_memory.importance.value,
                            memory_type="enhanced",
                            context=enhanced_memory.context_data,
                            conversation_id=None,
                            explicit=True
                        )
                    )
                    
                    await self.base_memory_service.store_memory(updated_memory_entry)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to optimize memory {base_memory.id}: {e}")
                    continue
            
            # Update clusters
            await self._rebuild_user_clusters(user_id)
            optimization_stats["clusters_updated"] = 1
            
            self.logger.info(
                "Memory optimization completed",
                extra={
                    "user_id": user_id,
                    **optimization_stats
                }
            )
            
            return optimization_stats
            
        except Exception as e:
            self.logger.error(f"Failed to optimize memory storage: {e}")
            raise
    
    # Private helper methods
    
    async def _categorize_memory(self, content: str, context: Optional[Dict[str, Any]]) -> MemoryCategory:
        """Use LLM to categorize memory content."""
        try:
            prompt = f"""
            Analyze the following content and categorize it into one of these categories:
            - personal: Personal information, preferences, user details
            - technical: Technical discussions, code, programming solutions
            - project: Project-related conversations, planning, management
            - learning: Educational content, explanations, tutorials
            - creative: Creative discussions, brainstorming, ideas
            - problem_solving: Problem resolution, debugging, troubleshooting
            - social: Social interactions, casual chat, greetings
            - reference: Facts, documentation, references, definitions
            - feedback: User feedback, preferences, evaluations
            - context: Background context, settings, configuration
            
            Content: {content[:500]}...
            
            Context: {json.dumps(context) if context else 'None'}
            
            Respond with only the category name (lowercase).
            """
            
            response = await self.llm_service.call_llm([{"role": "user", "content": prompt}])
            category_name = response.strip().lower()
            
            # Map to enum
            for category in MemoryCategory:
                if category.value == category_name:
                    return category
            
            return MemoryCategory.CONTEXT  # Default fallback
            
        except Exception as e:
            self.logger.warning(f"Failed to categorize memory: {e}")
            return MemoryCategory.CONTEXT
    
    async def _analyze_sentiment(self, content: str) -> float:
        """Analyze sentiment of memory content."""
        try:
            prompt = f"""
            Analyze the sentiment of the following content on a scale from -1.0 (very negative) to 1.0 (very positive).
            Return only a number between -1.0 and 1.0.
            
            Content: {content[:500]}...
            """
            
            response = await self.llm_service.call_llm([{"role": "user", "content": prompt}])
            
            try:
                sentiment = float(response.strip())
                return max(-1.0, min(1.0, sentiment))  # Clamp to valid range
            except ValueError:
                return 0.0  # Neutral if parsing fails
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze sentiment: {e}")
            return 0.0
    
    async def _extract_tags(self, content: str) -> Set[str]:
        """Extract relevant tags from memory content."""
        try:
            prompt = f"""
            Extract 3-5 relevant tags from the following content. 
            Tags should be single words or short phrases that capture key concepts.
            Return tags separated by commas.
            
            Content: {content[:500]}...
            """
            
            response = await self.llm_service.call_llm([{"role": "user", "content": prompt}])
            
            tags = set()
            for tag in response.split(','):
                tag = tag.strip().lower()
                if tag and len(tag) > 1:
                    tags.add(tag)
            
            return tags
            
        except Exception as e:
            self.logger.warning(f"Failed to extract tags: {e}")
            return set()
    
    async def _calculate_importance(self, content: str, context: Optional[Dict[str, Any]]) -> MemoryImportance:
        """Calculate memory importance based on content and context."""
        try:
            # Check for importance indicators
            importance_keywords = {
                MemoryImportance.CRITICAL: ['critical', 'urgent', 'important', 'remember', 'never forget'],
                MemoryImportance.HIGH: ['significant', 'key', 'main', 'primary', 'essential'],
                MemoryImportance.LOW: ['casual', 'minor', 'just', 'maybe', 'perhaps']
            }
            
            content_lower = content.lower()
            
            # Check for explicit importance indicators
            for importance, keywords in importance_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    return importance
            
            # Consider content length and structure
            if len(content) > 500:  # Longer content often more important
                return MemoryImportance.HIGH
            elif len(content) < 50:  # Very short content less important
                return MemoryImportance.LOW
            
            # Check context for importance indicators
            if context:
                if context.get('user_flagged_important'):
                    return MemoryImportance.CRITICAL
                if context.get('topic') in ['project', 'work', 'deadline']:
                    return MemoryImportance.HIGH
            
            return MemoryImportance.MEDIUM  # Default
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate importance: {e}")
            return MemoryImportance.MEDIUM
    
    async def _calculate_contextual_score(
        self,
        memory: EnhancedMemory,
        query_embedding: List[float],
        context_weights: Dict[str, float]
    ) -> float:
        """Calculate contextual relevance score for memory."""
        try:
            score = 0.0
            
            # Relevance score (cosine similarity)
            if memory.embedding and query_embedding:
                similarity = self._cosine_similarity(memory.embedding, query_embedding)
                score += context_weights.get('relevance', 0.4) * similarity
            
            # Recency score
            days_old = (datetime.now() - memory.timestamp).days
            recency_score = max(0, 1 - (days_old / 365))  # Decay over a year
            score += context_weights.get('recency', 0.2) * recency_score
            
            # Importance score
            importance_score = memory.importance.value / 5.0  # Normalize to 0-1
            score += context_weights.get('importance', 0.2) * importance_score
            
            # Access frequency score
            access_score = min(1.0, memory.access_count / 10.0)  # Cap at 10 accesses
            score += context_weights.get('access_frequency', 0.1) * access_score
            
            # Sentiment score (positive sentiment slightly preferred)
            if memory.sentiment_score is not None:
                sentiment_score = (memory.sentiment_score + 1) / 2  # Normalize to 0-1
                score += context_weights.get('sentiment', 0.1) * sentiment_score
            
            return score
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate contextual score: {e}")
            return 0.0
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            # Convert to numpy arrays for calculation
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
            
        except Exception:
            return 0.0
    
    async def _update_access_tracking(self, memories: List[EnhancedMemory]) -> None:
        """Update access tracking for memories."""
        try:
            for memory in memories:
                memory.access_count += 1
                memory.last_accessed = datetime.now()
                
                # Update in storage
                updated_memory_entry = MemoryEntry(
                    content=memory.content,
                    metadata=MemoryMetadata(
                        user_id=memory.user_id,
                        timestamp=memory.timestamp,
                        source="access_tracking",
                        importance=memory.importance.value,
                        memory_type="enhanced",
                        context=memory.context_data,
                        conversation_id=None,
                        explicit=True
                    )
                )
                
                await self.base_memory_service.store_memory(updated_memory_entry)
                
        except Exception as e:
            self.logger.warning(f"Failed to update access tracking: {e}")
    
    async def _update_memory_clusters(self, user_id: str, new_memory: EnhancedMemory) -> None:
        """Update memory clusters with new memory."""
        # This would implement clustering logic - simplified for now
        pass
    
    async def _get_user_clusters(self, user_id: str) -> List[MemoryCluster]:
        """Get memory clusters for user."""
        # This would retrieve clusters from storage - simplified for now
        return []
    
    async def _rebuild_user_clusters(self, user_id: str) -> None:
        """Rebuild memory clusters for user."""
        # This would implement full clustering rebuild - simplified for now
        pass
    
    async def _compress_memory_content(self, content: str) -> str:
        """Compress memory content while preserving key information."""
        try:
            prompt = f"""
            Compress the following content to about 70% of its original length while preserving all key information and context.
            Maintain the essential meaning and important details.
            
            Original content: {content}
            """
            
            compressed = await self.llm_service.call_llm([{"role": "user", "content": prompt}])
            
            # Only return if actually shorter
            if len(compressed) < len(content):
                return compressed
            else:
                return content
                
        except Exception as e:
            self.logger.warning(f"Failed to compress memory content: {e}")
            return content


# Dependency injection function
async def get_enhanced_memory_service() -> EnhancedMemoryService:
    """Get enhanced memory service instance."""
    from services.dependencies import (
        get_memory_service,
        get_llm_service, 
        get_vector_service,
        get_redis_service
    )
    
    base_memory_service = await get_memory_service()
    llm_service = await get_llm_service()
    vector_service = await get_vector_service()
    redis_service = await get_redis_service()  # Using redis service for caching
    
    return EnhancedMemoryService(
        base_memory_service=base_memory_service,
        llm_service=llm_service,
        vector_service=vector_service,
        redis_service=redis_service
    )
