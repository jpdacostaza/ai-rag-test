#!/usr/bin/env python3
"""
Debug script to trace where OpenAI models are coming from
"""
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_manager import _model_cache, refresh_model_cache

async def debug_models():
    print("=== INITIAL CACHE STATE ===")
    print(f"Cache data: {_model_cache['data']}")
    print(f"Last updated: {_model_cache['last_updated']}")
    print(f"TTL: {_model_cache['ttl']}")
    
    print("\n=== AFTER REFRESH ===")
    await refresh_model_cache(force=True)
    print(f"Models found: {len(_model_cache['data'])}")
    for i, model in enumerate(_model_cache['data']):
        print(f"  {i+1}. {model['id']} (owned_by: {model.get('owned_by', 'unknown')})")
    
    print(f"\nCache last updated: {_model_cache['last_updated']}")

if __name__ == "__main__":
    asyncio.run(debug_models())
