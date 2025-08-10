import re
import time
from utilities.circuit_breaker import CircuitBreaker
from core.metrics import METRICS_ENABLED, generate_latest


def test_circuit_breaker_metric_labels():
    cb = CircuitBreaker(name="llm_test", failure_threshold=1, reset_timeout=0.05)
    assert cb.state == "closed"
    # Force open by recording a failure
    cb.record_failure()
    assert cb.state == "open"
    # Wait for reset timeout to allow half_open on allow()
    time.sleep(0.06)
    assert cb.allow() is True  # transitions to half_open internally
    assert cb.state in ("half_open", "open")
    # Record success to close
    cb.record_success()
    assert cb.state == "closed"
    if METRICS_ENABLED:
        text = generate_latest().decode()
        assert re.search(r'circuit_breaker_state_total\{[^}]*name="llm_test"[^}]*state="open"', text)
        assert re.search(r'circuit_breaker_state_total\{[^}]*name="llm_test"[^}]*state="closed"', text)
    else:
        assert True
