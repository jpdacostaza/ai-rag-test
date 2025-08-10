"""Tests for memory hit/miss and latency metrics instrumentation."""
import pytest


class DummyProvider:
    provider_type = "dummy"

    def __init__(self, results):
        self._results = results

    async def store_memory(self, entry):  # pragma: no cover - not used here
        return True

    async def get_memories(self, query):
        return self._results

    async def delete_memory(self, user_id: str, memory_id: str):  # pragma: no cover
        return True

    async def get_stats(self, user_id: str):  # pragma: no cover
        return None

    async def health_check(self):  # pragma: no cover
        return True


@pytest.mark.asyncio
async def test_memory_metrics_hit_and_miss():
    from services.memory_service import MemoryService, MemoryEntry, MemoryMetadata
    from core.metrics import (
        METRICS_ENABLED,
        memory_hits_total,
        memory_misses_total,
        memory_retrieval_latency_seconds,
    )

    if not METRICS_ENABLED:
        pytest.skip("Metrics disabled")

    def get_counter_value(counter):
        samples = list(counter.collect())[0].samples
        return {(s.labels.get("provider")): s.value for s in samples if s.name == counter._name}

    def get_histogram_count(hist):
        samples = list(hist.collect())[0].samples
        for s in samples:
            if s.name.endswith("_count"):
                return s.value
        return 0

    hits_before = get_counter_value(memory_hits_total)
    misses_before = get_counter_value(memory_misses_total)
    hist_before = get_histogram_count(memory_retrieval_latency_seconds)

    svc_miss = MemoryService(DummyProvider([]))
    await svc_miss.get_memories("user1", "query")

    meta = MemoryMetadata(user_id="user1", timestamp="now", source="test")
    entry = MemoryEntry(content="test", metadata=meta)
    svc_hit = MemoryService(DummyProvider([entry]))
    await svc_hit.get_memories("user1", "query")

    hits_after = get_counter_value(memory_hits_total)
    misses_after = get_counter_value(memory_misses_total)
    hist_after = get_histogram_count(memory_retrieval_latency_seconds)

    assert hits_after.get("dummy", 0) == hits_before.get("dummy", 0) + 1
    assert misses_after.get("dummy", 0) == misses_before.get("dummy", 0) + 1
    assert hist_after == hist_before + 2
