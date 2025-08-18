# Utilities

Error handling
- `utilities/simple_error_handling.py`: lightweight decorators for API/service ops
- `utilities/error_patterns.py` (+ migration guides/examples): more complex system still present; some modules use it

Infra helpers
- `utilities/circuit_breaker.py`: LLM breaker used in core
- `utilities/connection_factory.py`, `database_types.py`: connection mgmt
- `utilities/cache_manager.py`: in-memory cache with metrics hooks

Web search & metrics
- `utilities/enhanced_web_search.py`, `web_search_metrics.py`, `smart_web_search_trigger.py`

Others
- `utilities/feature_registry.py`, `async_context_managers.py`, `performance_monitoring.py`, `watchdog.py`, `validation.py`
