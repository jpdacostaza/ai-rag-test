#!/usr/bin/env python3
"""
API Gateway Application - Main FastAPI application for the gateway service
Routes requests to appropriate backend services.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import logging
import os
from datetime import datetime
from routes.gateway import gateway_router

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="API Gateway",
    description="Centralized API Gateway for backend services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include gateway router
app.include_router(gateway_router)

@app.get("/health")
async def health_check():
    """Health check endpoint for the gateway."""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint with gateway information."""
    return {
        "message": "API Gateway is running",
        "services": [
            "backend (port 3000)",
            "memory-api (port 5001)", 
            "pipelines (port 9099)",
            "openwebui (port 8080)"
        ],
        "gateway_port": 8090,
        "docs": "/docs"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for the gateway."""
    logger.error(f"Gateway error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal gateway error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("GATEWAY_PORT", "8090"))
    logger.info(f"Starting API Gateway on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
