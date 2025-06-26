"""
title: Test Function
author: Backend Team
version: 1.0.0
description: Minimal test function for OpenWebUI
"""


class Valves:
    """TODO: Add proper docstring for Valves class."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.debug_mode = True


class Function:
    """TODO: Add proper docstring for Function class."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.valves = Valves()

    def pipe(self, user_message, model_id, messages, body):
        """TODO: Add proper docstring for pipe."""
        print("[Test Function] Working!")
        return user_message
