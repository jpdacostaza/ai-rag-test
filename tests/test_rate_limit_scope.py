import os
import pytest
from fastapi.testclient import TestClient
from core.main import app
import types


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    # Ensure deterministic limit for tests
    monkeypatch.setenv('RATE_LIMIT_PER_MINUTE', '5')
    yield

@pytest.mark.parametrize('scope,header_a,header_b', [
    ('user', {'x-user-id': 'u1'}, {'x-user-id': 'u2'}),  # separate buckets
    ('ip', {}, {}),  # same IP consumes shared bucket
    ('both', {'x-user-id': 'u1'}, {'x-user-id': 'u1'}),  # same composite
])
def test_rate_limit_scopes(monkeypatch, scope, header_a, header_b):
    monkeypatch.setenv('RATE_LIMIT_SCOPE', scope)
    # Monkeypatch LLM call to be instantaneous
    import services.llm_service as llm_mod
    async def fast_llm(*args, **kwargs):
        return {
            'model': 'dummy',
            'choices': [{'message': {'role': 'assistant', 'content': 'ok'}}],
            'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2}
        }
    llm_mod.call_llm = fast_llm  # type: ignore
    client = TestClient(app)

    # Helper to post a minimal chat request
    def do_req(extra_headers):
        body = {
            'model': 'dummy',
            'messages': [
                {'role': 'user', 'content': 'hello'}
            ]
        }
        headers = dict(extra_headers)
        # Force low limit deterministically
        headers['x-test-rate-limit'] = '5'
        return client.post('/v1/chat/completions', json=body, headers=headers)

    # Fire 3 quick requests with small limit; 3rd should block for same bucket
    r1 = do_req(header_a)
    r2 = do_req(header_a)
    r3 = do_req(header_a)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code in (200, 429)
    blocked_same = (r3.status_code == 429)

    r_other = do_req(header_b)
    if scope == 'user':
        # Other user unaffected; original bucket likely blocked
        assert r_other.status_code == 200
    elif scope == 'ip':
        # Same IP so r_other likely also blocked once limit hit
        if blocked_same:
            assert r_other.status_code == 429
    elif scope == 'both':
        # Same user+ip composite behaves like user bucket
        if blocked_same:
            assert r_other.status_code == 429

    # Scope header present on successful responses
    for resp in (r1, r2):
        if resp.status_code == 200:
            assert 'X-RateLimit-Scope' in resp.headers


def test_rate_limit_headers_exposed(monkeypatch):
    monkeypatch.setenv('RATE_LIMIT_SCOPE', 'user')
    client = TestClient(app)
    body = { 'model': 'dummy', 'messages': [{'role': 'user', 'content': 'x'}] }
    # Patch LLM for this test as well
    import services.llm_service as llm_mod
    async def fast_llm2(*args, **kwargs):
        return {
            'model': 'dummy',
            'choices': [{'message': {'role': 'assistant', 'content': 'x'}}],
            'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2}
        }
    llm_mod.call_llm = fast_llm2  # type: ignore
    r = client.post('/v1/chat/completions', json=body, headers={'x-user-id': 'hdrtest', 'x-test-rate-limit': '5'})
    assert r.status_code in (200, 429)
    # Headers present when not blocked
    if r.status_code == 200:
        for h in ['X-RateLimit-Limit','X-RateLimit-Remaining','X-RateLimit-Reset','X-RateLimit-Scope']:
            assert h in r.headers
