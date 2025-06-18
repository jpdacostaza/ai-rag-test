from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import os
import shutil
import requests

router = APIRouter(prefix="/models", tags=["Model Management"])

# Example model directories (customize as needed)
OLLAMA_MODEL_DIR = os.path.abspath("storage/ollama/models")
CUSTOM_MODEL_DIR = os.path.abspath("storage/models")

# Helper to list models in a directory
def list_models_in_dir(directory: str) -> List[str]:
    if not os.path.exists(directory):
        return []
    return [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f)) or os.path.isfile(os.path.join(directory, f))]

@router.get("/", response_model=List[str])
def list_models():
    """List all available models from all sources."""
    ollama_models = list_models_in_dir(OLLAMA_MODEL_DIR)
    custom_models = list_models_in_dir(CUSTOM_MODEL_DIR)
    return list(set(ollama_models + custom_models))

@router.get("/{model_name}")
def get_model_details(model_name: str):
    """Get details about a specific model."""
    for directory in [OLLAMA_MODEL_DIR, CUSTOM_MODEL_DIR]:
        model_path = os.path.join(directory, model_name)
        if os.path.exists(model_path):
            return {"model_name": model_name, "path": model_path, "size": os.path.getsize(model_path) if os.path.isfile(model_path) else None}
    raise HTTPException(status_code=404, detail="Model not found")

@router.post("/download")
def download_model(source: str = Query(..., description="Model source URL or identifier"),
                  target_dir: Optional[str] = Query(None, description="Target directory (ollama, custom, etc.)")):
    """Download a new model from a URL or identifier."""
    if target_dir == "ollama":
        dest_dir = OLLAMA_MODEL_DIR
    else:
        dest_dir = CUSTOM_MODEL_DIR
    os.makedirs(dest_dir, exist_ok=True)
    filename = os.path.basename(source)
    dest_path = os.path.join(dest_dir, filename)
    # Simple HTTP/HTTPS download
    if source.startswith("http://") or source.startswith("https://"):
        with requests.get(source, stream=True) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return {"status": "downloaded", "path": dest_path}
    # For Ollama or HuggingFace, you can add custom logic here
    return {"status": "not_implemented", "detail": "Only HTTP/HTTPS download supported in this example."}

@router.delete("/{model_name}")
def delete_model(model_name: str):
    """Delete a model by name."""
    deleted = False
    for directory in [OLLAMA_MODEL_DIR, CUSTOM_MODEL_DIR]:
        model_path = os.path.join(directory, model_name)
        if os.path.exists(model_path):
            if os.path.isfile(model_path):
                os.remove(model_path)
            else:
                shutil.rmtree(model_path)
            deleted = True
    if not deleted:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"status": "deleted", "model": model_name}

# (Optional) Add endpoints for refresh, status, set default, etc.
