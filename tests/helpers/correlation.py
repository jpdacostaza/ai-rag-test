"""Test helper for injecting simple correlation ID middleware into FastAPI test apps."""
import uuid


def install_test_correlation_middleware(app):
    from starlette.middleware.base import BaseHTTPMiddleware

    class _TestCorrelation(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            cid = request.headers.get('x-correlation-id') or str(uuid.uuid4())
            response = await call_next(request)
            response.headers.setdefault('X-Correlation-ID', cid)
            return response

    app.add_middleware(_TestCorrelation)
    return app

__all__ = ["install_test_correlation_middleware"]
