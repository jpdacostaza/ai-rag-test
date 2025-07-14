"""
Simple Test Pipeline for OpenWebUI
==================================

A basic working pipeline to test OpenWebUI pipeline detection.
Based on the official OpenWebUI pipeline format.
"""

from typing import List, Union, Generator, Iterator
from pydantic import BaseModel


class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]
        priority: int = 0

    @property
    def pipelines(self):
        """Return pipelines configuration for OpenWebUI compatibility."""
        # Return a list of pipeline configurations that OpenWebUI expects
        return [{"id": "test_pipeline", "name": "Test Pipeline"}]

    def __init__(self):
        self.type = "manifold"
        self.id = "test_pipeline"
        self.name = "Test Pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"on_startup:{__name__}")

    async def on_shutdown(self):
        print(f"on_shutdown:{__name__}")

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        print(f"pipe:{__name__}")
        print(f"User message: {user_message}")
        print(f"Model ID: {model_id}")
        
        return f"Test pipeline response: {user_message}"
