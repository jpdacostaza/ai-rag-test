#!/usr/bin/env python3
# filepath: e:\Projects\opt\backend\review_memory_learning.py
"""
Review Learning and Memory Functions
====================================

This script analyzes all memory and learning-related functions in the codebase
and provides detailed improvement suggestions.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json


class MemoryLearningReviewer:
    """TODO: Add proper docstring for MemoryLearningReviewer class."""

    def __init__(self, project_root="."):
        """TODO: Add proper docstring for __init__."""
        self.project_root = Path(project_root)
        self.memory_files = []
        self.learning_files = []
        self.issues = []
        self.improvements = []

    def find_memory_learning_files(self):
        """Find all files related to memory and learning."""
        patterns = ["memory", "learning", "adaptive", "retrieval", "embedding", "vector"]

        for root, dirs, files in os.walk(self.project_root):
            # Skip irrelevant directories
            if any(skip in root for skip in [".git", "__pycache__", "venv", "test"]):
                continue

            for file in files:
                if file.endswith(".py"):
                    filepath = Path(root) / file
                    content = filepath.read_text(encoding="utf-8")

                    # Check if file contains memory/learning related code
                    if any(pattern in content.lower() for pattern in patterns):
                        if "memory" in file.lower() or "memory" in content.lower():
                            self.memory_files.append(filepath)
                        if "learning" in file.lower() or "adaptive" in content.lower():
                            self.learning_files.append(filepath)

    def analyze_memory_functions(self):
        """Analyze memory-related functions for issues and improvements."""
        print("\n🧠 Analyzing Memory Functions...")

        # Key files to analyze
        key_files = [
            "database_manager.py",
            "memory_manager.py",
            "enhanced_memory_system.py",
            "memory/advanced_memory_pipeline.py",
            "memory/memory_pipeline.py",
        ]

        for filename in key_files:
            filepath = self.project_root / filename
            if filepath.exists():
                self._analyze_file(filepath, "memory")

    def analyze_learning_functions(self):
        """Analyze learning-related functions for issues and improvements."""
        print("\n📚 Analyzing Learning Functions...")

        # Key files to analyze
        key_files = ["adaptive_learning.py", "enhanced_integration.py", "utilities/ai_tools.py"]

        for filename in key_files:
            filepath = self.project_root / filename
            if filepath.exists():
                self._analyze_file(filepath, "learning")

    def _analyze_file(self, filepath: Path, category: str):
        """Analyze a specific file for memory/learning issues."""
        try:
            content = filepath.read_text(encoding="utf-8")
            tree = ast.parse(content)

            # Analyze functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self._analyze_function(node, filepath, category)

        except Exception as e:
            self.issues.append({"file": str(filepath), "issue": f"Failed to parse file: {e}", "severity": "high"})

    def _analyze_function(self, node: ast.AST, filepath: Path, category: str):
        """Analyze a specific function for issues."""
        function_name = node.name

        # Check for common issues
        issues = []

        # 1. Check for missing error handling
        has_try_except = any(isinstance(n, ast.Try) for n in ast.walk(node))
        if not has_try_except and not function_name.startswith("_"):
            issues.append("Missing error handling")

        # 2. Check for performance issues
        if self._has_nested_loops(node):
            issues.append("Nested loops detected - potential O(n²) complexity")

        # 3. Check for memory leaks
        if self._has_potential_memory_leak(node):
            issues.append("Potential memory leak - large data structures not cleared")

        # 4. Check for missing validation
        if self._lacks_input_validation(node):
            issues.append("Missing input validation")

        # 5. Check for synchronization issues
        if "async" in ast.unparse(node) and self._lacks_proper_locking(node):
            issues.append("Potential race condition - missing locks/semaphores")

        if issues:
            self.issues.append(
                {"file": str(filepath), "function": function_name, "issues": issues, "category": category}
            )

    def _has_nested_loops(self, node: ast.AST) -> bool:
        """Check if function has nested loops."""
        loop_depth = 0
        max_depth = 0

        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While)):
                loop_depth += 1
                max_depth = max(max_depth, loop_depth)
            elif isinstance(child, ast.FunctionDef):
                loop_depth = 0

        return max_depth > 1

    def _has_potential_memory_leak(self, node: ast.AST) -> bool:
        """Check for potential memory leaks."""
        # Look for large collections that aren't cleared
        has_large_collection = False
        has_clear_operation = False

        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                if child.id in ["cache", "buffer", "history", "data"]:
                    has_large_collection = True
            if isinstance(child, ast.Call):
                if hasattr(child.func, "attr") and child.func.attr in ["clear", "close", "cleanup"]:
                    has_clear_operation = True

        return has_large_collection and not has_clear_operation

    def _lacks_input_validation(self, node: ast.AST) -> bool:
        """Check if function lacks input validation."""
        # Check if function has parameters but no validation
        if node.args.args:
            has_validation = any(
                isinstance(n, ast.If)
                or (
                    isinstance(n, ast.Call)
                    and hasattr(n.func, "id")
                    and n.func.id in ["isinstance", "validate", "check"]
                )
                for n in ast.walk(node)
            )
            return not has_validation
        return False

    def _lacks_proper_locking(self, node: ast.AST) -> bool:
        """Check if async function lacks proper locking."""
        has_shared_state = any(isinstance(n, ast.Attribute) and "self" in ast.unparse(n) for n in ast.walk(node))
        has_lock = any(
            "lock" in ast.unparse(n).lower() or "semaphore" in ast.unparse(n).lower() for n in ast.walk(node)
        )
        return has_shared_state and not has_lock

    def generate_improvements(self):
        """Generate specific improvements for memory and learning functions."""

        self.improvements = [
            {
                "category": "Memory Management",
                "improvements": [
                    {
                        "title": "Implement Memory Pooling",
                        "description": "Use object pooling for frequently created/destroyed memory objects",
                        "code": self._get_memory_pooling_code(),
                    },
                    {
                        "title": "Add Memory Pressure Monitoring",
                        "description": "Monitor and respond to memory pressure",
                        "code": self._get_memory_monitoring_code(),
                    },
                    {
                        "title": "Implement Hierarchical Memory",
                        "description": "Create memory hierarchy for better organization",
                        "code": self._get_hierarchical_memory_code(),
                    },
                ],
            },
            {
                "category": "Learning Optimization",
                "improvements": [
                    {
                        "title": "Implement Learning Rate Scheduling",
                        "description": "Adaptive learning rate based on performance",
                        "code": self._get_learning_rate_code(),
                    },
                    {
                        "title": "Add Reinforcement Learning",
                        "description": "Learn from user feedback",
                        "code": self._get_reinforcement_learning_code(),
                    },
                    {
                        "title": "Implement Meta-Learning",
                        "description": "Learn how to learn better",
                        "code": self._get_meta_learning_code(),
                    },
                ],
            },
            {
                "category": "Retrieval Enhancement",
                "improvements": [
                    {
                        "title": "Implement Hybrid Search",
                        "description": "Combine vector and keyword search",
                        "code": self._get_hybrid_search_code(),
                    },
                    {
                        "title": "Add Contextual Reranking",
                        "description": "Rerank results based on context",
                        "code": self._get_reranking_code(),
                    },
                    {
                        "title": "Implement Query Expansion",
                        "description": "Expand queries for better recall",
                        "code": self._get_query_expansion_code(),
                    },
                ],
            },
        ]

    def _get_memory_pooling_code(self) -> str:
        """TODO: Add proper docstring for _get_memory_pooling_code."""
        return '''# In utilities/memory_pool.py
from typing import List, Dict, Any, Optional
from collections import deque
import asyncio
import time

class MemoryPool:
    """Object pool for memory chunks to reduce allocation overhead."""
    
    def __init__(self, chunk_size: int = 1024, max_pool_size: int = 100):
        self.chunk_size = chunk_size
        self.max_pool_size = max_pool_size
        self.pool: deque = deque(maxlen=max_pool_size)
        self._lock = asyncio.Lock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'created': 0,
            'recycled': 0
        }
        
    async def acquire(self) -> Dict[str, Any]:
        """Acquire a memory chunk from the pool."""
        async with self._lock:
            if self.pool:
                chunk = self.pool.popleft()
                self._stats['hits'] += 1
                self._stats['recycled'] += 1
                # Clear the chunk for reuse
                chunk['content'] = ''
                chunk['metadata'] = {}
                chunk['timestamp'] = time.time()
                return chunk
            else:
                self._stats['misses'] += 1
                self._stats['created'] += 1
                return self._create_chunk()
                
    async def release(self, chunk: Dict[str, Any]):
        """Return a chunk to the pool."""
        async with self._lock:
            if len(self.pool) < self.max_pool_size:
                self.pool.append(chunk)
                
    def _create_chunk(self) -> Dict[str, Any]:
        """Create a new memory chunk."""
        return {
            'id': None,
            'content': '',
            'embedding': None,
            'metadata': {},
            'timestamp': time.time(),
            'access_count': 0,
            'importance_score': 0.0
        }
        
    def get_stats(self) -> Dict[str, int]:
        """Get pool statistics."""
        return {
            **self._stats,
            'pool_size': len(self.pool),
            'efficiency': self._stats['hits'] / max(1, self._stats['hits'] + self._stats['misses'])
        }

# Usage in database_manager.py
memory_pool = MemoryPool()

async def store_memory_efficient(content: str, metadata: Dict[str, Any]):
    """Store memory using object pool."""
    chunk = await memory_pool.acquire()
    try:
        chunk['content'] = content
        chunk['metadata'] = metadata
        # Process and store...
        return chunk
    except Exception as e:
        await memory_pool.release(chunk)
        raise'''

    def _get_memory_monitoring_code(self) -> str:
        """TODO: Add proper docstring for _get_memory_monitoring_code."""
        return '''# In utilities/memory_monitor.py
import psutil
import asyncio
from typing import Callable, Optional
from human_logging import log_service_status

class MemoryMonitor:
    """Monitor memory usage and trigger cleanup when needed."""
    
    def __init__(self, threshold_percent: float = 80.0):
        self.threshold_percent = threshold_percent
        self.cleanup_callbacks: List[Callable] = []
        self._monitoring = False
        self._task: Optional[asyncio.Task] = None
        
    def register_cleanup(self, callback: Callable):
        """Register a cleanup callback."""
        self.cleanup_callbacks.append(callback)
        
    async def start_monitoring(self, interval: int = 30):
        """Start memory monitoring."""
        self._monitoring = True
        self._task = asyncio.create_task(self._monitor_loop(interval))
        
    async def stop_monitoring(self):
        """Stop memory monitoring."""
        self._monitoring = False
        if self._task:
            self._task.cancel()
            
    async def _monitor_loop(self, interval: int):
        """Main monitoring loop."""
        while self._monitoring:
            try:
                memory_percent = psutil.virtual_memory().percent
                
                if memory_percent > self.threshold_percent:
                    log_service_status(
                        'memory_monitor',
                        'warning',
                        f'Memory usage high: {memory_percent:.1f}%'
                    )
                    await self._trigger_cleanup()
                    
                # Log stats periodically
                log_service_status(
                    'memory_monitor',
                    'info',
                    f'Memory usage: {memory_percent:.1f}%'
                )
                
            except Exception as e:
                log_service_status(
                    'memory_monitor',
                    'error',
                    f'Monitoring error: {e}'
                )
                
            await asyncio.sleep(interval)
            
    async def _trigger_cleanup(self):
        """Trigger all cleanup callbacks."""
        for callback in self.cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                log_service_status(
                    'memory_monitor',
                    'error',
                    f'Cleanup callback failed: {e}'
                )

# Usage in startup.py
memory_monitor = MemoryMonitor(threshold_percent=75.0)

# Register cleanup functions
memory_monitor.register_cleanup(db_manager.cleanup_old_memories)
memory_monitor.register_cleanup(cache_manager.clear_expired)

# Start monitoring
await memory_monitor.start_monitoring()'''

    def _get_hierarchical_memory_code(self) -> str:
        """TODO: Add proper docstring for _get_hierarchical_memory_code."""
        return '''# In memory/hierarchical_memory.py
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import asyncio

class MemoryLevel(Enum):
    """Memory hierarchy levels."""
    WORKING = "working"      # Current conversation
    SHORT_TERM = "short"     # Recent interactions (hours)
    LONG_TERM = "long"       # Historical data (days+)
    EPISODIC = "episodic"    # Specific events
    SEMANTIC = "semantic"    # General knowledge

class HierarchicalMemory:
    """Hierarchical memory system with different retention policies."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.levels = {
            MemoryLevel.WORKING: {
                'ttl': timedelta(minutes=30),
                'max_items': 50,
                'importance_threshold': 0.0
            },
            MemoryLevel.SHORT_TERM: {
                'ttl': timedelta(hours=24),
                'max_items': 500,
                'importance_threshold': 0.3
            },
            MemoryLevel.LONG_TERM: {
                'ttl': timedelta(days=365),
                'max_items': 10000,
                'importance_threshold': 0.6
            },
            MemoryLevel.EPISODIC: {
                'ttl': None,  # No expiration
                'max_items': 1000,
                'importance_threshold': 0.8
            },
            MemoryLevel.SEMANTIC: {
                'ttl': None,  # No expiration
                'max_items': 5000,
                'importance_threshold': 0.7
            }
        }
        self._promotion_task = None
        
    async def store(self, content: str, metadata: Dict[str, Any], 
                   level: MemoryLevel = MemoryLevel.WORKING):
        """Store memory at specific level."""
        importance = await self._calculate_importance(content, metadata)
        
        memory_data = {
            'content': content,
            'metadata': metadata,
            'level': level.value,
            'importance': importance,
            'timestamp': datetime.utcnow(),
            'access_count': 0
        }
        
        # Store in appropriate level
        await self._store_at_level(memory_data, level)
        
        # Check if should be promoted to higher levels
        await self._check_promotion(memory_data)
        
    async def retrieve(self, query: str, levels: Optional[List[MemoryLevel]] = None,
                      limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve memories from specified levels."""
        if levels is None:
            levels = list(MemoryLevel)
            
        results = []
        for level in levels:
            level_results = await self._retrieve_from_level(query, level, limit)
            results.extend(level_results)
            
        # Sort by relevance and recency
        results.sort(key=lambda x: (x['relevance'], x['timestamp']), reverse=True)
        return results[:limit]
        
    async def _calculate_importance(self, content: str, metadata: Dict[str, Any]) -> float:
        """Calculate importance score for memory."""
        score = 0.0
        
        # Length factor
        score += min(len(content) / 1000, 0.3)
        
        # Metadata factors
        if metadata.get('user_feedback') == 'positive':
            score += 0.3
        if metadata.get('contains_personal_info'):
            score += 0.2
        if metadata.get('is_question'):
            score += 0.1
            
        # Semantic importance (would use LLM in production)
        important_keywords = ['important', 'remember', 'don\'t forget', 'crucial']
        if any(keyword in content.lower() for keyword in important_keywords):
            score += 0.2
            
        return min(score, 1.0)
        
    async def _promote_memories(self):
        """Promote important memories to higher levels."""
        while True:
            try:
                # Check working memory for promotion
                working_memories = await self._get_memories_for_level(MemoryLevel.WORKING)
                
                for memory in working_memories:
                    if memory['importance'] > self.levels[MemoryLevel.SHORT_TERM]['importance_threshold']:
                        await self._store_at_level(memory, MemoryLevel.SHORT_TERM)
                        
                # Check short-term for promotion to long-term
                short_memories = await self._get_memories_for_level(MemoryLevel.SHORT_TERM)
                
                for memory in short_memories:
                    if memory['access_count'] > 3 and \
                       memory['importance'] > self.levels[MemoryLevel.LONG_TERM]['importance_threshold']:
                        await self._store_at_level(memory, MemoryLevel.LONG_TERM)
                        
            except Exception as e:
                log_service_status('hierarchical_memory', 'error', f'Promotion error: {e}')
                
            await asyncio.sleep(300)  # Run every 5 minutes
            
    async def start_promotion_task(self):
        """Start the memory promotion background task."""
        self._promotion_task = asyncio.create_task(self._promote_memories())
        
    async def consolidate_memories(self):
        """Consolidate similar memories to save space."""
        # Group similar memories and create summary
        # This would use embedding similarity in production
        pass'''

    def _get_learning_rate_code(self) -> str:
        """TODO: Add proper docstring for _get_learning_rate_code."""
        return '''# In learning/adaptive_scheduler.py
from typing import Dict, Any, Optional
import math
from datetime import datetime, timedelta

class AdaptiveLearningScheduler:
    """Adaptive learning rate scheduler based on performance."""
    
    def __init__(self, initial_rate: float = 0.1):
        self.initial_rate = initial_rate
        self.current_rate = initial_rate
        self.performance_history = []
        self.adjustment_history = []
        
    def update_performance(self, metric: float, timestamp: Optional[datetime] = None):
        """Update with latest performance metric."""
        if timestamp is None:
            timestamp = datetime.utcnow()
            
        self.performance_history.append({
            'metric': metric,
            'timestamp': timestamp,
            'rate': self.current_rate
        })
        
        # Adjust learning rate based on performance
        self._adjust_rate()
        
    def _adjust_rate(self):
        """Adjust learning rate based on recent performance."""
        if len(self.performance_history) < 2:
            return
            
        # Calculate performance trend
        recent_performance = self.performance_history[-10:]
        if len(recent_performance) < 2:
            return
            
        # Simple trend analysis
        improvements = 0
        for i in range(1, len(recent_performance)):
            if recent_performance[i]['metric'] > recent_performance[i-1]['metric']:
                improvements += 1
                
        improvement_rate = improvements / (len(recent_performance) - 1)
        
        # Adjust rate based on improvement
        if improvement_rate > 0.7:
            # Good progress, can increase rate
            self.current_rate = min(self.current_rate * 1.1, 1.0)
        elif improvement_rate < 0.3:
            # Poor progress, reduce rate
            self.current_rate = max(self.current_rate * 0.9, 0.01)
            
        # Apply decay over time
        self._apply_time_decay()
        
    def _apply_time_decay(self):
        """Apply time-based decay to learning rate."""
        if not self.adjustment_history:
            start_time = datetime.utcnow()
        else:
            start_time = self.adjustment_history[0]['timestamp']
            
        time_elapsed = (datetime.utcnow() - start_time).days
        
        # Exponential decay
        decay_factor = math.exp(-0.001 * time_elapsed)
        self.current_rate = self.initial_rate * decay_factor
        
    def get_rate(self) -> float:
        """Get current learning rate."""
        return self.current_rate
        
    def should_learn(self, importance: float) -> bool:
        """Determine if should learn based on importance and current rate."""
        # Probabilistic learning based on importance and rate
        threshold = (1 - self.current_rate) * (1 - importance)
        return random.random() > threshold

# Usage in adaptive_learning.py
scheduler = AdaptiveLearningScheduler(initial_rate=0.15)

# Update based on user feedback
if feedback == 'positive':
    scheduler.update_performance(0.9)
elif feedback == 'negative':
    scheduler.update_performance(0.3)
    
# Use in learning decision
if scheduler.should_learn(importance_score):
    await store_learning_example(...)'''

    def _get_reinforcement_learning_code(self) -> str:
        """TODO: Add proper docstring for _get_reinforcement_learning_code."""
        return '''# In learning/reinforcement_learner.py
from typing import Dict, List, Any, Tuple
import numpy as np
from collections import defaultdict
import json

class ReinforcementLearner:
    """Learn from user feedback using reinforcement learning."""
    
    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.9):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.action_history = []
        self.reward_history = []
        
    def record_action(self, state: Dict[str, Any], action: str, context: Dict[str, Any]):
        """Record an action taken in a given state."""
        state_key = self._serialize_state(state)
        self.action_history.append({
            'state': state_key,
            'action': action,
            'context': context,
            'timestamp': datetime.utcnow()
        })
        
    def record_reward(self, reward: float, action_index: int = -1):
        """Record reward for a previous action."""
        if action_index == -1 and self.action_history:
            action_index = len(self.action_history) - 1
            
        if 0 <= action_index < len(self.action_history):
            self.reward_history.append({
                'action_index': action_index,
                'reward': reward,
                'timestamp': datetime.utcnow()
            })
            
            # Update Q-table
            self._update_q_value(action_index, reward)
            
    def _update_q_value(self, action_index: int, reward: float):
        """Update Q-value using Q-learning algorithm."""
        if action_index >= len(self.action_history):
            return
            
        action_data = self.action_history[action_index]
        state = action_data['state']
        action = action_data['action']
        
        # Current Q-value
        current_q = self.q_table[state][action]
        
        # Find max Q-value for next state (if exists)
        max_next_q = 0
        if action_index + 1 < len(self.action_history):
            next_state = self.action_history[action_index + 1]['state']
            if next_state in self.q_table:
                max_next_q = max(self.q_table[next_state].values())
                
        # Q-learning update
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state][action] = new_q
        
    def get_best_action(self, state: Dict[str, Any], available_actions: List[str],
                       exploration_rate: float = 0.1) -> str:
        """Get best action for given state using epsilon-greedy strategy."""
        state_key = self._serialize_state(state)
        
        # Exploration vs exploitation
        if np.random.random() < exploration_rate:
            # Explore: random action
            return np.random.choice(available_actions)
        else:
            # Exploit: best known action
            if state_key in self.q_table:
                action_values = self.q_table[state_key]
                # Filter to available actions
                available_values = {
                    action: value 
                    for action, value in action_values.items() 
                    if action in available_actions
                }
                if available_values:
                    return max(available_values, key=available_values.get)
                    
            # No known good action, return random
            return np.random.choice(available_actions)
            
    def _serialize_state(self, state: Dict[str, Any]) -> str:
        """Serialize state to string key."""
        # Simplified serialization - in production would use better method
        key_parts = []
        for k, v in sorted(state.items()):
            if isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}:{v}")
        return "|".join(key_parts)
        
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights about learned behavior."""
        insights = {
            'total_states': len(self.q_table),
            'total_actions': sum(len(actions) for actions in self.q_table.values()),
            'average_reward': np.mean([r['reward'] for r in self.reward_history]) if self.reward_history else 0,
            'top_actions': self._get_top_actions(),
            'learning_progress': self._calculate_learning_progress()
        }
        return insights
        
    def _get_top_actions(self, n: int = 5) -> List[Tuple[str, float]]:
        """Get top N actions by average Q-value."""
        action_values = defaultdict(list)
        
        for state_actions in self.q_table.values():
            for action, value in state_actions.items():
                action_values[action].append(value)
                
        avg_values = {
            action: np.mean(values) 
            for action, values in action_values.items()
        }
        
        return sorted(avg_values.items(), key=lambda x: x[1], reverse=True)[:n]

# Usage in chat processing
rl_learner = ReinforcementLearner()

# Record action
state = {
    'user_intent': 'question',
    'topic': 'technical',
    'conversation_length': 5
}
action = 'provide_detailed_explanation'
rl_learner.record_action(state, action, {'response_length': 500})

# Record feedback as reward
if user_feedback == 'thumbs_up':
    rl_learner.record_reward(1.0)
elif user_feedback == 'thumbs_down':
    rl_learner.record_reward(-1.0)'''

    def _get_meta_learning_code(self) -> str:
        """TODO: Add proper docstring for _get_meta_learning_code."""
        return '''# In learning/meta_learner.py
from typing import Dict, List, Any, Optional
import numpy as np
from dataclasses import dataclass
from datetime import datetime

@dataclass
class LearningStrategy:
    """Represents a learning strategy."""
    name: str
    parameters: Dict[str, Any]
    performance_history: List[float]
    usage_count: int = 0
    
class MetaLearner:
    """Learn which learning strategies work best in different contexts."""
    
    def __init__(self):
        self.strategies = {
            'frequency_based': LearningStrategy(
                name='frequency_based',
                parameters={'weight': 0.3, 'threshold': 5},
                performance_history=[]
            ),
            'recency_based': LearningStrategy(
                name='recency_based',
                parameters={'decay_factor': 0.95, 'window': 100},
                performance_history=[]
            ),
            'importance_based': LearningStrategy(
                name='importance_based',
                parameters={'min_importance': 0.7, 'boost_factor': 2.0},
                performance_history=[]
            ),
            'hybrid': LearningStrategy(
                name='hybrid',
                parameters={'weights': [0.3, 0.3, 0.4]},
                performance_history=[]
            )
        }
        self.context_strategy_map = {}
        self.adaptation_history = []
        
    def select_strategy(self, context: Dict[str, Any]) -> str:
        """Select best learning strategy for given context."""
        context_key = self._get_context_key(context)
        
        # Check if we have a known good strategy for this context
        if context_key in self.context_strategy_map:
            return self.context_strategy_map[context_key]
            
        # Otherwise, use multi-armed bandit approach
        return self._select_via_ucb(context)
        
    def _select_via_ucb(self, context: Dict[str, Any]) -> str:
        """Select strategy using Upper Confidence Bound algorithm."""
        total_usage = sum(s.usage_count for s in self.strategies.values())
        
        ucb_scores = {}
        for name, strategy in self.strategies.items():
            if strategy.usage_count == 0:
                # Encourage exploration of unused strategies
                ucb_scores[name] = float('inf')
            else:
                # Calculate average performance
                avg_performance = np.mean(strategy.performance_history[-10:])
                
                # Calculate exploration bonus
                exploration_bonus = np.sqrt(2 * np.log(total_usage) / strategy.usage_count)
                
                # UCB score
                ucb_scores[name] = avg_performance + exploration_bonus
                
        # Select strategy with highest UCB score
        selected = max(ucb_scores, key=ucb_scores.get)
        self.strategies[selected].usage_count += 1
        
        return selected
        
    def update_performance(self, strategy_name: str, performance: float, context: Dict[str, Any]):
        """Update strategy performance based on results."""
        if strategy_name not in self.strategies:
            return
            
        strategy = self.strategies[strategy_name]
        strategy.performance_history.append(performance)
        
        # Update context-strategy mapping if performance is good
        if performance > 0.8:
            context_key = self._get_context_key(context)
            self.context_strategy_map[context_key] = strategy_name
            
        # Record adaptation
        self.adaptation_history.append({
            'timestamp': datetime.utcnow(),
            'strategy': strategy_name,
            'performance': performance,
            'context': context
        })
        
        # Adapt strategy parameters if needed
        self._adapt_strategy_parameters(strategy_name)
        
    def _adapt_strategy_parameters(self, strategy_name: str):
        """Adapt strategy parameters based on performance."""
        strategy = self.strategies[strategy_name]
        
        if len(strategy.performance_history) < 10:
            return
            
        recent_performance = strategy.performance_history[-10:]
        avg_performance = np.mean(recent_performance)
        
        # Simple parameter adaptation
        if strategy_name == 'frequency_based':
            if avg_performance < 0.5:
                # Lower threshold if not performing well
                strategy.parameters['threshold'] = max(1, strategy.parameters['threshold'] - 1)
            elif avg_performance > 0.8:
                # Increase weight if performing well
                strategy.parameters['weight'] = min(1.0, strategy.parameters['weight'] + 0.05)
                
        elif strategy_name == 'importance_based':
            if avg_performance < 0.5:
                # Lower importance threshold
                strategy.parameters['min_importance'] = max(0.3, strategy.parameters['min_importance'] - 0.1)
                
    def _get_context_key(self, context: Dict[str, Any]) -> str:
        """Generate a key for context."""
        # Simplified - in production would use more sophisticated method
        key_parts = []
        for k in ['domain', 'user_type', 'task_type']:
            if k in context:
                key_parts.append(f"{k}:{context[k]}")
        return "|".join(key_parts)
        
    def get_insights(self) -> Dict[str, Any]:
        """Get meta-learning insights."""
        insights = {
            'strategy_performance': {
                name: {
                    'avg_performance': np.mean(s.performance_history[-50:]) if s.performance_history else 0,
                    'usage_count': s.usage_count,
                    'current_parameters': s.parameters
                }
                for name, s in self.strategies.items()
            },
            'best_contexts': self.context_strategy_map,
            'adaptation_count': len(self.adaptation_history)
        }
        return insights

# Usage in adaptive learning
meta_learner = MetaLearner()

# Select strategy for current context
context = {
    'domain': 'technical',
    'user_type': 'expert',
    'task_type': 'problem_solving'
}
strategy = meta_learner.select_strategy(context)

# Apply selected strategy
result = apply_learning_strategy(strategy, data)

# Update based on performance
performance = calculate_performance(result, ground_truth)
meta_learner.update_performance(strategy, performance, context)'''

    def _get_hybrid_search_code(self) -> str:
        """TODO: Add proper docstring for _get_hybrid_search_code."""
        return '''# In retrieval/hybrid_search.py
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from rank_bm25 import BM25Okapi

class HybridSearchEngine:
    """Combine vector similarity and keyword search for better retrieval."""
    
    def __init__(self, vector_weight: float = 0.7, keyword_weight: float = 0.3):
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000)
        self.bm25 = None
        self.documents = []
        self.document_vectors = []
        
    def index_documents(self, documents: List[Dict[str, Any]]):
        """Index documents for hybrid search."""
        self.documents = documents
        
        # Extract text content
        texts = [doc.get('content', '') for doc in documents]
        
        # Build TF-IDF index
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
        
        # Build BM25 index
        tokenized_docs = [text.lower().split() for text in texts]
        self.bm25 = BM25Okapi(tokenized_docs)
        
        # Store embeddings if available
        self.document_vectors = [doc.get('embedding', None) for doc in documents]
        
    async def search(self, query: str, query_embedding: np.ndarray, 
                    top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        """Perform hybrid search combining vector and keyword matching."""
        
        # Vector similarity search
        vector_scores = self._compute_vector_similarity(query_embedding)
        
        # Keyword search using BM25
        keyword_scores = self._compute_keyword_scores(query)
        
        # TF-IDF similarity
        tfidf_scores = self._compute_tfidf_scores(query)
        
        # Combine scores
        combined_scores = self._combine_scores(
            vector_scores, 
            keyword_scores, 
            tfidf_scores
        )
        
        # Get top results
        top_indices = np.argsort(combined_scores)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if combined_scores[idx] > 0:
                results.append((
                    self.documents[idx],
                    float(combined_scores[idx])
                ))
                
        return results
        
    def _compute_vector_similarity(self, query_embedding: np.ndarray) -> np.ndarray:
        """Compute cosine similarity with document embeddings."""
        if not self.document_vectors or self.document_vectors[0] is None:
            return np.zeros(len(self.documents))
            
        similarities = []
        for doc_vector in self.document_vectors:
            if doc_vector is not None:
                similarity = np.dot(query_embedding, doc_vector) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(doc_vector)
                )
                similarities.append(similarity)
            else:
                similarities.append(0.0)
                
        return np.array(similarities)
        
    def _compute_keyword_scores(self, query: str) -> np.ndarray:
        """Compute BM25 scores."""
        if self.bm25 is None:
            return np.zeros(len(self.documents))
            
        query_tokens = query.lower().split()
        scores = self.bm25.get_scores(query_tokens)
        
        # Normalize scores
        max_score = max(scores) if max(scores) > 0 else 1.0
        return scores / max_score
        
    def _compute_tfidf_scores(self, query: str) -> np.ndarray:
        """Compute TF-IDF similarity scores."""
        query_vector = self.tfidf_vectorizer.transform([query])
        similarities = (self.tfidf_matrix * query_vector.T).toarray().flatten()
        return similarities
        
    def _combine_scores(self, vector_scores: np.ndarray, 
                       keyword_scores: np.ndarray,
                       tfidf_scores: np.ndarray) -> np.ndarray:
        """Combine different scoring methods."""
        # Normalize each score type
        vector_norm = vector_scores / (np.max(vector_scores) + 1e-6)
        keyword_norm = keyword_scores / (np.max(keyword_scores) + 1e-6)
        tfidf_norm = tfidf_scores / (np.max(tfidf_scores) + 1e-6)
        
        # Weighted combination
        combined = (
            self.vector_weight * vector_norm +
            self.keyword_weight * 0.6 * keyword_norm +
            self.keyword_weight * 0.4 * tfidf_norm
        )
        
        return combined
        
    def update_weights(self, feedback: Dict[str, Any]):
        """Update weights based on user feedback."""
        if feedback.get('vector_helpful', True):
            self.vector_weight = min(0.9, self.vector_weight + 0.05)
            self.keyword_weight = 1 - self.vector_weight
        else:
            self.keyword_weight = min(0.9, self.keyword_weight + 0.05)
            self.vector_weight = 1 - self.keyword_weight

