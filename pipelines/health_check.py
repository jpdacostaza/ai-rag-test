"""
Simple Health Check Pipeline
===========================
Provides health endpoint functionality for pipeline container monitoring.
"""

from typing import List, Union, Generator, Iterator
from pydantic import BaseModel


class Pipeline:
    """Simple pipeline for health monitoring"""
    
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]  # Connect to all pipelines
        # Pipeline priority (lower = higher priority)
        priority: int = 1000  # Low priority, won't interfere with other pipelines
        
    @property
    def pipelines(self):
        """Return pipelines configuration for OpenWebUI compatibility."""
        return [
            {
                "id": "health_check",
                "name": "Health Check Filter"
            }
        ]
        
    def __init__(self):
        self.name = "Health Check"
        self.valves = self.Valves()
        print("[HEALTH PIPELINE] Health check pipeline initialized")

    async def on_startup(self):
        """Called when the pipeline starts"""
        print("[HEALTH PIPELINE] Health check pipeline started successfully")

    async def on_shutdown(self):
        """Called when the pipeline shuts down"""
        print("[HEALTH PIPELINE] Health check pipeline shutting down")

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        This pipeline is transparent - it doesn't modify messages.
        It's only here to provide a health check presence.
        """
        # Pass through unchanged
        return user_message
