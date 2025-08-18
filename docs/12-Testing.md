# Testing

Overview
- Tests cover environment validation, memory degraded mode, tools listing, gateway metrics, circuit breaker, embeddings latency, web search, and more.

Running tests
- Use your Python test runner (pytest is configured via `pytest.ini`).

What’s covered
- Health and gateway metrics
- Memory queries (bulk and single)
- Circuit breaker behavior
- Web search pipeline smoke tests
- Unicode, fixes verification

Recommendations
- Add unit tests for `services/database_manager.py` refactor
- Add tests for unified `/v1/models` endpoint and upload semantics
