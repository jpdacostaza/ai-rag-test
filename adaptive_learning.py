"""
Adaptive Learning System for LLM Backend
========================================

This module implements self-learning capabilities including:
- Conversation quality feedback loops
- Automatic knowledge base expansion
- User interaction pattern learning
- Contextual response improvement
- Automated content ingestion from interactions
"""

import asyncio
from collections import defaultdict
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from database import db_manager
from database import get_embedding
from database import index_document_chunks
from database import retrieve_user_memory
from error_handler import MemoryErrorHandler
from human_logging import log_service_status


class FeedbackType(Enum):
    """Types of feedback for learning system."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    CORRECTION = "correction"
    CLARIFICATION = "clarification"


@dataclass
class InteractionMetrics:
    """Metrics for tracking interaction quality."""

    user_id: str
    conversation_id: str
    timestamp: datetime
    response_time: float
    user_satisfaction: Optional[float] = None
    feedback_type: Optional[FeedbackType] = None
    topics: Optional[List[str]] = None
    tools_used: Optional[List[str]] = None
    context_relevance_score: float = 0.0
    follow_up_questions: int = 0
    resolution_achieved: bool = False


@dataclass
class LearningPattern:
    """Represents a learned pattern from user interactions."""

    pattern_id: str
    user_id: str
    pattern_type: str  # "query_pattern", "context_preference", "tool_preference"
    pattern_data: Dict[str, Any]
    confidence: float
    usage_count: int
    last_updated: datetime


class ConversationAnalyzer:
    """Analyzes conversations to extract learning patterns."""

    def __init__(self):
        self.sentiment_keywords = {
            "positive": [
                "good",
                "great",
                "perfect",
                "thanks",
                "helpful",
                "correct",
                "exactly",
                "excellent",
                "amazing",
                "thank you",
            ],
            "negative": [
                "wrong",
                "incorrect",
                "bad",
                "unhelpful",
                "unclear",
                "confused",
                "useless",
                "terrible",
                "awful",
            ],
            "correction": [
                "actually",
                "no",
                "but",
                "however",
                "should be",
                "meant to",
                "that's wrong",
                "not right",
            ],
            "clarification": [
                "what do you mean",
                "can you explain",
                "i don't understand",
                "please clarify",
                "more details",
                "confused about",
            ],
        }

    async def analyze_interaction(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
        response_time: float,
        tools_used: Optional[List[str]],
    ) -> Optional[InteractionMetrics]:
        """Analyze a single interaction for learning opportunities."""
        try:
            # Extract topics using simple keyword analysis
            topics = await self._extract_topics(user_message + " " + assistant_response)

            # Determine feedback type from user message
            feedback_type = self._classify_feedback(user_message)

            # Calculate context relevance score
            context_score = await self._calculate_context_relevance(
                user_id, user_message, assistant_response
            )

            # Check for follow-up questions
            follow_ups = self._count_follow_up_indicators(user_message)

            metrics = InteractionMetrics(
                user_id=user_id,
                conversation_id=conversation_id,
                timestamp=datetime.now(),
                response_time=response_time,
                feedback_type=feedback_type,
                topics=topics,
                tools_used=tools_used,
                context_relevance_score=context_score,
                follow_up_questions=follow_ups,
            )

            return metrics

        except Exception:
            log_service_status("LEARNING", "error", "Interaction analysis failed: {e}")
            return None

    def _classify_feedback(self, message: str) -> FeedbackType:
        """Classify user message for feedback type."""
        message_lower = message.lower()

        scores = {feedback_type: 0 for feedback_type in FeedbackType}

        # Check for multi-word phrases first (more specific)
        for feedback_type, keywords in self.sentiment_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    # Give higher weight to longer, more specific phrases
                    weight = len(keyword.split())
                    scores[FeedbackType(feedback_type)] += weight

        # Prioritize feedback types by strength of signal
        if scores[FeedbackType.CORRECTION] > 0:
            return FeedbackType.CORRECTION
        elif (
            scores[FeedbackType.POSITIVE] > scores[FeedbackType.NEGATIVE]
            and scores[FeedbackType.POSITIVE] > scores[FeedbackType.CLARIFICATION]
        ):
            return FeedbackType.POSITIVE
        elif (
            scores[FeedbackType.NEGATIVE] > scores[FeedbackType.POSITIVE]
            and scores[FeedbackType.NEGATIVE] > scores[FeedbackType.CLARIFICATION]
        ):
            return FeedbackType.NEGATIVE
        elif scores[FeedbackType.CLARIFICATION] > 0:
            return FeedbackType.CLARIFICATION
        else:
            return FeedbackType.NEUTRAL

    async def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from conversation text."""
        # Simple topic extraction - can be enhanced with NLP models
        common_topics = [
            "programming",
            "python",
            "javascript",
            "web development",
            "AI",
            "machine learning",
            "data science",
            "databases",
            "API",
            "deployment",
            "debugging",
            "testing",
            "weather",
            "news",
            "calculations",
            "research",
            "writing",
            "analysis",
        ]

        text_lower = text.lower()
        found_topics = [topic for topic in common_topics if topic in text_lower]
        return found_topics[:5]  # Limit to top 5 topics

    async def _calculate_context_relevance(self, user_id: str, query: str, response: str) -> float:
        """Calculate how relevant the response is to user's context."""
        try:
            # Get user's recent memory
            query_embedding = get_embedding(db_manager, query)
            if query_embedding is None or (
                hasattr(query_embedding, "size") and query_embedding.size == 0
            ):
                return 0.5  # Neutral score if can't get embedding

            recent_memories = retrieve_user_memory(
                db_manager, user_id, query_embedding, n_results=3
            )

            if not recent_memories:
                return 0.5  # No context available

            # Simple relevance calculation based on keyword overlap
            # In production, use semantic similarity
            query_words = set(query.lower().split())
            response_words = set(response.lower().split())
            memory_words = set()

            for memory in recent_memories:
                if isinstance(memory, dict) and "text" in memory:
                    memory_words.update(memory["text"].lower().split())
                elif isinstance(memory, str):
                    memory_words.update(memory.lower().split())

            if not memory_words:
                return 0.5

            # Calculate overlap scores safely
            query_memory_overlap = len(query_words & memory_words) / max(len(query_words), 1)
            response_memory_overlap = len(response_words & memory_words) / max(
                len(response_words), 1
            )

            return min((query_memory_overlap + response_memory_overlap) / 2, 1.0)

        except Exception:
            log_service_status("LEARNING", "error", "Context relevance calculation failed: {e}")
            return 0.5

    def _count_follow_up_indicators(self, message: str) -> int:
        """Count indicators that suggest need for follow-up."""
        follow_up_indicators = [
            "?",
            "how",
            "what",
            "why",
            "when",
            "where",
            "can you",
            "please explain",
        ]
        message_lower = message.lower()
        return sum(1 for indicator in follow_up_indicators if indicator in message_lower)


