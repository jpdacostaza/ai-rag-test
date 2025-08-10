"""Centralized Prometheus metrics definitions.

Provides safe fallbacks when prometheus_client is unavailable to avoid import cycles.
Import metrics from this module instead of redefining in multiple places.
"""
from __future__ import annotations

try:  # pragma: no cover - optional dependency
    from prometheus_client import (
        Counter,
        Histogram,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    METRICS_ENABLED = True

    # Request level metrics
    chat_requests_total = Counter(
        "chat_requests_total", "Total chat requests", ["stream"]
    )

    memory_injections_total = Counter(
        "memory_injections_total", "Total times memory context injected"
    )

    streaming_heartbeats_total = Counter(
        "streaming_heartbeats_total", "Heartbeat events sent"
    )

    # LLM metrics
    llm_request_latency_seconds = Histogram(
        "llm_request_latency_seconds", "Latency of non-stream LLM calls in seconds"
    )
    llm_stream_latency_seconds = Histogram(
        "llm_stream_latency_seconds", "Total latency of streaming LLM sessions in seconds"
    )
    llm_request_errors_total = Counter(
        "llm_request_errors_total", "Total LLM call errors", ["phase"]
    )

    # Embedding metrics
    embedding_latency_seconds = Histogram(
        "embedding_latency_seconds", "Latency of embedding generation in seconds", ["provider"]
    )
    embedding_errors_total = Counter(
        "embedding_errors_total", "Total embedding errors", ["provider"]
    )

    # Memory metrics (new)
    memory_retrieval_latency_seconds = Histogram(
        "memory_retrieval_latency_seconds", "Latency of memory retrieval operations in seconds", ["provider"]
    )
    memory_hits_total = Counter(
        "memory_hits_total", "Total memory retrieval operations returning >=1 result", ["provider"]
    )
    memory_misses_total = Counter(
        "memory_misses_total", "Total memory retrieval operations returning 0 results", ["provider"]
    )
    memory_provider_active = Counter(
        "memory_provider_active_total", "Indicator counter incremented once at startup for the active memory provider", ["provider"]
    )
    memory_provider_health = Counter(
        "memory_provider_health_check_total", "Total memory provider health checks (label status=success|failure)", ["provider", "status"]
    )

    rate_limit_blocked_total = Counter(
        "rate_limit_blocked_total", "Total requests blocked by rate limiting"
    )

    # Redis / Chroma metrics
    redis_operation_latency_seconds = Histogram(
        "redis_operation_latency_seconds", "Latency of Redis operations in seconds", ["operation"]
    )
    redis_operation_errors_total = Counter(
        "redis_operation_errors_total", "Total Redis operation errors", ["operation"]
    )
    chroma_operation_errors_total = Counter(
        "chroma_operation_errors_total", "Total ChromaDB operation errors", ["operation"]
    )
    chroma_operation_latency_seconds = Histogram(
        "chroma_operation_latency_seconds", "Latency of ChromaDB operations in seconds", ["operation"]
    )

    # Gateway metrics (new)
    gateway_requests_total = Counter(
        "gateway_requests_total", "Total API gateway requests", ["service", "method", "status"]
    )
    gateway_request_latency_seconds = Histogram(
        "gateway_request_latency_seconds", "API gateway request latency in seconds", ["service", "method"]
    )

except Exception:  # pragma: no cover
    METRICS_ENABLED = False
    CONTENT_TYPE_LATEST = "text/plain"

    class _DummyMetric:  # noqa: D401 - simple dummy
        def labels(self, *_, **__):
            return self
        def inc(self, *_, **__):
            return None
        def observe(self, *_):
            return None

    def generate_latest():  # type: ignore
        return b""

    chat_requests_total = _DummyMetric()
    memory_injections_total = _DummyMetric()
    streaming_heartbeats_total = _DummyMetric()
    llm_request_latency_seconds = _DummyMetric()
    llm_stream_latency_seconds = _DummyMetric()
    llm_request_errors_total = _DummyMetric()
    embedding_latency_seconds = _DummyMetric()
    embedding_errors_total = _DummyMetric()
    memory_retrieval_latency_seconds = _DummyMetric()
    memory_hits_total = _DummyMetric()
    memory_misses_total = _DummyMetric()
    memory_provider_active = _DummyMetric()
    memory_provider_health = _DummyMetric()
    rate_limit_blocked_total = _DummyMetric()
    redis_operation_latency_seconds = _DummyMetric()
    redis_operation_errors_total = _DummyMetric()
    chroma_operation_errors_total = _DummyMetric()
    chroma_operation_latency_seconds = _DummyMetric()
    gateway_requests_total = _DummyMetric()
    gateway_request_latency_seconds = _DummyMetric()

__all__ = [
    "METRICS_ENABLED",
    "generate_latest",
    "CONTENT_TYPE_LATEST",
    # Counters
    "chat_requests_total",
    "memory_injections_total",
    "streaming_heartbeats_total",
    "llm_request_errors_total",
    "embedding_errors_total",
    "memory_retrieval_latency_seconds",
    "memory_hits_total",
    "memory_misses_total",
    "memory_provider_active",
    "memory_provider_health",
    "rate_limit_blocked_total",
    "redis_operation_latency_seconds",
    "redis_operation_errors_total",
    "chroma_operation_errors_total",
    # Histograms
    "llm_request_latency_seconds",
    "llm_stream_latency_seconds",
    "embedding_latency_seconds",
    "chroma_operation_latency_seconds",
    "gateway_requests_total",
    "gateway_request_latency_seconds",
]
