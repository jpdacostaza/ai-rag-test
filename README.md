# OpenWebUI Enhanced Memory System Backend - RAG Architecture

A comprehensive backend system for OpenWebUI with advanced RAG (Retrieval-Augmented Generation) dual-database memory capabilities using Redis and ChromaDB for persistent, user-isolated, and semantically searchable memory.

## 🚀 Quick Start

```bash
# 1. Start all services with RAG architecture
docker-compose up -d

# 2. Import memory filter to OpenWebUI
./scripts/import/import_memory_function.ps1

# 3. Test the RAG memory system
./tests/memory/test_memory_simple.ps1

# 4. Check system status
./tests/memory/memory_system_status.ps1
```

### 🍊 Orange Pi 5 Plus Optimized
This project includes **zero-configuration optimizations** for Orange Pi 5 Plus ARM64 platforms:
- ✅ **CPU Affinity**: Ollama dedicated to cores 1-7, system on core 0
- ✅ **Memory Management**: 6GB allocation with swap disabled for consistent performance  
- ✅ **ARM64 Tuning**: Optimized threading, memory limits, and request handling
- ✅ **Thermal Aware**: Extended timeouts and resource management for ARM SoCs

**📖 Full optimization guide**: [Orange Pi 5 Plus Setup](docs/ORANGE_PI_5_PLUS_OPTIMIZATION.md)

## 📋 System Overview - RAG Dual-Database Architecture

### Core Components
- **Memory API** (`memory/api/enhanced_memory_api.py`) - RAG dual-database backend (Redis + ChromaDB)
- **Memory Functions** (`memory/functions/memory_filter_function.py`) - OpenWebUI integration with RAG
- **Main API** (`main.py`) - OpenAI-compatible endpoints with RAG support
- **Docker Services** - Redis, ChromaDB, Memory API, OpenWebUI with RAG configuration

### Key Features - RAG Enhancement
- ✅ **RAG Dual-Database** - Redis (short-term) + ChromaDB (long-term) storage
- ✅ **Importance-Based Routing** - Automatic storage strategy selection
- ✅ **Explicit Memory Processing** - Handle "remember this" commands
- ✅ **Semantic Search** - ChromaDB embeddings with retrieval augmentation
- ✅ **User Isolation** - Private memory per user with cross-session persistence
- ✅ **Cross-Chat Memory** - Remember across sessions with context augmentation
- ✅ **Automatic Injection** - Filter-based context injection with RAG
- ✅ **Fallback Retrieval** - Always provides relevant context with semantic search
- ✅ **Network Resilience** - Multi-host Docker networking with fallback strategies
 - ✅ **Unified User Identity Resolution** - Centralized resolution logic (services/user_identity.py) ensuring consistent user mapping across endpoints and pipelines
 - ✅ **Correlation IDs** - Automatic per-request correlation IDs with header propagation (X-Correlation-ID) for traceability
 - ✅ **Rate Limiting** - Per-user token bucket with Redis or in-memory fallback
 - ✅ **Circuit Breaker** - LLM call protection with automatic open / half-open / close transitions
 - ✅ **Observability Metrics** - Prometheus counters & histograms for LLM, embeddings, Redis, Chroma, rate limiting, streaming
 - ✅ **Streaming Reliability** - Heartbeat events + session latency metrics
 - ✅ **Embedding Provider Abstraction** - Pluggable (HuggingFace / Ollama / No-op) with latency/error metrics
 - ✅ **Memory Safety** - Sanitization, truncation, and explicit <BEGIN/END_MEMORY_CONTEXT> delimiters

## 📁 Directory Structure

