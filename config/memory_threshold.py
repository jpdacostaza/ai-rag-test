"""Centralized Memory Threshold Accessor

Purpose:
    Provide a single authoritative location for the default memory retrieval
    threshold used across the system when the OpenWebUI function / external
    pipeline has not yet overridden it.

Rationale:
    Previously the literal value -0.5 appeared in multiple files with the
    comment 'Default fallback - should be overridden by function request'.
    This duplication risks drift if the fallback ever changes.

Usage:
    from config.memory_threshold import get_default_memory_threshold
    threshold = get_default_memory_threshold()

Change Policy:
    If the fallback value needs adjustment, change DEFAULT_MEMORY_THRESHOLD
    here only. Do NOT reintroduce hard-coded literals elsewhere.
"""

from functools import lru_cache
import os

# Single source fallback. Environment variable allows ops override without code change.
DEFAULT_MEMORY_THRESHOLD = float(os.getenv("DEFAULT_MEMORY_THRESHOLD", "-0.5"))

@lru_cache(maxsize=1)
def get_default_memory_threshold() -> float:
    """Return the system fallback memory retrieval threshold.

    This value is only used when an upstream component (OpenWebUI function,
    pipeline filter, explicit API request) does not provide a threshold.
    """
    return DEFAULT_MEMORY_THRESHOLD
