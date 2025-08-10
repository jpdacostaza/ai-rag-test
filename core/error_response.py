"""Standard error response builder to ensure consistent error envelopes.

Schema:
{
  "error": {
     "code": str,            # machine-readable code (snake_case)
     "message": str,         # human-readable summary
     "details": {...?},      # optional structured extra context
     "correlation_id": str?, # if available in context
     "retryable": bool       # hint for clients
  }
}
"""
from typing import Any, Dict, Optional
from starlette.responses import JSONResponse
import contextvars

_correlation_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("corr_id", default=None)

def set_correlation_for_error(cid: str):  # simple hook if not already set elsewhere
    try:
        _correlation_var.set(cid)
    except Exception:
        pass

def build_error(code: str, message: str, *, status: int = 400, details: Optional[Dict[str, Any]] = None,
                retryable: bool = False, correlation_id: Optional[str] = None) -> JSONResponse:
    if correlation_id is None:
        try:
            correlation_id = _correlation_var.get()
        except Exception:
            correlation_id = None
    payload: Dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
        }
    }
    if details:
        payload["error"]["details"] = details
    if correlation_id:
        payload["error"]["correlation_id"] = correlation_id
    return JSONResponse(status_code=status, content=payload)

__all__ = ["build_error", "set_correlation_for_error"]
