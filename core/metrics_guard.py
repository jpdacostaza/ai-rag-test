"""Metrics cardinality guard utilities.

Provides helper to sanitize/limit high-cardinality label values before
emitting Prometheus metrics. Use for any user/input-derived label.
"""
from __future__ import annotations
import re
from typing import Iterable

_SAFE_RE = re.compile(r"[^a-zA-Z0-9_:\-]+")

def normalize_label(value: str, max_length: int = 64) -> str:
    """Normalize potentially unsafe/high-cardinality label value.

    - Lowercase
    - Replace disallowed chars with '_'
    - Truncate to max_length
    - Empty -> 'unknown'
    """
    if value is None:
        return "unknown"
    v = value.strip().lower()
    v = _SAFE_RE.sub("_", v)
    if not v:
        return "unknown"
    if len(v) > max_length:
        v = v[:max_length]
    return v

def whitelist_label(value: str, allowed: Iterable[str], default: str = "other") -> str:
    v = normalize_label(value)
    return v if v in allowed else default

__all__ = ["normalize_label", "whitelist_label"]
