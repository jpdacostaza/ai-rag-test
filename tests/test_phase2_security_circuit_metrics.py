import os
import re
import importlib
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.security import SecurityHeadersMiddleware
from utilities.circuit_breaker import CircuitBreaker, circuit_breaker_state_total
from core.metrics import METRICS_ENABLED, generate_latest


def test_csp_nonce_optional(monkeypatch):
    monkeypatch.setenv('CSP_NONCE_ENABLED', 'true')
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get('/csp')
    def csp():
        # Access nonce if set
        return {'ok': True}

    client = TestClient(app)
    r = client.get('/csp')
    assert r.status_code == 200
    csp = r.headers.get('Content-Security-Policy', '')
    assert "script-src 'self' 'nonce-" in csp
    # Ensure nonce pattern appears
    assert re.search(r"nonce-[A-Za-z0-9_\-]{10,}", csp)

    # Disable and verify no nonce
    monkeypatch.setenv('CSP_NONCE_ENABLED', 'false')
    r2 = client.get('/csp')
    csp2 = r2.headers.get('Content-Security-Policy', '')
    assert "nonce-" not in csp2


@pytest.mark.skipif(not METRICS_ENABLED, reason='Prometheus metrics disabled')
def test_circuit_breaker_state_metric():
    # Create breaker with tiny reset
    br = CircuitBreaker('metric_test', failure_threshold=1, reset_timeout=0.05)
    # Force open
    br.record_failure()
    assert br.state == 'open'
    # Allow half-open transition
    import time
    time.sleep(0.06)
    assert br.allow() is True  # half_open
    # Success closes
    br.record_success()
    # Scrape metrics
    data = generate_latest().decode()
    # Expect at least states: open, half_open, closed
    assert 'circuit_breaker_state_total' in data
    assert 'state="open"' in data
    # half_open or closed may appear depending on race; assert closed
    assert 'state="closed"' in data
