#!/usr/bin/env python3
"""
API Gateway Router
Provides centralized access to all services with FastAPI Router pattern.
"""

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import os

logger = logging.getLogger(__name__)

# Create router
gateway_router = APIRouter(
    prefix="/gateway",
    tags=["gateway"],
    responses={404: {"description": "Not found"}},
)

# Service configuration
SERVICES = {
    "backend": {
        "url": os.getenv("BACKEND_URL", "http://backend-main:3000"),
        "health": "/health"
    },
    "memory": {
        "url": os.getenv("MEMORY_API_URL", "http://backend-memory-api:5001"),
        "health": "/health"
    },
    "ollama": {
        "url": "http://backend-ollama:11434",
        "health": "/api/tags"
    },
    "openwebui": {
        "url": "http://backend-openwebui:8080",
        "health": "/health"
    },
    "pipelines": {
        "url": "http://backend-pipelines:9099",
        "health": "/"
    },
    "chroma": {
        "url": "http://backend-chroma:8000",
        "health": "/api/v1/heartbeat"
    }
}

# HTTP client instance
client = None

async def get_http_client():
    """Get or create HTTP client"""
    global client
    if client is None:
        client = httpx.AsyncClient(timeout=30.0)
    return client

async def close_http_client():
    """Close HTTP client"""
    global client
    if client:
        await client.aclose()
        client = None

@gateway_router.get("/health")
async def gateway_health():
    """Gateway health check endpoint"""
    return {
        "status": "healthy",
        "service": "API Gateway",
        "timestamp": datetime.now().isoformat(),
        "services": len(SERVICES)
    }

@gateway_router.get("/health/{service_name}")
async def service_health(service_name: str):
    """Check health of a specific service"""
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    service = SERVICES[service_name]
    try:
        client = await get_http_client()
        response = await client.get(f"{service['url']}{service['health']}")
        return {
            "service": service_name,
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "status_code": response.status_code,
            "url": service['url'],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "service": service_name,
            "status": "error",
            "error": str(e),
            "url": service['url'],
            "timestamp": datetime.now().isoformat()
        }

@gateway_router.get("/services")
async def list_services():
    """List all available services"""
    return {
        "services": list(SERVICES.keys()),
        "total": len(SERVICES),
        "timestamp": datetime.now().isoformat()
    }

@gateway_router.api_route("/proxy/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(service_name: str, path: str, request: Request):
    """Proxy requests to backend services"""
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    service = SERVICES[service_name]
    target_url = f"{service['url']}/{path}"
    
    # Get request body and headers
    body = await request.body()
    headers = dict(request.headers)
    
    # Remove host header to avoid conflicts
    headers.pop("host", None)
    
    try:
        client = await get_http_client()
        response = await client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers=headers,
            params=request.query_params
        )
        
        # Return the response
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Service unavailable")
    except Exception as e:
        logger.error(f"Proxy error for {service_name}/{path}: {e}")
        raise HTTPException(status_code=500, detail="Internal gateway error")

@gateway_router.get("/")
async def gateway_root():
    """Gateway root endpoint"""
    return {
        "service": "API Gateway",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/gateway/health",
            "services": "/gateway/services",
            "proxy": "/gateway/proxy/{service}/{path}"
        }
    }
