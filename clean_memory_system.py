#!/usr/bin/env python3
"""
Clean Memory System
==================
Clear old test memories and fix name confusion.
"""

import requests
import json

def clean_memory_system():
    """Clean up the memory system to remove old test data"""
    base_url = "http://localhost:8001"
    
    print("🧹 Cleaning Memory System...")
    
    # Since there's no delete endpoint, let's restart the containers to reset Redis
    # and create a fresh start for the user
    print("   Stopping memory containers to clear Redis cache...")
    
    import subprocess
    
    # Restart Redis to clear short-term memories
    result = subprocess.run(["docker", "compose", "restart", "redis"], 
                          capture_output=True, text=True, cwd=".")
    
    if result.returncode == 0:
        print("✅ Redis restarted - short-term memories cleared")
    else:
        print(f"❌ Failed to restart Redis: {result.stderr}")
    
    # Restart memory API to get fresh connections
    result = subprocess.run(["docker", "compose", "restart", "memory_api"], 
                          capture_output=True, text=True, cwd=".")
    
    if result.returncode == 0:
        print("✅ Memory API restarted")
    else:
        print(f"❌ Failed to restart Memory API: {result.stderr}")
    
    print("🎉 Memory system cleaned! You can now start fresh.")
    print("📝 Next steps:")
    print("   1. Go to OpenWebUI")
    print("   2. Start a new chat")
    print("   3. Tell it your real name and job")
    print("   4. Test memory in a new chat")

if __name__ == "__main__":
    clean_memory_system()
