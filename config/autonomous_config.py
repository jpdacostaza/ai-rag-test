"""
Configuration for Autonomous Reasoning System
============================================

Settings and parameters for autonomous decision-making capabilities.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class AutonomousConfig:
    """Configuration for autonomous reasoning system."""
    
    # Planning Configuration
    enable_autonomous_planning: bool = True
    max_planning_depth: int = 5
    default_task_timeout: int = 300  # seconds
    max_concurrent_tasks: int = 3
    
    # Decision Making
    complexity_threshold: float = 5.0  # threshold for autonomous routing
    confidence_threshold: float = 0.6  # minimum confidence for autonomous execution
    enable_adaptive_strategies: bool = True
    
    # Tool Integration
    enable_autonomous_tool_selection: bool = True
    max_tool_chain_length: int = 4
    tool_timeout: int = 30  # seconds
    
    # Memory Integration
    enable_autonomous_memory_search: bool = True
    memory_relevance_threshold: float = 0.7
    max_memory_contexts: int = 5
    
    # Learning and Adaptation
    enable_execution_learning: bool = True
    store_execution_patterns: bool = True
    pattern_confidence_decay: float = 0.95  # per day
    
    # Safety and Constraints
    max_execution_time: int = 600  # seconds
    enable_validation_steps: bool = True
    require_user_confirmation: bool = False  # for high-risk operations
    
    # Logging and Monitoring
    detailed_logging: bool = True
    performance_tracking: bool = True
    execution_metrics: bool = True


# Global configuration instance
autonomous_config = AutonomousConfig()


# Intent classification patterns for autonomous routing
AUTONOMOUS_INTENT_PATTERNS = {
    "research_task": [
        "research", "investigate", "find information about", "analyze", 
        "study", "explore", "examine", "look into", "gather data"
    ],
    "planning_task": [
        "plan", "organize", "schedule", "create a strategy", "develop a plan",
        "outline", "structure", "design", "prepare", "coordinate"
    ],
    "multi_step_task": [
        "help me with", "work on", "complete", "accomplish", "achieve",
        "solve", "figure out", "step by step", "break down", "comprehensive"
    ],
    "data_analysis": [
        "compare", "contrast", "evaluate", "assess", "summarize",
        "synthesize", "correlate", "trend analysis", "insights"
    ],
    "problem_solving": [
        "troubleshoot", "debug", "fix", "resolve", "optimize",
        "improve", "enhance", "solve problem", "find solution"
    ]
}

# Strategy selection criteria
STRATEGY_SELECTION_RULES = {
    "direct_response": {
        "max_complexity": 3.0,
        "max_words": 20,
        "simple_patterns": ["what is", "define", "explain", "tell me"]
    },
    "tool_assisted": {
        "max_complexity": 5.0,
        "tool_keywords": ["weather", "time", "convert", "calculate", "search"],
        "single_action": True
    },
    "hybrid_approach": {
        "max_complexity": 7.0,
        "requires_context": True,
        "multiple_sources": True
    },
    "autonomous_execution": {
        "min_complexity": 7.0,
        "multi_step": True,
        "planning_required": True
    }
}

# Task execution templates
TASK_TEMPLATES = {
    "research_task": {
        "steps": [
            {"type": "memory_search", "description": "Search existing knowledge"},
            {"type": "tool_call", "description": "Web search for current information"},
            {"type": "llm_query", "description": "Synthesize findings"},
            {"type": "validation", "description": "Verify information accuracy"}
        ]
    },
    "analysis_task": {
        "steps": [
            {"type": "memory_search", "description": "Gather relevant data"},
            {"type": "llm_query", "description": "Perform analysis"},
            {"type": "tool_call", "description": "Additional data if needed"},
            {"type": "llm_query", "description": "Generate insights"},
            {"type": "validation", "description": "Validate conclusions"}
        ]
    },
    "planning_task": {
        "steps": [
            {"type": "llm_query", "description": "Break down requirements"},
            {"type": "memory_search", "description": "Find similar plans"},
            {"type": "llm_query", "description": "Create detailed plan"},
            {"type": "validation", "description": "Review plan feasibility"}
        ]
    }
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "response_time": {
        "excellent": 2000,  # ms
        "good": 5000,
        "acceptable": 10000,
        "poor": 15000
    },
    "accuracy": {
        "excellent": 0.95,
        "good": 0.85,
        "acceptable": 0.75,
        "poor": 0.65
    },
    "user_satisfaction": {
        "excellent": 0.9,
        "good": 0.8,
        "acceptable": 0.7,
        "poor": 0.6
    }
}


def get_autonomous_config() -> AutonomousConfig:
    """Get the global autonomous configuration."""
    return autonomous_config


def update_autonomous_config(**kwargs) -> None:
    """Update autonomous configuration settings."""
    global autonomous_config
    for key, value in kwargs.items():
        if hasattr(autonomous_config, key):
            setattr(autonomous_config, key, value)


def is_autonomous_enabled() -> bool:
    """Check if autonomous reasoning is enabled."""
    return autonomous_config.enable_autonomous_planning


def get_complexity_threshold() -> float:
    """Get the complexity threshold for autonomous routing."""
    return autonomous_config.complexity_threshold


def get_confidence_threshold() -> float:
    """Get the confidence threshold for autonomous execution."""
    return autonomous_config.confidence_threshold