```
backend/
├── 📄 Core Application Files
│   ├── main.py                     # Main application
│   ├── memory/
│   │   ├── api/
│   │   │   ├── enhanced_memory_api.py   # Memory API (Redis + ChromaDB)
│   │   │   └── main.py                  # Memory API main entry
│   │   └── functions/
│   │       ├── memory_filter_function.py # OpenWebUI memory function
│   │       └── enhanced_memory_function.py # Enhanced memory function
│   └── docker-compose.yml          # Service orchestration
│
├── 📚 docs/                        # Documentation
│   ├── guides/                     # Setup & usage guides
│   ├── status/                     # Project status reports
│   └── *.md                        # Analysis & summaries
│
├── 🧪 tests/                       # Testing Suite
│   ├── memory/                     # Memory system tests
│   └── integration/                # Integration tests
│
├── 📜 scripts/                     # Utility Scripts
│   ├── import/                     # Function import scripts
│   └── memory/                     # Memory system scripts
│
├── 📦 archive/                     # Archived files
├── 🔧 Core modules (*.py)          # Application modules
└── 🏗️ Infrastructure               # handlers/, pipelines/, routes/, etc.
```

## 🧪 Testing

### Memory System Tests
```bash
# Quick functionality check
./tests/memory/test_memory_simple.ps1

# Comprehensive validation  
./tests/memory/test_memory_validation.ps1

# Full test suite
./tests/memory/test_memory_system_comprehensive.ps1

# Interactive demo
./tests/memory/demo_memory_system.ps1

# System status
./tests/memory/memory_system_status.ps1
```

## 🔧 Management

### Memory Filter Management
```bash
# Import memory filter to OpenWebUI
./scripts/import/import_memory_function.ps1

# Update existing filter
./scripts/import/update_memory_filter.ps1

# Debug import issues
./scripts/import/import_function_debug.ps1
```

### System Management
```bash
# Start memory system
./scripts/memory/start-memory-system.ps1

# Check Docker services
docker-compose ps

# View logs
docker-compose logs memory_api
docker-compose logs openwebui
```

## 📚 Documentation

### Quick Reference
- **Setup Guide**: `docs/guides/MEMORY_PIPELINE_SETUP_GUIDE.md`
- **Usage Guide**: `docs/guides/MEMORY_PIPELINE_USAGE_GUIDE.md`
- **Test Plan**: `docs/guides/MEMORY_PIPELINE_TEST_PLAN.md`

### Status Reports
- **Success Report**: `docs/MEMORY_SYSTEM_SUCCESS_REPORT.md`
- **Project Status**: `docs/status/`

### Detailed Structure
See `README_STRUCTURE.md` for complete directory documentation.

## 🎯 Memory System Workflow

1. **User sends message** → OpenWebUI receives
2. **Memory Filter activated** → Retrieves relevant memories
3. **Context injection** → Memories added to system message
4. **LLM processes** → Generates response with memory context
5. **Response stored** → New interaction saved for future recall
6. **Cross-chat persistence** → Available in all future conversations

## 🔧 Configuration

### Environment Variables
```bash
REDIS_URL=redis://localhost:6379
CHROMADB_URL=http://localhost:8002
MEMORY_API_URL=http://localhost:8000
OPENWEBUI_URL=http://localhost:3000
# Optional logging / tracing
LOG_LEVEL=INFO
LOG_STYLE=human            # or json
 # (Legacy human_logging_old removed; unified logging always used)

# Correlation / request tracing
ENABLE_CORRELATION_ID=true  # (middleware auto-enabled; header X-Correlation-ID respected)

# Embeddings
EMBEDDING_PROVIDER=ollama           # or huggingface
EMBEDDING_MODEL=nomic-embed-text    # model name per provider
DISABLE_EMBEDDINGS=false            # set true to start without embeddings
CHROMA_COLLECTION=default           # vector collection name

# Circuit Breaker (LLM)
LLM_BREAKER_FAILURE_THRESHOLD=3     # consecutive failures to open breaker
LLM_BREAKER_RESET_TIMEOUT=20        # seconds before half-open trial

# Rate Limiting (middleware header override for tests: x-test-rate-limit)
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_SCOPE=user            # user | ip | both (composite)

# Memory provider selection (default pipeline). Options: pipeline|api|database|local
MEMORY_PROVIDER=pipeline

# Web Search (ddgs-only)
WEB_SEARCH_CACHE_TTL=300                 # Seconds for in-memory/Redis cached results (min 30)
WEB_SEARCH_DEFAULT_MAX_RESULTS=5         # Default result count (1-25) if not specified by caller
WEB_SEARCH_MAX_CACHE_ENTRIES=256         # Bounded in-memory LRU cache size (32-4096)

# (Optional) Prometheus scraped via /metrics endpoint (enabled automatically when prometheus_client installed)
```

