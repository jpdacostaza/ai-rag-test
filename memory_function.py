"""
Enhanced Memory Function for OpenWebUI - DISABLED
=====================================

⚠️ THIS FUNCTION IS DISABLED IN FAVOR OF ENHANCED MEMORY PIPELINE ⚠️

This function has been superseded by the Enhanced Memory Pipeline which provides:
- Better user authentication (no fallbacks to "openwebui_default_user")
- Improved memory handling
- Direct pipeline integration without function conflicts

This file is kept for reference but is disabled to prevent conflicts.
"""

import time
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class Valves(BaseModel):
    """Configuration valves for the memory function."""
    
    # Memory Settings - DISABLED
    enable_memory: bool = False  # DISABLED
    enable_learning: bool = False  # DISABLED
    debug: bool = True


class MemoryFunction:
    """
    DISABLED Memory Function for OpenWebUI
    
    This function is disabled in favor of Enhanced Memory Pipeline.
    All memory operations are handled by the pipeline instead.
    """
    
    def __init__(self):
        self.valves = Valves()
        
    def log(self, message: str, level: str = "WARNING"):
        """Log messages with timestamp."""
        if self.valves.debug:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{level}] [DISABLED Memory Function] {message}")
    
    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming messages - DISABLED."""
        self.log("⚠️ FUNCTION DISABLED - Enhanced Memory Pipeline is handling memory")
        return body
    
    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process outgoing messages - DISABLED."""
        self.log("⚠️ FUNCTION DISABLED - Enhanced Memory Pipeline is handling memory")
        return body


# Instantiate the disabled function for OpenWebUI
Tools = [MemoryFunction()]