class AdaptiveLearningSystem:
    """Main adaptive learning system that coordinates all learning components."""

    def __init__(self):
        self.analyzer = ConversationAnalyzer()
        self.user_patterns: Dict[str, Dict] = defaultdict(dict)
        self.global_patterns: Dict[str, Any] = {}
        self.learning_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.knowledge_expansion_queue: deque = deque(maxlen=100)

    async def process_interaction(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
        response_time: float,
        tools_used: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Process an interaction for learning opportunities."""
        try:
            tools_used = tools_used or []

            # Analyze the interaction
            metrics = await self.analyzer.analyze_interaction(
                user_id,
                conversation_id,
                user_message,
                assistant_response,
                response_time,
                tools_used,
            )

            if not metrics:
                return {"status": "failed", "reason": "Analysis failed"}

            # Store metrics for trend analysis
            self.learning_metrics[user_id].append(metrics)

            # Extract and update learning patterns
            await self._update_learning_patterns(user_id, metrics)

            # Check for knowledge expansion opportunities
            await self._check_knowledge_expansion(
                user_id, metrics, user_message, assistant_response
            )

            # Update user preference models
            await self._update_user_preferences(user_id, metrics)

            log_service_status(
                "LEARNING",
                "ready",
                f"Processed interaction for {user_id}: {
                    metrics.feedback_type.value if metrics.feedback_type else 'neutral'}",
            )

            return {
                "status": "success",
                "feedback_type": metrics.feedback_type.value if metrics.feedback_type else None,
                "context_relevance": metrics.context_relevance_score,
                "topics": metrics.topics,
                "learning_applied": True,
            }

        except Exception as e:
            MemoryErrorHandler.handle_memory_error(e, "adaptive_learning", user_id)
            return {"status": "error", "reason": str(e)}

    async def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get learning insights for a specific user."""
        try:
            if user_id not in self.user_patterns:
                return {"status": "no_data", "message": "No learning data available for user"}

            user_data = self.user_patterns[user_id]
            # Last 10 interactions
            recent_metrics = list(self.learning_metrics[user_id])[-10:]

            # Calculate trends
            if recent_metrics:
                avg_context_score = sum(m.context_relevance_score for m in recent_metrics) / len(
                    recent_metrics
                )
                feedback_distribution = defaultdict(int)
                for m in recent_metrics:
                    if m.feedback_type:
                        feedback_distribution[m.feedback_type.value] += 1
            else:
                avg_context_score = 0
                feedback_distribution = {}

            return {
                "status": "success",
                "user_id": user_id,
                "insights": {
                    "top_topics": dict(
                        sorted(
                            user_data.get("topic_preferences", {}).items(),
                            key=lambda x: x[1],
                            reverse=True,
                        )[:5]
                    ),
                    "preferred_tools": dict(
                        sorted(
                            user_data.get("tool_preferences", {}).items(),
                            key=lambda x: x[1],
                            reverse=True,
                        )[:5]
                    ),
                    "avg_context_relevance": round(avg_context_score, 2),
                    "feedback_distribution": dict(feedback_distribution),
                    "total_interactions": len(recent_metrics),
                    "preferences": user_data.get("preferences", {}),
                    "learning_trend": "improving" if avg_context_score > 0.6 else "stable",
                },
            }

        except Exception as e:
            return {"status": "error", "reason": str(e)}

    async def _update_learning_patterns(self, user_id: str, metrics: InteractionMetrics):
        """Update learning patterns based on interaction metrics."""
        try:
            if not self.user_patterns[user_id]:
                self.user_patterns[user_id] = {
                    "query_patterns": defaultdict(int),
                    "tool_preferences": defaultdict(int),
                    "topic_preferences": defaultdict(int),
                    "feedback_history": [],
                    "response_time_preferences": [],
                }

            user_data = self.user_patterns[user_id]

            # Update topic preferences
            for topic in metrics.topics or []:
                user_data["topic_preferences"][topic] += 1

            # Update tool preferences based on feedback
            if metrics.feedback_type == FeedbackType.POSITIVE:
                for tool in metrics.tools_used or []:
                    user_data["tool_preferences"][tool] += 1
            elif metrics.feedback_type == FeedbackType.NEGATIVE:
                for tool in metrics.tools_used or []:
                    user_data["tool_preferences"][tool] -= 1

            # Store feedback history for trend analysis
            user_data["feedback_history"].append(
                {
                    "timestamp": metrics.timestamp.isoformat(),
                    "feedback_type": (
                        metrics.feedback_type.value if metrics.feedback_type else "neutral"
                    ),
                    "context_score": metrics.context_relevance_score,
                }
            )

            # Keep only recent feedback (last 100 interactions)
            user_data["feedback_history"] = user_data["feedback_history"][-100:]

        except Exception:
            log_service_status("LEARNING", "error", "Pattern update failed: {e}")

    async def _check_knowledge_expansion(
        self, user_id: str, metrics: InteractionMetrics, user_message: str, assistant_response: str
    ):
        """Check if this interaction should trigger knowledge base expansion."""
        try:
            # Criteria for knowledge expansion:
            # 1. User provided correction or clarification
            # 2. New factual information in the conversation
            # 3. High-quality interaction with positive feedback

            should_expand = False
            expansion_content = ""
            expansion_type = ""

            if metrics.feedback_type == FeedbackType.CORRECTION:
                should_expand = True
                expansion_content = "User correction: {user_message}\nContext: {assistant_response}"
                expansion_type = "correction"

            elif (
                metrics.feedback_type == FeedbackType.POSITIVE
                and metrics.context_relevance_score > 0.7
            ):
                should_expand = True
                expansion_content = (
                    "High-quality interaction: Q: {user_message}\nA: {assistant_response}"
                )
                expansion_type = "quality_interaction"

            elif any(
                keyword in user_message.lower()
                for keyword in ["learn", "remember", "note", "important"]
            ):
                should_expand = True
                expansion_content = "User-requested learning: {user_message}"
                expansion_type = "user_requested"

            if should_expand and expansion_content:
                self.knowledge_expansion_queue.append(
                    {
                        "user_id": user_id,
                        "content": expansion_content,
                        "type": expansion_type,
                        "timestamp": datetime.now().isoformat(),
                        "topics": metrics.topics,
                    }
                )

                # Immediately process high-priority expansions
                if expansion_type in ["correction", "user_requested"]:
                    await self._process_knowledge_expansion(
                        user_id, expansion_content, expansion_type
                    )

        except Exception:
            log_service_status("LEARNING", "error", "Knowledge expansion check failed: {e}")

    async def _process_knowledge_expansion(self, user_id: str, content: str, expansion_type: str):
        """Process knowledge expansion by storing new information."""
        try:
            doc_id = "learning_{expansion_type}_{user_id}_{int(time.time())}"

            # Use the more efficient batch indexing function
            success = index_document_chunks(
                db_manager=db_manager,
                user_id=user_id,
                doc_id=doc_id,
                name="Learned Knowledge - {expansion_type}",
                chunks=[content],
                # Wrap content in a list for the new function
            )

            if success:
                log_service_status(
                    "LEARNING", "ready", "Expanded knowledge base for {user_id}: {expansion_type}"
                )
            else:
                log_service_status(
                    "LEARNING", "error", "Failed to expand knowledge base for {user_id}"
                )

        except Exception:
            log_service_status("LEARNING", "error", "Knowledge expansion processing failed: {e}")

    async def _update_user_preferences(self, user_id: str, metrics: InteractionMetrics):
        """Update user preference models based on interaction feedback."""
        try:
            # This could include preferences for:
            # - Response length
            # - Level of detail
            # - Preferred tools
            # - Communication style
            # - Topic interests

            preferences = self.user_patterns[user_id].get("preferences", {})

            # Update response time preferences
            if metrics.feedback_type == FeedbackType.POSITIVE:
                preferences["preferred_response_time"] = preferences.get(
                    "preferred_response_time", []
                )
                preferences["preferred_response_time"].append(metrics.response_time)
                preferences["preferred_response_time"] = preferences["preferred_response_time"][
                    -10:
                ]  # Keep last 10

            # Update detail level preferences based on follow-up questions
            if metrics.follow_up_questions > 2:
                preferences["detail_level"] = preferences.get("detail_level", 0.5) + 0.1
            elif (
                metrics.follow_up_questions == 0 and metrics.feedback_type == FeedbackType.POSITIVE
            ):
                preferences["detail_level"] = preferences.get("detail_level", 0.5) - 0.05

            # Normalize detail level between 0 and 1
            preferences["detail_level"] = max(0, min(1, preferences.get("detail_level", 0.5)))

            self.user_patterns[user_id]["preferences"] = preferences

        except Exception:
            log_service_status("LEARNING", "error", "Preference update failed: {e}")

    async def process_knowledge_expansion_queue(self):
        """Process queued knowledge expansions in background."""
        try:
            while self.knowledge_expansion_queue:
                item = self.knowledge_expansion_queue.popleft()
                await self._process_knowledge_expansion(
                    item["user_id"], item["content"], item["type"]
                )
                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.1)

        except Exception:
            log_service_status("LEARNING", "error", "Queue processing failed: {e}")


# Background task function
async def start_learning_background_tasks():
    """Start background tasks for the learning system."""
    try:
        while True:
            await adaptive_learning_system.process_knowledge_expansion_queue()
            await asyncio.sleep(60)  # Process queue every minute
    except Exception:
        log_service_status("LEARNING", "error", "Background task error: {e}")


# Global adaptive learning system instance
adaptive_learning_system = AdaptiveLearningSystem()