### Metrics Overview (Prometheus Names)
Counters:
- chat_requests_total{stream}
- memory_injections_total
- memory_hits_total{provider}
- memory_misses_total{provider}
- streaming_heartbeats_total
- llm_request_errors_total{phase}
- embedding_errors_total{provider}
- rate_limit_blocked_total
- redis_operation_errors_total{operation}
- chroma_operation_errors_total{operation}
- circuit_breaker_state_total{name,state}
- gateway_requests_total{service,method,status}
- web_search_cache_evictions_total
- web_search_cache_size (Gauge)
	(Rate limiting scope exposed via X-RateLimit-Scope response header)

Histograms:
- llm_request_latency_seconds
- llm_stream_latency_seconds
- embedding_latency_seconds{provider}
- memory_retrieval_latency_seconds{provider}
- redis_operation_latency_seconds{operation}
- chroma_operation_latency_seconds{operation}
- gateway_request_latency_seconds{service,method}

Access metrics: GET /metrics (returns 'metrics_disabled' if Prometheus lib absent)

Auto-generated reference: run `python tools/generate_metrics_doc.py > METRICS.md` (requires prometheus_client) to build a full list.

### Standard Error Envelope
All errors (middleware, validation, internal) are normalized to:
```json
{
	"error": {
		"code": "rate_limited",
		"message": "Too many requests, slow down",
		"details": {"retry_after_seconds": 60},
		"retryable": true,
		"correlation_id": "..." // when available
	}
}
```

### Version Endpoint
`GET /version` returns build metadata:
```json
{ "build": { "version": "0.0.0", "commit": "abc123", "build_time": "2025-08-10T00:00:00Z" } }
```

### Memory Provider Selection Precedence
The active memory provider is resolved in this order:
1. Explicit argument passed internally when creating service (tests/internal only)
2. Environment variable MEMORY_PROVIDER (api|database|pipeline|local)
3. Default fallback: pipeline

Invalid or unsupported values silently fall back to pipeline. Active provider surfaced via readiness endpoint `memory_provider` field and metric `memory_provider_active_total{provider}`.

### Bulk Memory Query Endpoint
POST /api/memory/bulk_query
Request example:
```json
{ "user_id": "user123", "queries": ["project status", "memory design"], "limit": 5 }
```
Response shape:
```json
{ "success": true, "query_count": 2, "results": { "project status": { "success": true, "memories": [], "total_count": 0 } } }
```
Each query runs concurrently; failures isolated per key (success:false with error field).

### Gateway Correlation & Security
- X-Correlation-ID automatically generated/passed through (FastAPI + aiohttp gateway)
- Rate limiting responses include X-RateLimit-Limit / Remaining / Reset when allowed
- CSP hardened: dynamic connect-src (self + configured service hosts) and optional nonce (enable with CSP_NONCE_ENABLED=true)
- Security headers: HSTS, X-Frame-Options, X-Content-Type-Options, Permissions-Policy, Referrer-Policy, CSP

