import pytest
from services.memory_service import MemoryEntry, MemoryMetadata, MemoryService

class DummyProvider:
    provider_type = "dummy"
    async def store_memory(self, entry): return True
    async def get_memories(self, query): return []
    async def delete_memory(self, user_id, memory_id): return True
    async def get_stats(self, user_id): return None
    async def health_check(self): return True

@pytest.mark.asyncio
async def test_memory_formatting_sanitizes_script():
    svc = MemoryService(DummyProvider())
    mem = MemoryEntry(content="<script>alert('x')</script>Important note", metadata=MemoryMetadata(user_id="u", timestamp="t", source="s", importance=0.5, context=""))
    formatted = svc.format_memories_for_injection([mem])
    assert '<script>' not in formatted.lower()
    assert 'alert' not in formatted.lower() or 'script' not in formatted.lower()
    assert 'Important note' in formatted
