import asyncio
import os
import sys

from model_manager import _model_cache
from model_manager import refresh_model_cache

os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

sys.path.append(".")


async def force_refresh_and_show():
    print("Starting forced refresh...")
    await refresh_model_cache(force=True)
    print(f'Models found: {len(_model_cache["data"])}')
    for model in _model_cache["data"]:
        print(f'  - {model["id"]}')


asyncio.run(force_refresh_and_show())
