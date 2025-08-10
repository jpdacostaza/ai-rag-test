import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from middleware.rate_limit_middleware import RateLimitMiddleware


def build_app(limit=5):
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, limit_per_minute=limit)

    @app.post("/chat")
    async def chat():
        return {"ok": True}
    return app


def test_rate_limit_enforced_in_memory():
    app = build_app(limit=3)
    client = TestClient(app)
    headers = {"x-user-id": "u1", "x-test-rate-limit": "3"}
    for i in range(3):
        r = client.post("/chat", headers=headers, json={"m": i})
        assert r.status_code == 200
    r = client.post("/chat", headers=headers, json={"m": 4})
    assert r.status_code == 429
    body = r.json()
    assert 'error' in body
    assert body['error']['code'] == 'rate_limited'