### Web Search Integration (DDGS Only)
- Single dependency: `ddgs` (legacy `duckduckgo-search` removed)
- Strategies: primary, news (year-aware), recent, current
- Cache layers: in-process (TTL configurable) + optional Redis (auto-detected)
- Override TTL / default results via `WEB_SEARCH_CACHE_TTL` / `WEB_SEARCH_DEFAULT_MAX_RESULTS`
- Import surface:
	- Programmatic: `from utilities.enhanced_web_search import search_web`
	- Pipeline: `from pipelines.enhanced_web_search_pipeline import Pipeline`
- Metrics (if enabled): WEB_SEARCH_QUERIES, *_CACHE_HITS/MISSES, *_DURATION, *_RESULTS_ITEMS (exposed via `/metrics` when instrumentation module present)

### Health Endpoints
- GET /health          → aggregated component status + circuit breaker state
- GET /health/detailed  → watchdog + breaker

Breaker field example:
```json
{
	"breaker": { "state": "closed" }
}
```

### Circuit Breaker Behavior
- closed → normal operation
- open (after threshold failures) → 503 for LLM calls
- half_open (after reset timeout) → trial request determines close or reopen

### Memory Safety & Injection
Injected system prompt is wrapped with:
```
<BEGIN_MEMORY_CONTEXT>
	... sanitized memory snippets ...
<END_MEMORY_CONTEXT>
```
Sanitization removes script tags / potentially unsafe patterns and truncates excessive memory payloads.

### Embedding Provider Abstraction
Resolved dynamically based on EMBEDDING_PROVIDER. Latency & error metrics collected per provider. Set DISABLE_EMBEDDINGS=true to skip initialization gracefully.

### Memory Filter Settings
- **Threshold**: 0.3 (semantic similarity)
- **Max memories**: 3 per retrieval
- **Fallback**: Empty query if no matches
- **Debug logging**: Enabled

## 🚨 Troubleshooting

### Common Issues
1. **Filter not working**: Check OpenWebUI functions list
2. **No memories**: Verify Redis/ChromaDB connectivity
3. **Import fails**: Use debug import script
4. **Performance issues**: Check service logs
5. **User not recognized**: Confirm client sends one of: body.user.{email|id|username}, X-User-Id header, AUTHENTICATED_USER_ID system message (pipeline), or Authorization Bearer token
6. **Missing correlation ID**: Ensure reverse proxy forwards X-Correlation-ID or allow backend to generate one
7. Legacy logging module removed (core.human_logging_old) – remove any external imports; use core.unified_logging
7. **Breaker always open**: Verify LLM endpoint/model reachable; adjust LLM_BREAKER_FAILURE_THRESHOLD / RESET_TIMEOUT
8. **High Redis / Chroma errors**: Check redis_operation_errors_total / chroma_operation_errors_total metrics for failing operations
9. **Embeddings disabled**: Confirm DISABLE_EMBEDDINGS=false and provider/model names valid
10. **Rate limit unexpected**: Inspect rate_limit_blocked_total and ensure requests include x-user-id

### Debug Commands
```bash
# Check services
docker-compose ps

# Test memory API directly
curl http://localhost:8000/health

# Verify filter installation
./tests/memory/memory_system_status.ps1

# Identity resolver unit tests
pytest -q tests/test_user_identity.py

# Correlation ID middleware tests
pytest -q tests/test_correlation_id.py

# Circuit breaker tests
pytest -q tests/test_circuit_breaker.py

# Health breaker field test
pytest -q tests/test_health_breaker.py
```

## 🎉 Success Indicators

When working correctly, you should see:
- ✅ AI references previous conversations
- ✅ Cross-chat memory persistence
- ✅ Context injection in responses
- ✅ User-specific memory isolation

## 📞 Support

For detailed technical information, see:
- Architecture: `docs/backend_analysis_summary.md`
- Implementation: `docs/MEMORY_SYSTEM_SUCCESS_REPORT.md`
- Integration: `docs/CONVERSATION_SYNC_SUMMARY_JUNE27.md`

---

**Status**: ✅ **OPERATIONAL** - Memory system fully functional and production-ready!
