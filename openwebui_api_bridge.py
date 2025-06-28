"""
OpenWebUI API Bridge
===================

This module provides API endpoints that bridge the gap between
OpenWebUI's expected pipeline API and the actual pipelines server API.

The issue: OpenWebUI expects endpoints like /api/v1/pipelines/list
The reality: Pipelines server provides /v1/pipelines

This bridge maps the expected endpoints to the actual ones.
"""

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PIPELINES_BASE_URL = "http://pipelines:9099"
PIPELINES_API_KEY = "0p3n-w3bu!"

app = FastAPI(title="OpenWebUI API Bridge", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    method = request.method
    url = str(request.url)
    logger.info(f"🌐 {method} {url}")
    
    # Log headers if they contain Authorization
    if "authorization" in request.headers:
        logger.info(f"🔑 Authorization header present")
    
    response = await call_next(request)
    logger.info(f"📤 Response: {response.status_code}")
    return response

async def forward_to_pipelines(path: str, method: str = "GET", json_data: Dict = None, 
                             request_headers: Dict = None):
    """Forward request to the actual pipelines server."""
    url = f"{PIPELINES_BASE_URL}{path}"
    
    # Set up headers with authentication
    headers = {
        "Authorization": f"Bearer {PIPELINES_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Add any additional headers from the original request
    if request_headers:
        # Filter out headers that shouldn't be forwarded
        for key, value in request_headers.items():
            if key.lower() not in ['host', 'content-length']:
                headers[key] = value
    
    logger.info(f"Forwarding {method} {url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=json_data, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            logger.info(f"Pipeline response: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Pipeline error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except httpx.TimeoutException:
        logger.error("Timeout forwarding to pipelines")
        raise HTTPException(status_code=504, detail="Pipeline server timeout")
    except Exception as e:
        logger.error(f"Error forwarding to pipelines: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Essential endpoints that OpenWebUI requires

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify routing works."""
    logger.info("🧪 Test endpoint called")
    return {"test": "success"}

@app.get("/api/models")
async def list_models_api():
    """OpenWebUI API models endpoint - ONLY for non-pipeline models."""
    logger.info("🤖 OpenWebUI requesting API models list")
    
    # DO NOT return pipeline models here - they should be pipelines/filters only
    # OpenWebUI will get pipelines directly from the pipelines server
    
    # Return empty models list since pipelines handles all our custom models
    logger.info("✅ Returning empty models list (pipelines handle memory models)")
    return {"data": []}

# Bridge endpoints for OpenWebUI's expected API paths

@app.get("/api/v1/pipelines/list")
async def list_pipelines_list(request: Request, authorization: Optional[str] = Header(None)):
    """Bridge endpoint for OpenWebUI pipeline list requests (with /list suffix)."""
    logger.info("📋 OpenWebUI requesting pipeline list (/api/v1/pipelines/list)")
    
    # Forward to actual pipelines endpoint
    response = await forward_to_pipelines("/v1/pipelines", 
                                        request_headers=dict(request.headers))
    
    logger.info(f"✅ Returning {len(response.get('data', []))} pipelines")
    return response

@app.get("/api/v1/pipelines")
async def list_pipelines(request: Request, authorization: Optional[str] = Header(None)):
    """Bridge endpoint for OpenWebUI pipeline requests."""
    logger.info("📋 OpenWebUI requesting pipelines (/api/v1/pipelines)")
    
    # Forward to actual pipelines endpoint
    response = await forward_to_pipelines("/v1/pipelines", 
                                        request_headers=dict(request.headers))
    
    logger.info(f"✅ Returning {len(response.get('data', []))} pipelines")
    return response

@app.get("/api/v1/pipelines/")
async def list_pipelines_trailing_slash(request: Request, authorization: Optional[str] = Header(None)):
    """Bridge endpoint for OpenWebUI pipeline requests with trailing slash."""
    logger.info("📋 OpenWebUI requesting pipelines (/api/v1/pipelines/)")
    
    # Forward to actual pipelines endpoint
    response = await forward_to_pipelines("/v1/pipelines", 
                                        request_headers=dict(request.headers))
    
    logger.info(f"✅ Returning {len(response.get('data', []))} pipelines")
    return response

@app.get("/api/pipelines")
async def list_pipelines_short(request: Request, authorization: Optional[str] = Header(None)):
    """Bridge endpoint for OpenWebUI pipeline requests (short path)."""
    logger.info("📋 OpenWebUI requesting pipelines (/api/pipelines)")
    
    # Forward to actual pipelines endpoint
    response = await forward_to_pipelines("/v1/pipelines", 
                                        request_headers=dict(request.headers))
    
    logger.info(f"✅ Returning {len(response.get('data', []))} pipelines")
    return response

# Forward other pipeline operations

@app.post("/api/v1/{pipeline_id}/filter/inlet")
async def pipeline_inlet(pipeline_id: str, request: Request, data: dict):
    """Forward inlet filter requests."""
    logger.info(f"🔄 Inlet filter request for pipeline: {pipeline_id}")
    logger.info(f"📥 Raw inlet data: {data}")
    
    # The data coming from OpenWebUI needs to be structured as FilterForm
    # which expects: {"body": {...}, "user": {...}}
    
    # If data is already in FilterForm format, use it as-is
    if 'body' in data and 'user' in data:
        filter_form = data
    else:
        # Otherwise, wrap the data as the body and extract user info
        filter_form = {
            "body": data,
            "user": data.get("user", None)
        }
    
    logger.info(f"📤 Formatted for pipeline: {filter_form}")
    
    response = await forward_to_pipelines(f"/v1/{pipeline_id}/filter/inlet", 
                                        method="POST", 
                                        json_data=filter_form,
                                        request_headers=dict(request.headers))
    
    logger.info(f"✅ Inlet processed for {pipeline_id}")
    return response

@app.post("/api/v1/{pipeline_id}/filter/outlet")
async def pipeline_outlet(pipeline_id: str, request: Request, data: dict):
    """Forward outlet filter requests."""
    logger.info(f"🔄 Outlet filter request for pipeline: {pipeline_id}")
    logger.info(f"📥 Raw outlet data: {data}")
    
    # The data coming from OpenWebUI needs to be structured as FilterForm
    # which expects: {"body": {...}, "user": {...}}
    
    # If data is already in FilterForm format, use it as-is
    if 'body' in data and 'user' in data:
        filter_form = data
    else:
        # Otherwise, wrap the data as the body and extract user info
        filter_form = {
            "body": data,
            "user": data.get("user", None)
        }
    
    logger.info(f"📤 Formatted for pipeline: {filter_form}")
    
    response = await forward_to_pipelines(f"/v1/{pipeline_id}/filter/outlet", 
                                        method="POST", 
                                        json_data=filter_form,
                                        request_headers=dict(request.headers))
    
    logger.info(f"✅ Outlet processed for {pipeline_id}")
    return response

@app.get("/api/v1/{pipeline_id}/valves")
async def get_pipeline_valves(pipeline_id: str, request: Request):
    """Forward valve configuration requests."""
    logger.info(f"🔧 Getting valves for pipeline: {pipeline_id}")
    
    response = await forward_to_pipelines(f"/v1/{pipeline_id}/valves", 
                                        request_headers=dict(request.headers))
    
    return response

@app.post("/api/v1/{pipeline_id}/valves/update")
async def update_pipeline_valves(pipeline_id: str, request: Request, body: dict):
    """Forward valve update requests."""
    logger.info(f"🔧 Updating valves for pipeline: {pipeline_id}")
    
    response = await forward_to_pipelines(f"/v1/{pipeline_id}/valves/update", 
                                        method="POST", 
                                        json_data=body,
                                        request_headers=dict(request.headers))
    
    return response

# Health and status endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.info("🏥 OpenWebUI health check")
    return {
        "status": "ok", 
        "service": "openwebui-pipelines-bridge",
        "healthy": True,
        "pipelines": True
    }

@app.get("/")
async def root():
    """Root endpoint that OpenWebUI checks for server detection."""
    logger.info("🏠 OpenWebUI checking root endpoint for server detection")
    return {
        "status": True
    }

@app.get("/status")
async def status():
    """Status endpoint that OpenWebUI may check."""
    logger.info("📊 OpenWebUI checking status endpoint")
    return {
        "status": "ok",
        "service": "pipelines",
        "version": "1.0.0",
        "pipelines_available": True
    }

# Individual pipeline endpoints
@app.get("/api/v1/pipelines/{pipeline_id}")
async def get_pipeline_details(pipeline_id: str, request: Request, authorization: Optional[str] = Header(None)):
    """Get individual pipeline details that OpenWebUI expects."""
    logger.info(f"🔍 OpenWebUI requesting single pipeline: {pipeline_id}")
    
    # First get the list of all pipelines
    pipelines_response = await forward_to_pipelines("/v1/pipelines", 
                                                  request_headers=dict(request.headers))
    
    # Find the specific pipeline
    for pipeline in pipelines_response.get('data', []):
        if pipeline['id'] == pipeline_id:
            logger.info(f"✅ Found pipeline: {pipeline_id}")
            return pipeline
    
    logger.warning(f"❌ Pipeline not found: {pipeline_id}")
    raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")

@app.get("/v1/pipelines/{pipeline_id}")
async def get_single_pipeline_v1(pipeline_id: str, request: Request, authorization: Optional[str] = Header(None)):
    """Get individual pipeline information (v1 endpoint)."""
    logger.info(f"🔍 Direct v1 request for pipeline: {pipeline_id}")
    
    # Forward to the same logic as API v1
    return await get_pipeline_details(pipeline_id, request, authorization)

# Additional endpoints that OpenWebUI may call
@app.get("/api/version")
async def get_api_version():
    """API version endpoint that OpenWebUI may check."""
    logger.info("🔍 OpenWebUI checking API version")
    return {"version": "1.0.0", "service": "openwebui-api-bridge", "pipelines": True}

@app.get("/api/v1/version")
async def get_api_v1_version():
    """API v1 version endpoint that OpenWebUI may check."""
    logger.info("🔍 OpenWebUI checking API v1 version")
    return {"version": "1.0.0", "service": "openwebui-api-bridge", "pipelines": True}

@app.get("/api/v1/pipelines/{pipeline_id}/valves")
async def get_pipeline_valves(pipeline_id: str, request: Request, authorization: Optional[str] = Header(None)):
    """Get pipeline valves (configuration)."""
    logger.info(f"⚙️ OpenWebUI requesting valves for pipeline: {pipeline_id}")
    
    # Forward to actual pipelines endpoint
    response = await forward_to_pipelines(f"/v1/pipelines/{pipeline_id}/valves", 
                                        request_headers=dict(request.headers))
    
    logger.info(f"✅ Returning valves for pipeline: {pipeline_id}")
    return response

@app.post("/api/v1/pipelines/{pipeline_id}/valves/update")
async def update_pipeline_valves(pipeline_id: str, request: Request, data: dict, authorization: Optional[str] = Header(None)):
    """Update pipeline valves (configuration)."""
    logger.info(f"⚙️ OpenWebUI updating valves for pipeline: {pipeline_id}")
    
    # Forward to actual pipelines endpoint
    response = await forward_to_pipelines(f"/v1/pipelines/{pipeline_id}/valves/update", 
                                        method="POST",
                                        json_data=data,
                                        request_headers=dict(request.headers))
    
    logger.info(f"✅ Updated valves for pipeline: {pipeline_id}")
    return response

@app.get("/api/v1/pipelines/{pipeline_id}/valves/spec")
async def get_pipeline_valves_spec(pipeline_id: str, request: Request, authorization: Optional[str] = Header(None)):
    """Get pipeline valves specification (schema)."""
    logger.info(f"📋 OpenWebUI requesting valves spec for pipeline: {pipeline_id}")
    
    # Forward to actual pipelines endpoint
    response = await forward_to_pipelines(f"/v1/pipelines/{pipeline_id}/valves/spec", 
                                        request_headers=dict(request.headers))
    
    logger.info(f"✅ Returning valves spec for pipeline: {pipeline_id}")
    return response

@app.get("/debug/info")
async def debug_info():
    """Debug information."""
    return {
        "pipelines_url": PIPELINES_BASE_URL,
        "has_api_key": bool(PIPELINES_API_KEY),
        "endpoints": {
            "expected_by_openwebui": [
                "/api/v1/pipelines/list",
                "/api/v1/pipelines",
                "/api/pipelines",
                "/api/v1/pipelines/{id}",
                "/api/v1/pipelines/{id}/valves"
            ],
            "actual_pipelines_server": [
                "/v1/pipelines",
                "/pipelines"
            ]
        }
    }

# Function endpoints (newer OpenWebUI versions may use these instead)
@app.get("/api/v1/functions")
async def list_functions(request: Request, authorization: Optional[str] = Header(None)):
    """Bridge endpoint for OpenWebUI function requests (alternative to pipelines)."""
    logger.info("📋 OpenWebUI requesting functions (/api/v1/functions)")
    
    # Forward to actual pipelines endpoint but format as functions
    response = await forward_to_pipelines("/v1/pipelines", 
                                        request_headers=dict(request.headers))
    
    # Convert pipelines to functions format that OpenWebUI expects
    functions_data = []
    for pipeline in response.get('data', []):
        if pipeline['type'] == 'filter':  # Only include filter pipelines as functions
            function_def = {
                "id": pipeline['id'],
                "name": pipeline['name'],
                "type": "filter",  # Keep original type for OpenWebUI
                "description": f"Memory pipeline: {pipeline['name']}",
                "content": f"# {pipeline['name']}\n# Memory pipeline for OpenWebUI",
                "meta": {
                    "description": f"Memory pipeline: {pipeline['name']}",
                    "manifest": {
                        "required": False,
                        "type": "filter"
                    }
                },
                "valves": pipeline.get('valves', False)
            }
            functions_data.append(function_def)
    
    logger.info(f"✅ Returning {len(functions_data)} functions")
    return {"data": functions_data}

@app.get("/api/v1/functions/list")
async def list_functions_list(request: Request, authorization: Optional[str] = Header(None)):
    """Bridge endpoint for OpenWebUI function list requests."""
    logger.info("📋 OpenWebUI requesting function list (/api/v1/functions/list)")
    return await list_functions(request, authorization)

@app.get("/api/v1/functions/")
async def list_functions_trailing_slash(request: Request, authorization: Optional[str] = Header(None)):
    """Bridge endpoint for OpenWebUI function requests with trailing slash."""
    logger.info("📋 OpenWebUI requesting functions (/api/v1/functions/)")
    return await list_functions(request, authorization)

# OpenAI-compatible endpoints that OpenWebUI expects from all connections
@app.get("/models")
async def list_models():
    """OpenAI-compatible models endpoint - empty since pipelines handle memory models."""
    logger.info("🤖 OpenWebUI requesting models list")
    
    # Don't return pipeline models here - OpenWebUI gets them as pipelines/filters
    logger.info("✅ Returning empty models list (pipelines are handled as filters)")
    return {"data": []}

@app.get("/v1/models")
async def list_models_v1():
    """OpenAI-compatible v1 models endpoint."""
    logger.info("🤖 OpenWebUI requesting v1 models list")
    return await list_models()

# NOTE: Removed /v1/chat/completions endpoint
# OpenWebUI handles pipeline routing internally when pipelines are properly configured
# The pipeline models should work as filters on existing models, not as standalone models

# Catch-all route for debugging (MUST BE LAST!)
@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all_api_v1(path: str, request: Request):
    """Catch-all route to debug what OpenWebUI is requesting."""
    method = request.method
    url = str(request.url)
    
    # Skip paths that are handled by specific routes
    handled_paths = [
        "pipelines", "pipelines/", "pipelines/list",
        "version", "functions", "functions/", "functions/list"
    ]
    
    # Skip individual pipeline paths that are handled specifically
    pipeline_patterns = [
        r"pipelines/[^/]+$",           # /api/v1/pipelines/{id}
        r"pipelines/[^/]+/valves",     # /api/v1/pipelines/{id}/valves
        r"pipelines/[^/]+/valves/spec", # /api/v1/pipelines/{id}/valves/spec
        r"pipelines/[^/]+/valves/update", # /api/v1/pipelines/{id}/valves/update
        r"[^/]+/filter/inlet",         # /api/v1/{id}/filter/inlet
        r"[^/]+/filter/outlet"         # /api/v1/{id}/filter/outlet
    ]
    
    import re
    for pattern in pipeline_patterns:
        if re.match(pattern, path):
            logger.info(f"🔄 Skipping catch-all for known pipeline pattern: {path}")
            raise HTTPException(status_code=404, detail=f"Endpoint /api/v1/{path} should be handled by specific route")
    
    if path in handled_paths:
        logger.info(f"🔄 Skipping catch-all for handled path: {path}")
        raise HTTPException(status_code=404, detail=f"Endpoint /api/v1/{path} should be handled by specific route")
    
    logger.warning(f"🚨 CATCH-ALL: {method} /api/v1/{path}")
    logger.warning(f"🚨 Full URL: {url}")
    
    # If it's a single word (potential pipeline ID), try to handle it
    if path and "/" not in path and path not in handled_paths:
        logger.info(f"🔍 Treating '{path}' as potential pipeline ID")
        try:
            return await get_pipeline_details(path, request)
        except HTTPException:
            pass
    
    raise HTTPException(status_code=404, detail=f"Endpoint /api/v1/{path} not implemented")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
