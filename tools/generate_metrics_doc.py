"""Generate METRICS.md by introspecting metric objects.

Run: python tools/generate_metrics_doc.py > METRICS.md
"""
from __future__ import annotations
import inspect
import sys
import os

try:
    import prometheus_client  # type: ignore
except Exception:
    print("prometheus_client not installed; cannot introspect metrics", file=sys.stderr)
    sys.exit(1)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core import metrics as core_metrics  # type: ignore
from utilities import web_search_metrics  # type: ignore

IGNORE = set([
    'METRICS_ENABLED', 'generate_latest', 'CONTENT_TYPE_LATEST'
])

SECTIONS = []

def collect(module, title: str):
    items = []
    for name in dir(module):
        if name.startswith('_') or name in IGNORE:
            continue
        obj = getattr(module, name)
        # Prometheus metric objects have '_type' attribute (Counter/Histogram/Gauge)
        if hasattr(obj, '_type') and name.islower():  # heuristic: skip exported class names
            mtype = getattr(obj, '_type', 'unknown')
            # Description stored in ._documentation for counters/histograms
            desc = getattr(obj, '_documentation', '') or ''
            # Label names
            labels = getattr(obj, '_labelnames', ())
            items.append((name, mtype, desc, labels))
    if items:
        SECTIONS.append((title, sorted(items)))

collect(core_metrics, 'Core Metrics')
collect(web_search_metrics, 'Web Search Metrics')

print('# Metrics Reference\n')
print('Auto-generated metric listing. Do not edit manually; regenerate when metrics change.\n')
for title, items in SECTIONS:
    print(f'## {title}\n')
    for name, mtype, desc, labels in items:
        label_str = ', '.join(labels) if labels else '—'
        print(f'- **{name}** ({mtype}) labels: {label_str}\n  - {desc}')
    print()
