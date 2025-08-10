"""Prometheus metrics instrumentation for web search subsystem.

Additions:
 - WEB_SEARCH_CACHE_SIZE gauge to track current in-memory LRU cache size.
"""
try:
    from prometheus_client import Counter, Histogram, Gauge
except Exception:  # Library optional; provide dummies
    class _Dummy:
        def labels(self, *_, **__): return self
        def inc(self, *_a, **_k): pass
        def observe(self, *_a, **_k): pass
        def set(self, *_a, **_k): pass
    Counter = Histogram = Gauge = lambda *a, **k: _Dummy()  # type: ignore

WEB_SEARCH_QUERIES = Counter(
    "web_search_queries_total", "Total web search queries (before cache evaluation)")
WEB_SEARCH_CACHE_HITS = Counter(
    "web_search_cache_hits_total", "Number of in-memory cache hits")
WEB_SEARCH_CACHE_MISSES = Counter(
    "web_search_cache_misses_total", "Number of in-memory cache misses")
WEB_SEARCH_REDIS_HITS = Counter(
    "web_search_redis_hits_total", "Number of Redis cache hits")
WEB_SEARCH_REDIS_MISSES = Counter(
    "web_search_redis_misses_total", "Number of Redis cache misses")
WEB_SEARCH_RESULTS_ITEMS = Histogram(
    "web_search_results_count", "Number of result items returned per query",
    buckets=(0,1,2,3,5,8,13))
WEB_SEARCH_DURATION = Histogram(
    "web_search_duration_seconds", "End-to-end search duration (excluding cache hits)",
    buckets=(0.01,0.05,0.1,0.25,0.5,1,2,3,5,8))

WEB_SEARCH_CACHE_EVICTIONS = Counter(
    "web_search_cache_evictions_total", "Number of in-memory cache evictions (LRU)"
)

WEB_SEARCH_CACHE_SIZE = Gauge(
    "web_search_cache_size", "Current number of entries in the in-memory web search cache"
)

try:
    from prometheus_client import Counter as _Counter
    WEB_SEARCH_TRIGGER_REASONS = _Counter(
        "web_search_trigger_reason_total", "Web search triggers by reason", ["reason"])
except Exception:  # pragma: no cover
    WEB_SEARCH_TRIGGER_REASONS = Counter("web_search_trigger_reason_total", "Web search triggers by reason")

__all__ = [
    "WEB_SEARCH_QUERIES","WEB_SEARCH_CACHE_HITS","WEB_SEARCH_CACHE_MISSES",
    "WEB_SEARCH_REDIS_HITS","WEB_SEARCH_REDIS_MISSES","WEB_SEARCH_RESULTS_ITEMS",
    "WEB_SEARCH_DURATION","WEB_SEARCH_TRIGGER_REASONS","WEB_SEARCH_CACHE_EVICTIONS","WEB_SEARCH_CACHE_SIZE"
]
