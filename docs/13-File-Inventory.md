# File Inventory (snapshot)

This is a generated inventory of key files with one-line explanations. For brevity, it focuses on primary modules.

Core (`core/`)
- main.py — FastAPI app composition and `/v1/chat/completions`
- startup.py — Phased, idempotent startup lifecycle
- enhanced_api_gateway.py — aiohttp-based gateway proxy with LB/CB/caching
- unified_logging.py — JSON/human logging with correlation IDs
- metrics.py — Prometheus metrics definitions and fallbacks
- error_handler.py — legacy helper wrappers; moving toward simple_error_handling
- error_response.py — standardized error envelope
- security.py — input validation, headers, CORS/trusted hosts
- metrics_guard.py — metrics cardinality guard
- config_validation.py — config validation helpers
- auth.py — authentication helpers

Routes (`routes/`)
- chat.py — Legacy/autonomous chat handlers leveraging services
- models.py — `/v1/models` listing via Ollama with cache and a Mistral workaround
- memory.py — REST endpoints for memory health/store/query/bulk/stats
- upload.py — Document ingestion, search, JSON helpers
- tools.py — Tools listing and enhanced web search endpoint
- health.py — health/readiness/liveness and storage/alerts
- gateway.py — Gateway health/status/config
- debug.py — Debug stats and endpoint listing

Services (`services/`)
- llm_service.py — LLM calls (Ollama/OpenAI) + streaming + embeddings
- database_manager.py — Redis/Chroma/embeddings orchestration (to be refactored)
- streaming_service.py — streaming session metadata lifecycle
- tool_service.py — tool detection/execution
- user_profiles.py — lightweight profile manager
- auth_validator.py — unified user-ID extraction/validation
- user_identity.py — additional identity helpers used by core
- redis_service.py — async Redis wrapper
- vector_service.py — ChromaDB wrapper
- model_manager.py — model cache/ops; overlaps with routes/models.py
- model_preloader.py — preloads models
- memory_service.py, storage_manager.py, embedding_provider.py, chat routers — supporting services

Middleware (`middleware/`)
- performance_middleware.py — request timing and system snapshots
- rate_limit_middleware.py — token-bucket with Redis fallback
- security_middleware.py — gateway IP/rate/auth/CB/headers/validation

Config (`config/`)
- config_unified.py — singleton config and env aliases
- gateway_config.py, pipeline_config.py, autonomous_config.py — service configs
- unified_prompt*.json — system prompts
- memory_* and weather_* configs — RAG/tools settings
- pyproject.toml, mypy.ini — tooling configs

Pipelines (`pipelines/`)
- enhanced_memory_pipeline.py — memory context injector
- anti_hallucination_pipeline.py — hallucination guardrails
- health_check.py — pipeline health
- valves.json — feature toggles

Utilities (`utilities/`)
- simple_error_handling.py — lightweight decorators (preferred)
- error_patterns.py (+ guides) — legacy complex system
- enhanced_web_search.py, web_search_metrics.py — web search utils
- circuit_breaker.py — breaker used for LLM calls
- cache_manager.py, connection_factory.py — infra helpers

Docs (`docs/`)
- ARCHITECTURE_OVERVIEW.md — high-level map and issues
- AUTONOMOUS_INTEGRATION_GUIDE.md, TESTING_AND_METRICS_EXPLAINED.md, etc.

Scripts (`scripts/`)
- **monitoring/** — Real-time monitoring and health check scripts
  - realtime_monitor.py — Real-time duplicate detection monitor with database watching
- **setup/** — Initial setup and configuration scripts  
  - auto_deduplication_setup.py — Auto-deduplication integration setup and hooks
  - copy_prompt_to_functions.py — Copy unified prompt for cross-container filter access
- **maintenance/** — Maintenance and cleanup scripts
  - activate_cleanup.py — Manual duplicate cleanup activation (destructive operations)
- add-model.sh, api_function_installer.py — Legacy model management and function installation

Memory/API (`memory/`)
- Separate memory API and functions for advanced scenarios

Functions (`functions/`)
- Tools (weather), filters (memory/web search) used by pipelines and tool service
