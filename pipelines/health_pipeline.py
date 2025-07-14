"""
Health Check Pipeline for OpenWebUI
===================================

A simple pipeline that provides a health endpoint for container monitoring.
"""

from pydantic import BaseModel
from typing import List, Union, Generator, Iterator, Optional
import json


class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]  # Connect to all pipelines
        priority: int = 0
        
    @property
    def pipelines(self):
        """Return pipelines configuration for OpenWebUI compatibility."""
        return [
            {
                "id": "health_pipeline",
                "name": "Health Check Pipeline"
            }
        ]
        
    def __init__(self):
        self.name = "Health Check Pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        """Called when the pipeline starts up."""
        print(f"[HEALTH] Health Check Pipeline started")

    async def on_shutdown(self):
        """Called when the pipeline shuts down."""
        print(f"[HEALTH] Health Check Pipeline stopping")

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        This pipeline doesn't modify messages, it's just for health checking.
        """
        # Just pass through the message unchanged
        return user_message


# FastAPI routes for health checking
from fastapi import FastAPI, HTTPException
import uvicorn

# This will be mounted by the pipeline system
app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "OpenWebUI Pipelines",
        "timestamp": "2025-07-13T17:00:00Z"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OpenWebUI Pipelines",
        "status": "running",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    # This will only run if the file is executed directly
    uvicorn.run(app, host="0.0.0.0", port=9099)
