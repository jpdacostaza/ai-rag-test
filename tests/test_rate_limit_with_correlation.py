from fastapi import FastAPI
from fastapi.testclient import TestClient
from middleware.rate_limit_middleware import RateLimitMiddleware
from core.security import SecurityHeadersMiddleware
from tests.helpers.correlation import install_test_correlation_middleware


def build_app(limit=2):
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, limit_per_minute=limit)
    install_test_correlation_middleware(app)

    @app.post('/chat')
    async def chat():
        return {'ok': True}
    return app


def test_rate_limit_response_has_correlation_and_headers():
    app = build_app()
    client = TestClient(app)
    headers = {'x-user-id': 'abc', 'x-test-rate-limit': '2'}
    r1 = client.post('/chat', headers=headers)
    cid = r1.headers.get('X-Correlation-ID')
    assert cid
    r2 = client.post('/chat', headers=headers)
    r3 = client.post('/chat', headers=headers)
    # Third should be limited
    assert r3.status_code == 429
    body = r3.json()
    assert 'error' in body
    assert body['error']['code'] == 'rate_limited'
    # Still should include correlation id on error path if security middleware runs first
    assert 'X-Correlation-ID' in r3.headers
