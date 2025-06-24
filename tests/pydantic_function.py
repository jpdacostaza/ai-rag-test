from pydantic import BaseModel
from typing import Optional

class Function:
    class Valves(BaseModel):
        debug_mode: bool = True

    def __init__(self):
        self.valves = self.Valves()

    def pipe(self, body: dict) -> dict:
        print("[Function] Processing")
        return body
