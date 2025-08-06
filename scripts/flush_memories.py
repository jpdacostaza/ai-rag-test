#!/usr/bin/env python3
"""
Memory Database Flush Script
============================

This script completely clears all memories from both Redis and ChromaDB.
Use this to start fresh with a clean memory state.
"""

import requests
import json
import time

def flush_all_memories():
    """Flush all memories from Redis and ChromaDB."""
    print("🗑️ Starting memory database flush...")
    
    memory_api_url = "http://localhost:5001"
    
    # Check current status
    try:
        response = requests.get(f"{memory_api_url}/health")
        if response.status_code == 200:
            data = response.json()
            current_count = data.get("memory_count", 0)
            print(f"📊 Current memory count: {current_count}")
        else:
            print(f"⚠️ Could not get current status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False
    
    # Method 1: Try to clear via memory API endpoints
    print("\n🔄 Method 1: Attempting to clear via Memory API...")
    
    # Common user IDs to try clearing
    user_ids_to_clear = [
        "admin@theroot.za.net",
        "persistent_user_anonymous", 
        "test_user",
        "default_user",
        # Add session-based IDs pattern
    ]
    
    for user_id in user_ids_to_clear:
        try:
            # Try to get memories for this user first
            retrieve_payload = {
                "user_id": user_id,
                "query": "all memories",
                "limit": 100,
                "threshold": 10.0  # Very high threshold to get everything
            }
            
            response = requests.post(
                f"{memory_api_url}/api/memory/retrieve",
                json=retrieve_payload
            )
            
            if response.status_code == 200:
                data = response.json()
                memories = data.get("memories", [])
                print(f"📝 Found {len(memories)} memories for user {user_id}")
                
                # Unfortunately, there's no bulk delete endpoint, so this is mainly for info
                
            else:
                print(f"⚠️ Could not retrieve memories for {user_id}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error processing user {user_id}: {e}")
    
    print("\n🔄 Method 2: Direct Docker operations...")
    
    # Method 2: Direct Docker redis flush
    import subprocess
    try:
        print("🗑️ Flushing Redis...")
        result = subprocess.run([
            "docker-compose", "exec", "-T", "redis", 
            "redis-cli", "FLUSHALL"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Redis flushed successfully")
        else:
            print(f"❌ Redis flush failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error flushing Redis: {e}")
    
    # Method 3: Restart ChromaDB for clean slate
    try:
        print("🔄 Restarting ChromaDB...")
        result = subprocess.run([
            "docker-compose", "restart", "chroma"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ ChromaDB restarted successfully")
        else:
            print(f"❌ ChromaDB restart failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error restarting ChromaDB: {e}")
    
    # Wait for services to stabilize
    print("⏳ Waiting for services to stabilize...")
    time.sleep(5)
    
    # Check final status
    try:
        response = requests.get(f"{memory_api_url}/health")
        if response.status_code == 200:
            data = response.json()
            final_count = data.get("memory_count", 0)
            print(f"\n📊 Final memory count: {final_count}")
            
            if final_count == 0:
                print("🎉 SUCCESS: All memories cleared!")
            else:
                print(f"⚠️ WARNING: Still {final_count} memories remaining")
                print("💡 Try running the script again or manually restart memory-api container")
        else:
            print(f"⚠️ Could not verify final status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking final status: {e}")

if __name__ == "__main__":
    flush_all_memories()
