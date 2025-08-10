"""Micro-benchmark to estimate Prometheus metrics overhead.

Measures time per operation for Counter.inc() and Histogram.observe() vs no-op equivalents.
Run directly: python scripts/metrics_overhead_benchmark.py
"""
from __future__ import annotations
import math
from time import perf_counter

TRY_IMPORT_ERROR = None
try:
    from prometheus_client import Counter, Histogram  # type: ignore
    PROM_ENABLED = True
except Exception as e:  # pragma: no cover
    PROM_ENABLED = False
    TRY_IMPORT_ERROR = e

OPS = 100_000  # adjust if needed

class NoOpCounter:
    def labels(self, *_, **__):
        return self
    def inc(self, *_ , **__):
        return None

class NoOpHistogram:
    def labels(self, *_, **__):
        return self
    def observe(self, *_):
        return None

results = []

if PROM_ENABLED:
    counter = Counter("bench_counter_total", "Benchmark counter", ["kind"])
    hist = Histogram("bench_hist_seconds", "Benchmark histogram", ["kind"])
    c = counter.labels("test")
    h = hist.labels("test")

    t0 = perf_counter()
    for _ in range(OPS):
        c.inc()
    t1 = perf_counter()

    for i in range(OPS):
        h.observe(i % 10)
    t2 = perf_counter()

    counter_time = (t1 - t0) / OPS * 1e6  # microseconds per op
    hist_time = (t2 - t1) / OPS * 1e6
    results.append(("prometheus_counter_inc_us", counter_time))
    results.append(("prometheus_histogram_observe_us", hist_time))
else:
    results.append(("prometheus_unavailable", -1))

# No-op baseline
noop_c = NoOpCounter().labels("test")
noop_h = NoOpHistogram().labels("test")

t3 = perf_counter()
for _ in range(OPS):
    noop_c.inc()
t4 = perf_counter()
for _ in range(OPS):
    noop_h.observe(1)
t5 = perf_counter()

noop_counter_time = (t4 - t3) / OPS * 1e6
noop_hist_time = (t5 - t4) / OPS * 1e6
results.append(("noop_counter_inc_us", noop_counter_time))
results.append(("noop_histogram_observe_us", noop_hist_time))

# Pretty print
width = max(len(k) for k, _ in results)
print("Metrics Overhead Benchmark (ops = %d)" % OPS)
if not PROM_ENABLED:
    print(f"Prometheus client not available: {TRY_IMPORT_ERROR}")
for k, v in results:
    if v < 0:
        print(f"{k.ljust(width)} : N/A")
    else:
        print(f"{k.ljust(width)} : {v:8.3f} us/op")

if PROM_ENABLED:
    prom_ct = dict(results).get("prometheus_counter_inc_us", 0)
    noop_ct = dict(results).get("noop_counter_inc_us", 1)
    overhead_factor = prom_ct / noop_ct if noop_ct else math.nan
    print(f"Approx counter overhead factor vs no-op: {overhead_factor:0.2f}x")
