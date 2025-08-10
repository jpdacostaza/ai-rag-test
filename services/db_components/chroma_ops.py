"""ChromaDB operation helpers extracted from DatabaseManager."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from core.unified_logging import log_service_status
from core.metrics import (
    METRICS_ENABLED,
    chroma_operation_latency_seconds,
    chroma_operation_errors_total,
)

async def query_collection(
    collection,
    get_embedding,
    query_text: str,
    n_results: int = 5,
) -> Optional[Dict[str, Any]]:
    """Query a ChromaDB collection with latency/error instrumentation."""
    if not collection:
        log_service_status("chromadb", "error", "ChromaDB collection not available")
        return None
    start = time.time()
    try:
        query_embedding = await get_embedding(query_text)
        if query_embedding is None:
            return None
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        if METRICS_ENABLED:
            chroma_operation_latency_seconds.labels(operation="query").observe(time.time() - start)
        return results
    except Exception as e:  # pragma: no cover
        log_service_status("chromadb", "error", f"Error querying chromadb: {e}")
        if METRICS_ENABLED:
            chroma_operation_errors_total.labels(operation="query").inc()
        return None