# Usage in memory retrieval
hybrid_search = HybridSearchEngine()

# Index memories
memories = await db_manager.get_all_memories(user_id)
hybrid_search.index_documents(memories)

# Search
results = await hybrid_search.search(
    query="What did we discuss about Python?",
    query_embedding=query_embedding,
    top_k=5
)'''

    def _get_reranking_code(self) -> str:
        """TODO: Add proper docstring for _get_reranking_code."""
        return '''# In retrieval/contextual_reranker.py
from typing import List, Dict, Any, Tuple
import numpy as np
from datetime import datetime, timedelta

class ContextualReranker:
    """Rerank search results based on context and user preferences."""
    
    def __init__(self):
        self.context_weights = {
            'recency': 0.2,
            'relevance': 0.4,
            'importance': 0.2,
            'user_preference': 0.2
        }
        self.user_preferences = {}
        
    async def rerank(self, results: List[Tuple[Dict[str, Any], float]], 
                    context: Dict[str, Any], 
                    user_id: str) -> List[Tuple[Dict[str, Any], float]]:
        """Rerank results based on multiple factors."""
        
        # Get user preferences
        preferences = self.user_preferences.get(user_id, {})
        
        reranked = []
        for doc, base_score in results:
            # Calculate component scores
            recency_score = self._calculate_recency_score(doc, context)
            importance_score = self._calculate_importance_score(doc, context)
            preference_score = self._calculate_preference_score(doc, preferences)
            
            # Combine scores
            final_score = (
                self.context_weights['relevance'] * base_score +
                self.context_weights['recency'] * recency_score +
                self.context_weights['importance'] * importance_score +
                self.context_weights['user_preference'] * preference_score
            )
            
            # Apply context-specific boosting
            final_score = self._apply_context_boost(final_score, doc, context)
            
            reranked.append((doc, final_score))
            
        # Sort by final score
        reranked.sort(key=lambda x: x[1], reverse=True)
        
        return reranked
        
    def _calculate_recency_score(self, doc: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate recency score based on timestamp."""
        if 'timestamp' not in doc:
            return 0.5
            
        doc_time = doc['timestamp']
        if isinstance(doc_time, str):
            doc_time = datetime.fromisoformat(doc_time)
            
        # Calculate age in hours
        age_hours = (datetime.utcnow() - doc_time).total_seconds() / 3600
        
        # Decay function
        if context.get('prefer_recent', True):
            # Exponential decay with half-life of 24 hours
            score = np.exp(-age_hours / 24)
        else:
            # Inverse - prefer older for historical queries
            score = 1 - np.exp(-age_hours / 168)  # Weekly half-life
            
        return score
        
    def _calculate_importance_score(self, doc: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate importance based on various signals."""
        importance = doc.get('importance_score', 0.5)
        
        # Boost if marked as important
        if doc.get('metadata', {}).get('starred', False):
            importance = min(1.0, importance + 0.3)
            
        # Boost if frequently accessed
        access_count = doc.get('access_count', 0)
        if access_count > 5:
            importance = min(1.0, importance + 0.1 * np.log(access_count))
            
        # Context-specific importance
        if context.get('task_type') == 'problem_solving':
            if doc.get('metadata', {}).get('contains_solution', False):
                importance = min(1.0, importance + 0.4)
                
        return importance
        
    def _calculate_preference_score(self, doc: Dict[str, Any], preferences: Dict[str, Any]) -> float:
        """Calculate score based on user preferences."""
        score = 0.5  # Neutral default
        
        # Topic preferences
        doc_topics = doc.get('topics', [])
        preferred_topics = preferences.get('preferred_topics', [])
        
        for topic in doc_topics:
            if topic in preferred_topics:
                score += 0.1
                
        # Source preferences
        doc_source = doc.get('source', 'unknown')
        preferred_sources = preferences.get('preferred_sources', [])
        
        if doc_source in preferred_sources:
            score += 0.2
            
        # Length preferences
        doc_length = len(doc.get('content', ''))
        preferred_length = preferences.get('preferred_length', 'medium')
        
        if preferred_length == 'short' and doc_length < 500:
            score += 0.1
        elif preferred_length == 'long' and doc_length > 1000:
            score += 0.1
        elif preferred_length == 'medium' and 500 <= doc_length <= 1000:
            score += 0.1
            
        return min(1.0, score)
        
    def _apply_context_boost(self, score: float, doc: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Apply context-specific score boosting."""
        
        # Boost if document matches current conversation topic
        if context.get('current_topic'):
            doc_topics = doc.get('topics', [])
            if context['current_topic'] in doc_topics:
                score *= 1.3
                
        # Boost if from same conversation thread
        if context.get('conversation_id'):
            if doc.get('conversation_id') == context['conversation_id']:
                score *= 1.2
                
        # Boost based on query intent
        intent = context.get('query_intent', 'general')
        
        if intent == 'factual' and doc.get('metadata', {}).get('is_fact', False):
            score *= 1.4
        elif intent == 'opinion' and doc.get('metadata', {}).get('is_opinion', False):
            score *= 1.3
        elif intent == 'instruction' and doc.get('metadata', {}).get('is_instruction', False):
            score *= 1.5
            
        return score
        
    def update_preferences(self, user_id: str, feedback: Dict[str, Any]):
        """Update user preferences based on feedback."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                'preferred_topics': [],
                'preferred_sources': [],
                'preferred_length': 'medium'
            }
            
        prefs = self.user_preferences[user_id]
        
        # Update based on positive feedback
        if feedback.get('helpful', False):
            doc = feedback.get('document', {})
            
            # Update topic preferences
            for topic in doc.get('topics', []):
                if topic not in prefs['preferred_topics']:
                    prefs['preferred_topics'].append(topic)
                    
            # Update source preferences
            source = doc.get('source')
            if source and source not in prefs['preferred_sources']:
                prefs['preferred_sources'].append(source)

# Usage in memory retrieval
reranker = ContextualReranker()

# Initial search results
search_results = await hybrid_search.search(query, embedding)

# Rerank based on context
context = {
    'prefer_recent': True,
    'task_type': 'problem_solving',
    'current_topic': 'python',
    'query_intent': 'instruction'
}

reranked_results = await reranker.rerank(search_results, context, user_id)'''

    def _get_query_expansion_code(self) -> str:
        """TODO: Add proper docstring for _get_query_expansion_code."""
        return '''# In retrieval/query_expander.py
from typing import List, Dict, Any, Set
import nltk
from nltk.corpus import wordnet
import spacy

class QueryExpander:
    """Expand queries to improve recall."""
    
    def __init__(self):
        # Load spaCy model for NER and POS tagging
        self.nlp = spacy.load("en_core_web_sm")
        
        # Download required NLTK data
        nltk.download('wordnet', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        
        self.expansion_cache = {}
        self.domain_terms = self._load_domain_terms()
        
    def expand_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Expand query with synonyms, related terms, and variations."""
        
        # Check cache
        cache_key = f"{query}:{str(context)}"
        if cache_key in self.expansion_cache:
            return self.expansion_cache[cache_key]
            
        # Process query with spaCy
        doc = self.nlp(query)
        
        expanded = {
            'original': query,
            'tokens': [],
            'entities': [],
            'synonyms': [],
            'related_terms': [],
            'acronyms': [],
            'variations': []
        }
        
        # Extract entities
        for ent in doc.ents:
            expanded['entities'].append({
                'text': ent.text,
                'label': ent.label_
            })
            
        # Process each token
        for token in doc:
            if not token.is_stop and not token.is_punct:
                expanded['tokens'].append(token.text)
                
                # Get synonyms
                synonyms = self._get_synonyms(token.text, token.pos_)
                expanded['synonyms'].extend(synonyms)
                
                # Get domain-specific expansions
                domain_expansions = self._get_domain_expansions(token.text, context)
                expanded['related_terms'].extend(domain_expansions)
                
        # Generate query variations
        expanded['variations'] = self._generate_variations(query, expanded)
        
        # Detect and expand acronyms
        expanded['acronyms'] = self._expand_acronyms(query)
        
        # Cache result
        self.expansion_cache[cache_key] = expanded
        
        return expanded
        
    def _get_synonyms(self, word: str, pos: str = None) -> List[str]:
        """Get synonyms from WordNet."""
        synonyms = set()
        
        # Map spaCy POS to WordNet POS
        pos_map = {
            'NOUN': wordnet.NOUN,
            'VERB': wordnet.VERB,
            'ADJ': wordnet.ADJ,
            'ADV': wordnet.ADV
        }
        
        wn_pos = pos_map.get(pos, None)
        
        # Get synsets
        synsets = wordnet.synsets(word, pos=wn_pos) if wn_pos else wordnet.synsets(word)
        
        for synset in synsets[:3]:  # Limit to top 3 senses
            for lemma in synset.lemmas():
                synonym = lemma.name().replace('_', ' ')
                if synonym.lower() != word.lower():
                    synonyms.add(synonym)
                    
        return list(synonyms)[:5]  # Return top 5 synonyms
        
    def _get_domain_expansions(self, term: str, context: Dict[str, Any]) -> List[str]:
        """Get domain-specific term expansions."""
        expansions = []
        
        domain = context.get('domain', 'general') if context else 'general'
        
        if domain in self.domain_terms:
            term_lower = term.lower()
            if term_lower in self.domain_terms[domain]:
                expansions.extend(self.domain_terms[domain][term_lower])
                
        return expansions
        
    def _generate_variations(self, query: str, expanded: Dict[str, Any]) -> List[str]:
        """Generate query variations."""
        variations = []
        
        # Add synonym variations
        for synonym in expanded['synonyms'][:3]:
            variation = query
            for token in expanded['tokens']:
                if token in query:
                    variation = variation.replace(token, synonym, 1)
                    break
            if variation != query:
                variations.append(variation)
                
        # Add question variations
        if query.endswith('?'):
            base_query = query[:-1]
            variations.extend([
                f"What is {base_query}?",
                f"How to {base_query}?",
                f"Why {base_query}?"
            ])
            
        # Add entity-focused variations
        for entity in expanded['entities']:
            variations.append(f"{entity['text']} {query}")
            
        return variations[:5]  # Limit variations
        
    def _expand_acronyms(self, query: str) -> List[Dict[str, str]]:
        """Detect and expand acronyms."""
        acronyms = []
        
        # Common acronyms mapping
        acronym_map = {
            'ML': 'Machine Learning',
            'AI': 'Artificial Intelligence',
            'NLP': 'Natural Language Processing',
            'API': 'Application Programming Interface',
            'DB': 'Database',
            'LLM': 'Large Language Model',
            'RAG': 'Retrieval Augmented Generation'
        }
        
        words = query.split()
        for word in words:
            if word.upper() in acronym_map:
                acronyms.append({
                    'acronym': word,
                    'expansion': acronym_map[word.upper()]
                })
                
        return acronyms
        
    def _load_domain_terms(self) -> Dict[str, Dict[str, List[str]]]:
        """Load domain-specific term mappings."""
        return {
            'technical': {
                'bug': ['error', 'issue', 'problem', 'defect'],
                'fix': ['repair', 'resolve', 'patch', 'solution'],
                'code': ['program', 'script', 'software', 'implementation'],
                'function': ['method', 'procedure', 'routine', 'operation']
            },
            'medical': {
                'pain': ['ache', 'discomfort', 'soreness'],
                'doctor': ['physician', 'practitioner', 'specialist'],
                'medicine': ['medication', 'drug', 'treatment']
            }
        }
        
    def create_expanded_query_string(self, expanded: Dict[str, Any], boost_original: bool = True) -> str:
        """Create search query string from expanded terms."""
        
        # Start with original query
        query_parts = [expanded['original']] if boost_original else []
        
        # Add high-value expansions
        query_parts.extend(expanded['synonyms'][:2])
        query_parts.extend([e['expansion'] for e in expanded['acronyms']])
        
        # Add some variations
        query_parts.extend(expanded['variations'][:2])
        
        # Join with OR operator
        return ' OR '.join(f'("{part}")' for part in query_parts)

# Usage in search
expander = QueryExpander()

# Expand user query
expanded = expander.expand_query(
    "How to fix ML bug?",
    context={'domain': 'technical'}
)

# Create expanded search query
search_query = expander.create_expanded_query_string(expanded)
# Result: "How to fix ML bug?" OR "Machine Learning" OR "error" OR "issue"'''

    def generate_report(self):
        """Generate comprehensive report."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "files_analyzed": {"memory_files": len(self.memory_files), "learning_files": len(self.learning_files)},
            "issues_found": len(self.issues),
            "improvements_suggested": sum(len(cat["improvements"]) for cat in self.improvements),
            "detailed_analysis": {"issues": self.issues, "improvements": self.improvements},
        }

        return report

    def run_review(self):
        """Run complete review of memory and learning functions."""
        print("🔍 Starting Memory and Learning Review...")

        # Find relevant files
        self.find_memory_learning_files()

        # Analyze functions
        self.analyze_memory_functions()
        self.analyze_learning_functions()

        # Generate improvements
        self.generate_improvements()

        # Generate report
        report = self.generate_report()

        # Save report
        report_path = Path("memory_learning_review.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n✅ Review complete! Report saved to: {report_path}")

        # Print summary
        print(f"\n📊 Summary:")
        print(f"  - Memory files analyzed: {len(self.memory_files)}")
        print(f"  - Learning files analyzed: {len(self.learning_files)}")
        print(f"  - Issues found: {len(self.issues)}")
        print(f"  - Improvements suggested: {sum(len(cat['improvements']) for cat in self.improvements)}")

        return report


if __name__ == "__main__":
    reviewer = MemoryLearningReviewer()
    reviewer.run_review()
