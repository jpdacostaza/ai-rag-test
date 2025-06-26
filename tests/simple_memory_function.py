"""
title: Simple Memory Function
author: Backend Team
version: 1.0.0
description: Simple memory function for OpenWebUI
"""

import os


class Valves:
    """TODO: Add proper docstring for Valves class."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.backend_url = "http://host.docker.internal:8001"
        self.api_key = os.getenv("API_KEY", "default_test_key")
        self.debug_mode = True


class Function:
    """TODO: Add proper docstring for Function class."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.valves = Valves()

    def pipe(self, body: dict):
        """TODO: Add proper docstring for pipe."""
        # Simple function that just prints debug info
        print(f"[Simple Memory Function] Processing request")
        print(f"[Simple Memory Function] Body keys: {body.keys()}")

        # Return the body unchanged
        return body
