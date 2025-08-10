"""Simple token-bucket style rate limiting middleware.

Redis-backed when available; falls back to per-process in-memory store.
Limits are coarse (per user_id per minute) to reduce overhead.
"""
from __future__ import annotations
import time
import asyncio
from typing import Dict, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from core.error_response import build_error
from core.metrics import METRICS_ENABLED, rate_limit_blocked_total
from core.unified_logging import log_service_status, get_correlation_id

# In-memory fallback store: key -> (reset_ts, count)
_memory_counters: Dict[str, Tuple[float, int]] = {}
_lock = asyncio.Lock()

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit_per_minute: int = 60):
        super().__init__(app)
        self.limit_per_minute = limit_per_minute
        import os
        scope = os.getenv("RATE_LIMIT_SCOPE", "user").strip().lower()
        if scope not in ("user", "ip", "both"):
            scope = "user"
        self.scope = scope

    async def dispatch(self, request: Request, call_next):  # type: ignore
        # Only rate limit API POSTs to chat endpoints (extend as needed)
        if request.method == 'POST' and request.url.path in ('/v1/chat/completions', '/chat'):  # adapt patterns
            user_id = request.headers.get('x-user-id') or request.headers.get('x-user') or 'anonymous'
            # Prefer X-Forwarded-For (first value) for reverse proxy deployments
            fwd_for = request.headers.get('x-forwarded-for')
            if fwd_for and ',' in fwd_for:
                fwd_for = fwd_for.split(',')[0].strip()
            client_ip = fwd_for or (request.client.host if request.client else 'unknown') or 'unknown'
            if self.scope == 'ip':
                key = f"rlip:{client_ip}"
            elif self.scope == 'both':
                key = f"rlmix:{user_id}:{client_ip}"
            else:
                key = f"rl:{user_id}"
            # Test override header for deterministic unit tests
            override = request.headers.get('x-test-rate-limit')
            try:
                effective_limit = int(override) if override and override.isdigit() else self.limit_per_minute
            except Exception:
                effective_limit = self.limit_per_minute
            now = time.time()
            window = 60
            allowed = True

            # Try Redis first
            redis_client = None
            try:
                from services.database_manager import db_manager
                if db_manager and db_manager.redis_client:
                    redis_client = db_manager.redis_client
            except Exception:
                pass

            if redis_client:
                try:
                    # Use Redis INCR with TTL pattern
                    count = await redis_client.incr(key)
                    if count == 1:
                        await redis_client.expire(key, window)
                    if count > effective_limit:
                        allowed = False
                except Exception as e:  # pragma: no cover
                    log_service_status('rate_limit', 'warning', f"Redis rate limit fallback: {e}")
                    redis_client = None

            if not redis_client:
                # Fallback to in-memory counter
                async with _lock:
                    reset_ts, count = _memory_counters.get(key, (now + window, 0))
                    if now > reset_ts:
                        reset_ts = now + window
                        count = 0
                    count += 1
                    _memory_counters[key] = (reset_ts, count)
                    if count > effective_limit:
                        allowed = False

            if not allowed:
                if METRICS_ENABLED:
                    rate_limit_blocked_total.inc()
                cid = get_correlation_id()
                extra = f" cid={cid}" if cid else ""
                log_service_status('rate_limit', 'warning', f"Rate limit exceeded for user {user_id}{extra}")
                return build_error(
                    code="rate_limited",
                    message="Too many requests, slow down",
                    status=429,
                    details={"retry_after_seconds": int(window), "limit_per_minute": effective_limit},
                    retryable=True,
                    correlation_id=cid
                )
            response = await call_next(request)
            # Add informational headers (best-effort) when allowed
            try:
                remaining = max(0, effective_limit - (count if 'count' in locals() else 0))
                reset_ts = int((reset_ts if 'reset_ts' in locals() else time.time() + 60))
                response.headers['X-RateLimit-Limit'] = str(effective_limit)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Reset'] = str(reset_ts)
                response.headers['X-RateLimit-Scope'] = self.scope
            except Exception:
                pass
            return response
        return await call_next(request)
