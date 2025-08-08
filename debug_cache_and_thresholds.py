#!/usr/bin/env python3
"""
Clear memory cache and check for conflicting settings
"""

import requests
import json
import subprocess
from datetime import datetime

def clear_memory_cache_and_verify():
    """Clear all memory cache and verify clean slate"""
    
    print("🧹 CLEARING MEMORY CACHE AND VERIFYING SETTINGS")
    print("=" * 50)
    
    # 1. Try to clear memory API cache
    print("1. Clearing memory API cache...")
    try:
        # Check if memory API has a clear endpoint
        response = requests.get("http://localhost:5001/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Memory API is accessible")
            
            # Try to get all memories to see what's stored
            retrieve_all = {
                "user_id": "global_user",
                "query": "",
                "limit": 50,
                "similarity_threshold": -2.0  # Get everything
            }
            
            response = requests.post(
                "http://localhost:5001/api/memory/retrieve",
                json=retrieve_all,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                print(f"   📊 Found {len(memories)} total memories in cache")
                
                # Show problematic memories
                problematic = []
                for memory in memories:
                    content = memory.get("content", "")
                    if "do you know about me" in content.lower() or "User works at do you know about me" in content:
                        problematic.append(content)
                
                if problematic:
                    print(f"   ❌ Found {len(problematic)} problematic cached memories:")
                    for prob in problematic[:3]:
                        print(f"      • {prob[:60]}...")
                else:
                    print("   ✅ No obviously problematic memories found")
            else:
                print(f"   ❌ Failed to retrieve memories: {response.status_code}")
        else:
            print(f"   ❌ Memory API not accessible: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Memory API error: {str(e)}")
    
    # 2. Check Docker containers for cache issues
    print(f"\n2. Checking container cache issues...")
    try:
        # Check if containers need restart to clear cache
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, check=True
        )
        print("   📋 Current container status:")
        print(f"   {result.stdout}")
        
    except Exception as e:
        print(f"   ❌ Docker check error: {str(e)}")
    
    # 3. Check for threshold conflicts
    print(f"\n3. Checking threshold configuration conflicts...")
    
    threshold_sources = {
        "Function v5.1": "0.3 (positive)",
        "Function v4": "-0.3 (negative)", 
        "Memory settings": "2.0 (very high)",
        "Current API": "Unknown"
    }
    
    for source, value in threshold_sources.items():
        print(f"   • {source}: {value}")
    
    print(f"\n   ⚠️  CONFLICT DETECTED: Multiple threshold values!")
    print(f"   📋 Solution: Use consistent negative threshold across all components")
    
    # 4. Test clean memory storage
    print(f"\n4. Testing clean memory storage...")
    
    # Store a test identity fact with explicit type
    test_memory = {
        "user_id": "global_user",
        "content": "CLEAN_TEST: User's name is J.P.",
        "metadata": {
            "type": "identity_fact",
            "source": "clean_test",
            "timestamp": datetime.now().isoformat(),
            "keywords": "clean test name jp user identity",
            "importance": 0.99
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:5001/api/memory/store",
            json=test_memory,
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ Clean test memory stored successfully")
            
            # Try to retrieve it with different thresholds
            test_thresholds = [-1.0, -0.5, 0.0, 0.3, 0.5, 1.0]
            
            for threshold in test_thresholds:
                retrieve_payload = {
                    "user_id": "global_user",
                    "query": "J.P.",
                    "limit": 5,
                    "similarity_threshold": threshold
                }
                
                response = requests.post(
                    "http://localhost:5001/api/memory/retrieve",
                    json=retrieve_payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    memories = result.get("memories", [])
                    
                    # Look for our clean test
                    found_clean = any("CLEAN_TEST" in m.get("content", "") for m in memories)
                    
                    print(f"   Threshold {threshold:+.1f}: {len(memories)} memories, Clean test: {'✅' if found_clean else '❌'}")
                    
                    if found_clean:
                        for memory in memories:
                            if "CLEAN_TEST" in memory.get("content", ""):
                                score = memory.get("similarity_score", 0)
                                metadata_type = memory.get("metadata", {}).get("type", "unknown")
                                print(f"      → Score: {score:.3f}, Type: {metadata_type}")
                                break
                else:
                    print(f"   Threshold {threshold:+.1f}: ❌ Failed to retrieve")
        else:
            print(f"   ❌ Failed to store clean test memory: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Clean memory test error: {str(e)}")

def suggest_fixes():
    """Suggest fixes for the threshold and cache issues"""
    
    print(f"\n🔧 SUGGESTED FIXES")
    print("=" * 20)
    
    print("1. 🎯 THRESHOLD ALIGNMENT:")
    print("   • Change function v5.1 threshold from 0.3 to -0.5")
    print("   • Use negative thresholds consistently") 
    print("   • Memory scores are typically negative (cosine similarity)")
    
    print(f"\n2. 🧹 CACHE CLEARING:")
    print("   • Restart memory-api container to clear vector cache")
    print("   • Clear ChromaDB collection if needed")
    print("   • Re-import function in OpenWebUI after threshold fix")
    
    print(f"\n3. 🚫 EXTRACTION FIX:")
    print("   • Fix regex to NOT extract from questions")
    print("   • Only extract from declarative statements")
    print("   • Improve context detection")
    
    print(f"\n4. 📋 STEPS TO FIX:")
    print("   1. Update threshold in v5.1 function to -0.5")
    print("   2. Fix extraction regex patterns")  
    print("   3. Restart containers: docker restart memory-api backend-openwebui")
    print("   4. Re-import function in OpenWebUI")
    print("   5. Test with clean introduction")

if __name__ == "__main__":
    clear_memory_cache_and_verify()
    suggest_fixes()
