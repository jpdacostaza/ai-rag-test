"""Simple async-aware circuit breaker implementation for external service calls."""
from __future__ import annotations
import time
from typing import Optional
import os
from core.unified_logging import log_service_status
from core.metrics import METRICS_ENABLED
try:  # optional, metric only if prometheus available
    from core.metrics import Counter
except Exception:  # pragma: no cover
    Counter = None  # type: ignore

if METRICS_ENABLED and Counter:
    circuit_breaker_state_total = Counter(
        "circuit_breaker_state_total", "Circuit breaker state changes", ["name", "state"]
    )
else:
    class _Dummy:  # noqa: D401
        def labels(self, *_, **__):
            return self
        def inc(self):
            pass
    circuit_breaker_state_total = _Dummy()

class CircuitBreaker:
    """A lightweight circuit breaker.

    States: closed -> open -> half_open -> closed
    """
    def __init__(self, name: str, failure_threshold: int = 5, reset_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._failures = 0
        self._state = "closed"
        self._opened_at: Optional[float] = None

    def _transition(self, new_state: str):
        if new_state != self._state:
            log_service_status("circuit_breaker", "info", f"Breaker '{self.name}' state {self._state} -> {new_state}")
            circuit_breaker_state_total.labels(name=self.name, state=new_state).inc()
            self._state = new_state
            if new_state == "open":
                self._opened_at = time.time()
            elif new_state == "closed":
                self._failures = 0
                self._opened_at = None

    def allow(self) -> bool:
        if self._state == "closed":
            return True
        if self._state == "open":
            if self._opened_at and (time.time() - self._opened_at) >= self.reset_timeout:
                self._transition("half_open")
                return True
            return False
        if self._state == "half_open":
            return True
        return True

    def record_success(self):
        if self._state in ("half_open", "open"):
            self._transition("closed")
        else:
            self._failures = 0

    def record_failure(self):
        self._failures += 1
        if self._state == "half_open":
            # Immediate reopen on failure in half-open
            self._transition("open")
        elif self._failures >= self.failure_threshold:
            self._transition("open")

    @property
    def state(self) -> str:
        return self._state

# Global breaker for LLM
_llm_breaker: Optional[CircuitBreaker] = None

def get_llm_breaker() -> CircuitBreaker:
    global _llm_breaker
    if _llm_breaker is None:
        try:
            failure_threshold = int(os.getenv("LLM_BREAKER_FAILURE_THRESHOLD", "3"))
        except ValueError:
            failure_threshold = 3
        try:
            reset_timeout = float(os.getenv("LLM_BREAKER_RESET_TIMEOUT", "20"))
        except ValueError:
            reset_timeout = 20.0
        _llm_breaker = CircuitBreaker("llm", failure_threshold=failure_threshold, reset_timeout=reset_timeout)
    return _llm_breaker
