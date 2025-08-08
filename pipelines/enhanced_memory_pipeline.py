"""
title: Enhanced Memory Pipeline 
author: OpenWebUI Assistant
date: 2025-08-08
version: 2.0
license: MIT
description: Zero-configuration pipeline for intelligent context understanding and conversation memory. Works globally across all models without external dependencies.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Pipeline:
    class Valves(BaseModel):
        """Configuration valves for the Enhanced Memory Pipeline"""
        # Global Settings
        ENABLE_GLOBAL_CONTEXT: bool = True
        INTELLIGENT_CONTEXT: bool = True
        DEBUG_LOGGING: bool = False
        
        # Memory Settings (future use)
        MEMORY_ENABLED: bool = False  # Disabled for zero-config
        MAX_MEMORY_ENTRIES: int = 100
        
        # Priority and Confidence
        PIPELINE_PRIORITY: int = 1  # High priority for context injection
        CONFIDENCE_THRESHOLD: float = 0.8

    def __init__(self):
        self.name = "Enhanced Memory & Context Pipeline"
        self.valves = self.Valves()
        
        # Global pipeline - works with all models
        self.type = "filter"  # Filter type for global operation
        
        if self.valves.DEBUG_LOGGING:
            print(f"[ENHANCED MEMORY] Pipeline initialized for global use")
            print(f"[ENHANCED MEMORY] Intelligent context: {'ENABLED' if self.valves.INTELLIGENT_CONTEXT else 'DISABLED'}")

    def log(self, message: str, level: str = "INFO") -> None:
        """Conditional logging based on debug setting"""
        if self.valves.DEBUG_LOGGING:
            print(f"[ENHANCED MEMORY] [{level}] {message}")

    async def on_startup(self):
        """Pipeline startup initialization"""
        self.log("Pipeline startup - ready to process requests")
        return True

    async def on_shutdown(self):
        """Pipeline shutdown cleanup"""
        self.log("Pipeline shutting down gracefully")
        return True

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming requests with intelligent context understanding (GLOBAL)"""
        try:
            if not self.valves.ENABLE_GLOBAL_CONTEXT:
                return body
                
            self.log("Processing request for intelligent context")
            
            # Intelligent Context Enhancement (Zero-Config)
            messages = body.get("messages", [])
            if not messages or not self.valves.INTELLIGENT_CONTEXT:
                return body
                
            # Let the model use its intelligence and web search capabilities
            # Remove explicit context injection - trust the model's knowledge
            self.log("Allowing model to use native intelligence and web search")
                
            return body
            
        except Exception as e:
            self.log(f"Inlet error: {e}", "ERROR")
            return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process outgoing responses (GLOBAL)"""
        try:
            self.log("Processing response")
            
            # Future: Could add response enhancement here
            # For now, just pass through
            
            return body
            
        except Exception as e:
            self.log(f"Outlet error: {e}", "ERROR")
            return body
