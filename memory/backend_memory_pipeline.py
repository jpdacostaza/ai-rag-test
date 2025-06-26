"""
OpenWebUI Memory Pipeline that connects to our FastAPI backend
This pipeline will call our backend's pipeline endpoints for memory and learning functionality
"""

from typing import List, Optional, Dict, Any
import requests
import json


class Pipeline:
    """Memory Pipeline for OpenWebUI that uses our FastAPI backend"""

    class Valves:
        """TODO: Add proper docstring for Valves class."""

        # Pipeline valve configuration
        backend_url: str = "http://host.docker.internal:8001"
        api_key: str = "development"
        memory_limit: int = 3
        enable_learning: bool = True
        enable_memory_injection: bool = True
        max_memory_length: int = 500

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        # Pipeline metadata
        self.type = "filter"  # or "pipe"
        self.id = "backend_memory_pipeline"
        self.name = "Backend Memory Pipeline"
        self.description = "Memory and learning pipeline powered by FastAPI backend"
        self.version = "1.0.0"
        self.valves = self.Valves()

    async def on_startup(self):
        """Called when the pipeline starts"""
        print(f"[{self.name}] Pipeline starting up...")
        # Test backend connectivity
        try:
            response = requests.get(f"{self.valves.backend_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"[{self.name}] ✅ Backend connection successful")
            else:
                print(f"[{self.name}] ⚠️ Backend returned status {response.status_code}")
        except Exception as e:
            print(f"[{self.name}] ❌ Backend connection failed: {e}")

    async def on_shutdown(self):
        """Called when the pipeline shuts down"""
        print(f"[{self.name}] Pipeline shutting down...")

    def pipe(self, user_message: str, model_id: str, messages: List[Dict], body: Dict) -> str:
        """
        This method is called when the pipeline is used as a "pipe" type.
        Not used in this filter-based implementation.
        """
        return user_message

    async def inlet(self, body: Dict, user: Optional[Dict] = None) -> Dict:
        """
        Process incoming requests (before they go to the LLM)
        This is where we inject memory/context
        """
        try:
            print(f"[{self.name}] Processing inlet...")

            # Extract user information
            user_id = user.get("id", "default_user") if user else "default_user"
            messages = body.get("messages", [])

            if not messages:
                return body

            # Find the latest user message
            latest_message = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    latest_message = msg
                    break

            if not latest_message or not latest_message.get("content"):
                return body

            user_query = latest_message["content"]
            print(f"[{self.name}] User {user_id} query: {user_query[:50]}...")

            # Call our backend's pipeline inlet endpoint
            if self.valves.enable_memory_injection:
                try:
                    backend_request = {"body": body, "user": user or {"id": user_id}}

                    response = requests.post(
                        f"{self.valves.backend_url}/pipelines/memory_pipeline/inlet",
                        json=backend_request,
                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.valves.api_key}"},
                        timeout=10,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        enhanced_body = result.get("body", body)
                        print(f"[{self.name}] ✅ Memory injection successful")
                        return enhanced_body
                    else:
                        print(f"[{self.name}] ⚠️ Backend inlet returned {response.status_code}")

                except Exception as e:
                    print(f"[{self.name}] ❌ Memory injection failed: {e}")

            return body

        except Exception as e:
            print(f"[{self.name}] ❌ Inlet processing failed: {e}")
            return body

    async def outlet(self, body: Dict, user: Optional[Dict] = None) -> Dict:
        """
        Process outgoing responses (after they come from the LLM)
        This is where we store the conversation for learning
        """
        try:
            print(f"[{self.name}] Processing outlet...")

            # Extract user information
            user_id = user.get("id", "default_user") if user else "default_user"
            messages = body.get("messages", [])

            if len(messages) < 2:
                return body

            # Call our backend's pipeline outlet endpoint
            if self.valves.enable_learning:
                try:
                    backend_request = {"body": body, "user": user or {"id": user_id}}

                    response = requests.post(
                        f"{self.valves.backend_url}/pipelines/memory_pipeline/outlet",
                        json=backend_request,
                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.valves.api_key}"},
                        timeout=10,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        processed_body = result.get("body", body)
                        print(f"[{self.name}] ✅ Learning storage successful")
                        return processed_body
                    else:
                        print(f"[{self.name}] ⚠️ Backend outlet returned {response.status_code}")

                except Exception as e:
                    print(f"[{self.name}] ❌ Learning storage failed: {e}")

            return body

        except Exception as e:
            print(f"[{self.name}] ❌ Outlet processing failed: {e}")
            return body
