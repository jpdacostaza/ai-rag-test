"""
OpenWebUI Pipeline endpoints as a separate module
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Optional
from human_logging import log_service_status

router = APIRouter()

def verify_api_key(api_key: Optional[str] = None):
    """Simple API key verification"""
    return api_key or "development"

@router.get("/pipelines")
async def list_pipelines():
    """List available pipelines for OpenWebUI"""
    log_service_status("PIPELINES", "info", "Pipeline list request received")
    
    # Simple pipeline configuration
    pipelines = [{
        "id": "memory_pipeline",
        "name": "Memory Pipeline",
        "type": "filter",
        "description": "Memory pipeline for OpenWebUI",
        "author": "Backend Team",
        "version": "1.0.0"
    }]
    
    log_service_status("PIPELINES", "ready", f"Returned {len(pipelines)} pipelines")
    return {"pipelines": pipelines}

@router.post("/pipelines/{pipeline_id}/inlet")
async def pipeline_inlet(
    pipeline_id: str,
    request: dict = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """Process incoming messages through the memory pipeline (inlet)"""
    try:
        if pipeline_id != "memory_pipeline":
            raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
        
        log_service_status("PIPELINES", "info", f"Processing inlet for pipeline {pipeline_id}")
        
        # Extract data from the request
        messages = request.get("messages", [])
        user_id = request.get("user", {}).get("id", "unknown")
        
        # For now, just pass through the messages without modification
        # In a real implementation, this would inject memory/context
        response = {
            "messages": messages,
            "user": request.get("user", {}),
            "__metadata__": {
                "pipeline": "memory_pipeline",
                "processed": True,
                "memory_injected": False  # Would be True if we actually injected memory
            }
        }
        
        log_service_status("PIPELINES", "ready", f"Inlet processing completed for {pipeline_id}")
        return response
        
    except Exception as e:
        log_service_status("PIPELINES", "error", f"Inlet processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")

@router.post("/pipelines/{pipeline_id}/outlet")
async def pipeline_outlet(
    pipeline_id: str,
    request: dict = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """Process outgoing messages through the memory pipeline (outlet)"""
    try:
        if pipeline_id != "memory_pipeline":
            raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
        
        log_service_status("PIPELINES", "info", f"Processing outlet for pipeline {pipeline_id}")
        
        # Extract data from the request
        messages = request.get("messages", [])
        user_id = request.get("user", {}).get("id", "unknown")
        
        # For now, just pass through without modification
        # In a real implementation, this would store the conversation in memory
        response = {
            "messages": messages,
            "user": request.get("user", {}),
            "__metadata__": {
                "pipeline": "memory_pipeline",
                "processed": True,
                "memory_stored": False  # Would be True if we actually stored memory
            }
        }
        
        log_service_status("PIPELINES", "ready", f"Outlet processing completed for {pipeline_id}")
        return response
        
    except Exception as e:
        log_service_status("PIPELINES", "error", f"Outlet processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")

@router.get("/pipelines/{pipeline_id}")
async def get_pipeline(pipeline_id: str):
    """Get pipeline details"""
    if pipeline_id != "memory_pipeline":
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
    
    return {
        "id": "memory_pipeline",
        "name": "Memory Pipeline",
        "type": "filter",
        "description": "Memory pipeline for OpenWebUI",
        "author": "Backend Team",
        "version": "1.0.0",
        "enabled": True,
        "valves": {
            "backend_url": "http://host.docker.internal:8001",
            "api_key": "development",
            "memory_limit": 3,
            "enable_learning": True
        }
    }

@router.get("/pipelines/{pipeline_id}/valves")
async def get_pipeline_valves(pipeline_id: str):
    """Get pipeline valve configuration"""
    if pipeline_id != "memory_pipeline":
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
    
    return {
        "backend_url": "http://host.docker.internal:8001",
        "api_key": "development",
        "memory_limit": 3,
        "enable_learning": True,
        "enable_memory_injection": True,
        "max_memory_length": 500
    }
