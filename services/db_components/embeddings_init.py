"""Embedding initialization component extracted from DatabaseManager.

Handles provider selection (huggingface / ollama) and provider abstraction initialization.
"""
from __future__ import annotations
import asyncio
from typing import Optional, Any
from core.unified_logging import log_service_status

async def initialize_huggingface_embedding(model_name: str):
    try:
        from config.config_unified import SENTENCE_TRANSFORMERS_HOME, EMBEDDING_PROVIDER, OLLAMA_BASE_URL
        import os
        os.environ["SENTENCE_TRANSFORMERS_HOME"] = SENTENCE_TRANSFORMERS_HOME
        os.makedirs(SENTENCE_TRANSFORMERS_HOME, exist_ok=True)
        log_service_status("embeddings", "info", f" Loading/downloading model '{model_name}' (HF)")

        def load_or_download_model():
            from sentence_transformers import SentenceTransformer
            try:
                return SentenceTransformer(model_name, cache_folder=SENTENCE_TRANSFORMERS_HOME)
            except Exception as e:
                log_service_status("embeddings", "error", f"Failed to load/download model '{model_name}': {e}")
                return None

        model = await asyncio.to_thread(load_or_download_model)
        if model is None:
            return None
        # Initialize provider abstraction
        try:
            from services.embedding_provider import initialize_embedding_provider
            await initialize_embedding_provider(model, EMBEDDING_PROVIDER.lower(), model_name, OLLAMA_BASE_URL)
        except Exception as e:  # pragma: no cover
            log_service_status("embeddings", "warning", f"Provider init failed: {e}")
        return model
    except Exception as e:
        log_service_status("embeddings", "error", f"HF init error: {e}")
        return None

async def initialize_ollama_embedding(model_name: str):
    try:
        from config.config_unified import OLLAMA_BASE_URL, EMBEDDING_PROVIDER
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            tags = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if tags.status_code == 200:
                models = tags.json().get("models", [])
                names = [m.get("name", "").split(":")[0] for m in models]
                if model_name in names:
                    try:
                        from services.embedding_provider import initialize_embedding_provider
                        await initialize_embedding_provider(model_name, EMBEDDING_PROVIDER.lower(), model_name, OLLAMA_BASE_URL)  # type: ignore
                    except Exception as e:  # pragma: no cover
                        log_service_status("embeddings", "warning", f"Provider init failed: {e}")
                    return model_name
            # Pull if missing
            pull = await client.post(f"{OLLAMA_BASE_URL}/api/pull", json={"name": model_name}, timeout=300.0)
            if pull.status_code == 200:
                verify = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                if verify.status_code == 200:
                    models = verify.json().get("models", [])
                    if model_name in [m.get("name", "").split(":")[0] for m in models]:
                        try:
                            from services.embedding_provider import initialize_embedding_provider
                            await initialize_embedding_provider(model_name, EMBEDDING_PROVIDER.lower(), model_name, OLLAMA_BASE_URL)  # type: ignore
                        except Exception as e:  # pragma: no cover
                            log_service_status("embeddings", "warning", f"Provider init failed: {e}")
                        return model_name
        log_service_status("embeddings", "error", f"Ollama embedding model '{model_name}' unavailable")
        return None
    except Exception as e:
        log_service_status("embeddings", "error", f"Ollama init error: {e}")
        return None

async def initialize_embedding(model_name: str, provider: str):
    provider = provider.lower()
    if provider == "huggingface":
        return await initialize_huggingface_embedding(model_name)
    if provider == "ollama":
        return await initialize_ollama_embedding(model_name)
    log_service_status("embeddings", "error", f"Unknown embedding provider '{provider}'")
    return None
