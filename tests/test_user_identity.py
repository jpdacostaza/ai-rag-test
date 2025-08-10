import types
from typing import Dict, Any

from services.user_identity import resolve_user_id

class DummyRequest:
    def __init__(self, headers: Dict[str, str], host: str = "127.0.0.1"):
        self.headers = types.SimpleNamespace(get=lambda k, d=None: headers.get(k, d))
        self.client = types.SimpleNamespace(host=host)


def make_messages(contents):
    msgs = []
    for role, content in contents:
        msgs.append({"role": role, "content": content})
    return msgs


def test_body_user_object_email():
    req = DummyRequest({})
    body = {"user": {"email": "user@example.com", "id": "u1"}}
    messages = []
    assert resolve_user_id(req, body, messages) == "user@example.com"


def test_header_user():
    req = DummyRequest({"x-user-id": "header_user"})
    body = {}
    assert resolve_user_id(req, body, []) == "header_user"


def test_pipeline_injected():
    req = DummyRequest({})
    body = {}
    msgs = make_messages([("system", "AUTHENTICATED_USER_ID: pipeline_user")])
    assert resolve_user_id(req, body, msgs) == "pipeline_user"


def test_system_pattern():
    req = DummyRequest({})
    body = {}
    msgs = make_messages([("system", "context info user_id: pattern_user other stuff")])
    assert resolve_user_id(req, body, msgs) == "pattern_user"


def test_memory_context_email():
    req = DummyRequest({})
    body = {}
    msgs = make_messages([("system", "Previous conversation context and memories: user email test@test.org data")])
    assert resolve_user_id(req, body, msgs) == "test@test.org"


def test_bearer_token_derivation():
    req = DummyRequest({"authorization": "Bearer abcdef1234567890TOKENXYZ"})
    body = {}
    uid = resolve_user_id(req, body, [])
    assert uid.startswith("auth_") and len(uid) <= 21


def test_session_fallback_deterministic():
    req = DummyRequest({"user-agent": "TestAgent/1.0"}, host="1.2.3.4")
    body = {}
    uid1 = resolve_user_id(req, body, [])
    uid2 = resolve_user_id(req, body, [])
    assert uid1 == uid2
    assert uid1.startswith("session_")
