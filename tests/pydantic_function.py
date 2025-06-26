from pydantic import BaseModel
from typing import Optional


class Function:
    """TODO: Add proper docstring for Function class."""

    class Valves(BaseModel):
        """TODO: Add proper docstring for Valves class."""

        debug_mode: bool = True

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.valves = self.Valves()

    def pipe(self, body: dict) -> dict:
        """TODO: Add proper docstring for pipe."""
        print("[Function] Processing")
        return body
