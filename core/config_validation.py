"""Stricter configuration validation.

Performs fatal validation for critical environment variables that must be
present in production. Non-production modes (when ENVIRONMENT != production)
log warnings instead of raising.

Usage: import and call validate_configuration() early in startup.
"""
from __future__ import annotations
import os
import sys
from typing import List

REQUIRED_VARS: List[str] = [
    # Core connectivity (add more as they become mandatory)
    # 'REDIS_URL',  # Optional: comment out if dynamic discovery allowed
    # Placeholder for future critical vars
]

def validate_configuration() -> None:
    env = os.getenv("ENVIRONMENT", "development").lower()
    missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
    if not missing:
        return
    if env == "production":
        # Fail fast in production
        sys.stderr.write(f"[FATAL] Missing required environment variables: {', '.join(missing)}\n")
        raise SystemExit(1)
    else:
        sys.stderr.write(f"[WARN] Missing recommended env vars (non-fatal in {env}): {', '.join(missing)}\n")

__all__ = ["validate_configuration", "REQUIRED_VARS"]
