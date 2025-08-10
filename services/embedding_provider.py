"""Embedding Provider Abstraction.

Decouples database manager from concrete embedding backends.
Minimal initial implementation – safely wraps existing logic.

Usage:
    from services.embedding_provider import get_embedding_provider
    provider = get_embedding_provider()
    embedding = await provider.embed_text("hello world")

Design Goals:
- Async interface
- Pluggable backends (huggingface, ollama, noop)
- Graceful degradation (returns None on failure, logs)
"""
from __future__ import annotations
import asyncio
from typing import Optional, List
from core.unified_logging import log_service_status, get_logger
from core.metrics import (
    METRICS_ENABLED,
    embedding_latency_seconds,
    embedding_errors_total,
)

logger = get_logger(__name__)

class BaseEmbeddingProvider:
    name = "base"
    async def embed_text(self, text: str) -> Optional[List[float]]:  # pragma: no cover
        raise NotImplementedError

class NoopEmbeddingProvider(BaseEmbeddingProvider):
    name = "noop"
    async def embed_text(self, text: str) -> Optional[List[float]]:
        return None

class HuggingFaceEmbeddingProvider(BaseEmbeddingProvider):
    name = "huggingface"
    def __init__(self, model):
        self.model = model

    async def embed_text(self, text: str) -> Optional[List[float]]:
        start = asyncio.get_event_loop().time()
        try:
            if not self.model:
                return None
            model_str = str(self.model).lower()
            query_text = f"query: {text}" if "e5-" in model_str else text
            vecs = await asyncio.to_thread(self.model.encode, [query_text], normalize_embeddings=True)
            return vecs[0].tolist() if vecs else None
        except Exception as e:  # pragma: no cover
            log_service_status("EMBEDDINGS", "warning", f"HF embed failed: {e}")
            if METRICS_ENABLED:
                embedding_errors_total.labels(provider=self.name).inc()
            return None
        finally:
            if METRICS_ENABLED:
                embedding_latency_seconds.labels(provider=self.name).observe(
                    asyncio.get_event_loop().time() - start
                )

class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    name = "ollama"
    def __init__(self, model_name: str, base_url: str):
        self.model_name = model_name
        self.base_url = base_url.rstrip('/')

    async def embed_text(self, text: str) -> Optional[List[float]]:
        import httpx
        start = asyncio.get_event_loop().time()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{self.base_url}/api/embeddings", json={"model": self.model_name, "prompt": text})
                if resp.status_code == 200:
                    data = resp.json()
                    emb = data.get("embedding")
                    if emb:
                        return emb
                else:
                    log_service_status("EMBEDDINGS", "warning", f"Ollama embeddings status {resp.status_code}")
                    if METRICS_ENABLED:
                        embedding_errors_total.labels(provider=self.name).inc()
        except Exception as e:  # pragma: no cover
            log_service_status("EMBEDDINGS", "warning", f"Ollama embed failed: {e}")
            if METRICS_ENABLED:
                embedding_errors_total.labels(provider=self.name).inc()
        finally:
            if METRICS_ENABLED:
                embedding_latency_seconds.labels(provider=self.name).observe(
                    asyncio.get_event_loop().time() - start
                )
        return None

# Singleton holder
_embedding_provider: Optional[BaseEmbeddingProvider] = None

async def initialize_embedding_provider(embedding_model_obj, provider_name: str, model_name: str, ollama_url: str):
    global _embedding_provider
    try:
        if provider_name == "huggingface":
            _embedding_provider = HuggingFaceEmbeddingProvider(embedding_model_obj)
        elif provider_name == "ollama":
            _embedding_provider = OllamaEmbeddingProvider(model_name, ollama_url)
        else:
            _embedding_provider = NoopEmbeddingProvider()
        log_service_status("EMBEDDINGS", "info", f"Embedding provider initialized: {_embedding_provider.name}")
    except Exception as e:  # pragma: no cover
        log_service_status("EMBEDDINGS", "warning", f"Failed to init embedding provider: {e}")
        _embedding_provider = NoopEmbeddingProvider()

def get_embedding_provider() -> BaseEmbeddingProvider:
    return _embedding_provider or NoopEmbeddingProvider()
