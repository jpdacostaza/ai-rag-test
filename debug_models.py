#!/usr/bin/env python3
import asyncio
import os
import sys

from model_manager import _model_cache
from model_manager import refresh_model_cache

"""

Debug script to trace where OpenAI models are coming from
"""

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def debug_models():
    print("=== INITIAL CACHE STATE ===")
    print("Cache data: {_model_cache['data']}")
    print("Last updated: {_model_cache['last_updated']}")
    print("TTL: {_model_cache['ttl']}")

    print("\n=== AFTER REFRESH ===")
    await refresh_model_cache(force=True)
    print("Models found: {len(_model_cache['data'])}")
    for i, model in enumerate(_model_cache["data"]):
        print("  {i+1}. {model['id']} (owned_by: {model.get('owned_by', 'unknown')})")

    print("\nCache last updated: {_model_cache['last_updated']}")


if __name__ == "__main__":
    asyncio.run(debug_models())
