#!/bin/bash
"""
Cache Management Initialization Script
Run this when deploying updates to ensure cache compatibility.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_cache_manager, db_manager
from human_logging import log_service_status

def initialize_cache_management():
    """Initialize cache management with version control."""
    try:
        log_service_status("CACHE_INIT", "starting", "Initializing cache management system")
        
        # Get cache manager
        cache_manager = get_cache_manager()
        if not cache_manager:
            log_service_status("CACHE_INIT", "failed", "Could not initialize cache manager")
            return False
        
        # Force system prompt check
        current_prompt = "You are a helpful assistant. Use the following memory and chat history to answer. Always respond with plain text only - never use JSON formatting, structured responses, or any special formatting. Just provide direct, natural language answers."
        cache_manager.check_system_prompt_change(current_prompt)
        
        # Get initial stats
        stats = cache_manager.get_cache_stats()
        log_service_status("CACHE_INIT", "ready", f"Cache management initialized. Version: {stats.get('version', 'unknown')}, Total keys: {stats.get('total_keys', 0)}")
        
        return True
    except Exception as e:
        log_service_status("CACHE_INIT", "failed", f"Cache initialization failed: {e}")
        return False

if __name__ == "__main__":
    # Run as standalone script
    from human_logging import init_logging
    init_logging(level="INFO")
    
    success = initialize_cache_management()
    sys.exit(0 if success else 1)
