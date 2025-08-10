import asyncio
import json
import re
import time
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.security import SecurityHeadersMiddleware
from core.error_handler import ErrorHandler
from core.metrics import generate_latest, METRICS_ENABLED
from core.enhanced_api_gateway import EnhancedAPIGateway
from core.error_handler import RedisConnectionHandler
import redis


# ----------------------------- Security Headers ----------------------------- #

def test_security_headers_present():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)
    r = client.get("/ping")
    assert r.status_code == 200
    # Core headers we added
    for h in [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Strict-Transport-Security",
        "Content-Security-Policy",
        "Permissions-Policy",
        "Referrer-Policy",
    ]:
        assert h in r.headers, f"Missing security header: {h}"


# ----------------------------- Error Handler ------------------------------ #

def test_error_handler_keyerror_message():
    err = KeyError("missing_field")
    resp = ErrorHandler.create_error_response(err, context="test")
    # Should map KeyError to friendly message substring
    assert "missing" in resp.message.lower()
    assert resp.error is True
    assert resp.error_type == "KeyError"


# ----------------------------- Gateway Metrics ----------------------------- #

class DummyRequest:
    def __init__(self, method: str = "GET", path: str = "/x", remote: str = "127.0.0.1"):
        self.method = method
        self.path = path
        self.remote = remote
        self._cached_body_size = 0

@pytest.mark.asyncio
async def test_gateway_metrics_increment():
    gw = EnhancedAPIGateway()  # uses default services
    req = DummyRequest()
    # Pre snapshot of metrics text
    before = generate_latest().decode() if METRICS_ENABLED else ""
    await gw._record_metrics(req, status_code=200, duration_ms=15.0, service_name="unknown")
    after = generate_latest().decode() if METRICS_ENABLED else ""
    if METRICS_ENABLED:
        # Look for our counter line with labels we used
        assert re.search(r'gateway_requests_total\{[^}]*service="unknown"[^}]*status="200"', after), after
        # Ensure latency histogram line appears (bucket or sum) for service/method
        assert 'gateway_request_latency_seconds' in after
    else:
        # Fallback: just ensure no exception
        assert True


# ----------------------------- Async Retry Backoff ------------------------ #

@pytest.mark.asyncio
async def test_retry_operation_uses_async_sleep(monkeypatch):
    handler = RedisConnectionHandler(max_retries=3)

    attempt_counter = {"count": 0}

    async def fake_create(name: str = ""):
        attempt_counter["count"] += 1
        if attempt_counter["count"] < 3:
            raise redis.RedisError("temp failure")
        class Dummy:
            pass
        return Dummy()

    sleeps = []
    async def fake_sleep(seconds):
        sleeps.append(seconds)
        # don't actually sleep

    # Patch the connection factory method
    monkeypatch.setattr(handler.connection_factory, "create_redis_connection", lambda connection_name="": fake_create(connection_name))
    # Patch asyncio.sleep
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    async def op(client, *a, **k):  # operation to run once connection created
        return True

    result = await handler.retry_operation(op)
    assert result is True
    # We expect two backoff sleeps: 1, 2 (exponential 2 ** attempt with attempts 0,1 failing)
    assert sleeps == [1, 2]
    assert attempt_counter["count"] == 3
