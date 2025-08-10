# Metrics Reference

Auto-generated metric listing. Do not edit manually; regenerate when metrics change.

## Core Metrics

- **chat_requests_total** (counter) labels: stream
  - Total chat requests
- **chroma_operation_errors_total** (counter) labels: operation
  - Total ChromaDB operation errors
- **chroma_operation_latency_seconds** (histogram) labels: operation
  - Latency of ChromaDB operations in seconds
- **embedding_errors_total** (counter) labels: provider
  - Total embedding errors
- **embedding_latency_seconds** (histogram) labels: provider
  - Latency of embedding generation in seconds
- **gateway_request_latency_seconds** (histogram) labels: service, method
  - API gateway request latency in seconds
- **gateway_requests_total** (counter) labels: service, method, status
  - Total API gateway requests
- **llm_request_errors_total** (counter) labels: phase
  - Total LLM call errors
- **llm_request_latency_seconds** (histogram) labels: —
  - Latency of non-stream LLM calls in seconds
- **llm_stream_latency_seconds** (histogram) labels: —
  - Total latency of streaming LLM sessions in seconds
- **memory_hits_total** (counter) labels: provider
  - Total memory retrieval operations returning >=1 result
- **memory_injections_total** (counter) labels: —
  - Total times memory context injected
- **memory_misses_total** (counter) labels: provider
  - Total memory retrieval operations returning 0 results
- **memory_provider_active** (counter) labels: provider
  - Indicator counter incremented once at startup for the active memory provider
- **memory_provider_health** (counter) labels: provider, status
  - Total memory provider health checks (label status=success|failure)
- **memory_retrieval_latency_seconds** (histogram) labels: provider
  - Latency of memory retrieval operations in seconds
- **rate_limit_blocked_total** (counter) labels: —
  - Total requests blocked by rate limiting
- **redis_operation_errors_total** (counter) labels: operation
  - Total Redis operation errors
- **redis_operation_latency_seconds** (histogram) labels: operation
  - Latency of Redis operations in seconds
- **streaming_heartbeats_total** (counter) labels: —
  - Heartbeat events sent

