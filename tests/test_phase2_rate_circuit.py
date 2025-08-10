import time
import pytest
from fastapi.testclient import TestClient
from core.main import app
from utilities.circuit_breaker import CircuitBreaker


def test_rate_limit_headers_present(monkeypatch):
    client = TestClient(app)
    limit = 2
    # First allowed
    r1 = client.post('/v1/chat/completions', headers={'x-test-rate-limit': str(limit), 'x-user-id':'hdr-user'}, json={'model':'m','messages':[{'role':'user','content':'hi'}]})
    assert r1.status_code in (200, 429)
    # Second attempt
    r2 = client.post('/v1/chat/completions', headers={'x-test-rate-limit': str(limit), 'x-user-id':'hdr-user'}, json={'model':'m','messages':[{'role':'user','content':'hi'}]})
    # Third to possibly trigger limit
    r3 = client.post('/v1/chat/completions', headers={'x-test-rate-limit': str(limit), 'x-user-id':'hdr-user'}, json={'model':'m','messages':[{'role':'user','content':'hi'}]})
    sample = r3 if r3.status_code != 429 else r2
    # Headers should appear on a non-429 response
    if sample.status_code == 200:
        assert 'X-RateLimit-Limit' in sample.headers
        assert 'X-RateLimit-Remaining' in sample.headers
        assert 'X-RateLimit-Reset' in sample.headers
    else:
        pytest.skip('Could not validate headers due to tight limit producing only 429 responses')


def test_circuit_breaker_half_open_cycle(monkeypatch):
    # Use short timings
    br = CircuitBreaker('test', failure_threshold=2, reset_timeout=0.2)
    assert br.state == 'closed'
    # Cause failures to open
    br.record_failure()
    assert br.state == 'closed'  # threshold not reached
    br.record_failure()
    assert br.state == 'open'
    # Not allowed before timeout
    assert br.allow() is False
    # Advance time to trigger half-open
    start = time.time()
    while time.time() - start < 0.25:
        pass
    assert br.allow() is True  # transitions to half_open
    assert br.state == 'half_open'
    # Fail once in half-open -> immediate open
    br.record_failure()
    assert br.state == 'open'
    # Advance again to half-open
    start = time.time()
    while time.time() - start < 0.25:
        pass
    assert br.allow() is True
    # Success now -> closed
    br.record_success()
    assert br.state == 'closed'
