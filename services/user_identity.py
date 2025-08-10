"""Unified User Identity Resolution Module

Purpose:
    Centralize logic for extracting and validating a user identifier from
    OpenAI-compatible chat requests, headers, and pipeline-injected system
    messages. Previously duplicated across core.main and routes.chat.

Contract:
    resolve_user_id(request: fastapi.Request, body: dict, messages: list) -> str | None

Resolution Order (short-circuit on first valid):
    1. Explicit body.user (object: email > id > username > name)
    2. body.user as non-empty string
    3. Headers: x-user-id, x-user, x-openwebui-user, user-id, authorization token suffix
    4. Pipeline injected system message: AUTHENTICATED_USER_ID:{value}
    5. System message containing 'user_id:' pattern
    6. Memory context system message containing an email
    7. Authorization bearer token (derivative user id)
    8. Session fingerprint fallback (IP + user-agent hash)

Notes:
    - Does NOT create IDs from conversational content (privacy/safety)
    - Validation delegated to AuthValidator when available
    - Fallback session_* IDs are deterministic per (ip, user-agent) during process lifetime
"""
from __future__ import annotations
import hashlib
import re
from typing import Any, Dict, List, Optional
from core.unified_logging import log_service_status

try:
    from services.auth_validator import AuthValidator
    _AUTH_VALIDATOR_AVAILABLE = True
except Exception:  # pragma: no cover
    _AUTH_VALIDATOR_AVAILABLE = False
    AuthValidator = None  # type: ignore

PIPELINE_USER_PREFIX = "AUTHENTICATED_USER_ID:"
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
HEADER_CANDIDATES = ["x-user-id", "x-user", "x-openwebui-user", "user-id"]

def _validate(user_id: Optional[str]) -> Optional[str]:
    if not user_id:
        return None
    user_id = user_id.strip()
    if not user_id:
        return None
    if _AUTH_VALIDATOR_AVAILABLE:
        validator = AuthValidator()
        if not validator.is_valid_user_id(user_id):
            return None
    return user_id

def _extract_from_user_field(user_field: Any) -> Optional[str]:
    if isinstance(user_field, dict):
        for key in ("email", "id", "username", "name"):
            value = user_field.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    elif isinstance(user_field, str) and user_field.strip():
        return user_field.strip()
    return None

def _extract_pipeline_user(messages: List[Dict[str, Any]]) -> Optional[str]:
    for msg in messages or []:
        if msg.get("role") == "system" and isinstance(msg.get("content"), str) and msg["content"].startswith(PIPELINE_USER_PREFIX):
            candidate = msg["content"].replace(PIPELINE_USER_PREFIX, "").strip()
            return candidate or None
    return None

def _extract_system_user_pattern(messages: List[Dict[str, Any]]) -> Optional[str]:
    for msg in messages or []:
        if msg.get("role") == "system":
            content = msg.get("content", "")
            if "user_id:" in content:
                try:
                    after = content.split("user_id:", 1)[1]
                    token = after.split()[0].strip()
                    if token:
                        return token
                except Exception:
                    continue
    return None

def _extract_email_from_memory_context(messages: List[Dict[str, Any]]) -> Optional[str]:
    for msg in messages or []:
        if msg.get("role") == "system" and "Previous conversation context and memories" in msg.get("content", ""):
            match = EMAIL_REGEX.search(msg.get("content", ""))
            if match:
                return match.group()
    return None

def _extract_header_user(request) -> Optional[str]:  # type: ignore
    for header in HEADER_CANDIDATES:
        value = request.headers.get(header)
        if value:
            return value.strip()
    auth = request.headers.get("authorization") or ""
    if ":" in auth:
        parts = auth.split(":")
        if parts[-1].strip():
            return parts[-1].strip()
    return None

def _derive_from_bearer(request) -> Optional[str]:  # type: ignore
    auth_header = request.headers.get("authorization", "")
    if "Bearer" in auth_header:
        token = auth_header.replace("Bearer", "").strip()
        if token and token != "backend-api-key":
            return f"auth_{token[:16]}"
    return None

def _session_fingerprint(request) -> str:  # type: ignore
    host = getattr(getattr(request, "client", None), "host", "unknown")
    ua = request.headers.get("user-agent", "unknown")
    raw = f"{host}_{ua}"
    digest = hashlib.md5(raw.encode()).hexdigest()[:16]
    return f"session_{digest}"

def resolve_user_id(request, body: Dict[str, Any], messages: List[Dict[str, Any]]) -> Optional[str]:  # type: ignore
    log_service_status("AUTH", "debug", "[IDENTITY] Resolving user ID")
    candidate = _extract_from_user_field(body.get("user"))
    if _validate(candidate):
        return candidate
    candidate = _extract_header_user(request)
    if _validate(candidate):
        return candidate
    candidate = _extract_pipeline_user(messages)
    if _validate(candidate):
        return candidate
    candidate = _extract_system_user_pattern(messages)
    if _validate(candidate):
        return candidate
    candidate = _extract_email_from_memory_context(messages)
    if _validate(candidate):
        return candidate
    candidate = _derive_from_bearer(request)
    if _validate(candidate):
        return candidate
    return _session_fingerprint(request)
