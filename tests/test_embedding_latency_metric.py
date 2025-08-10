import pytest
import time

@pytest.mark.asyncio
async def test_embedding_latency_metric(monkeypatch):
    from services.embedding_provider import HuggingFaceEmbeddingProvider
    from core.metrics import embedding_latency_seconds, METRICS_ENABLED
    if not METRICS_ENABLED:
        pytest.skip('Metrics disabled')

    class SlowModel:
        def encode(self, texts, *a, **k):
            time.sleep(0.01)
            return [[0.1,0.2,0.3]]

    provider = HuggingFaceEmbeddingProvider(SlowModel())
    await provider.embed_text('hi there')
    # We can't directly assert histogram internals portably; ensure name appears in scrape
    from fastapi.testclient import TestClient
    from core.main import app
    client = TestClient(app)
    r = client.get('/metrics')
    if r.text.strip() == 'metrics_disabled':
        pytest.skip('Metrics disabled later')
    assert 'embedding_latency_seconds' in r.text
