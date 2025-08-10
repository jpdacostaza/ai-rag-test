import os
import re
from fastapi import FastAPI
from fastapi.testclient import TestClient
from core.security import SecurityHeadersMiddleware


def _get_headers(csp_nonce_enabled: bool):
    os.environ['CSP_NONCE_ENABLED'] = 'true' if csp_nonce_enabled else 'false'
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)
    r = client.get("/ping")
    return r.headers


def test_security_headers_baseline_and_nonce():
    h_base = _get_headers(False)
    for expected in [
        'X-Content-Type-Options', 'X-Frame-Options', 'Strict-Transport-Security',
        'Content-Security-Policy', 'Permissions-Policy', 'Referrer-Policy'
    ]:
        assert expected in h_base
    csp_base = h_base['Content-Security-Policy']
    assert 'script-src' in csp_base
    assert 'nonce-' not in csp_base

    h_nonce = _get_headers(True)
    csp_nonce = h_nonce['Content-Security-Policy']
    assert 'nonce-' in csp_nonce
    # Allow base64 or urlsafe base64 style (may include - or _)
    assert re.search(r"nonce-[A-Za-z0-9_\-]{10,}", csp_nonce)
