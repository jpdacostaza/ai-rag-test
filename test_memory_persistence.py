#!/usr/bin/env python3
"""
Simple test to verify memory storage and ensure clean facts persist
"""

import requests
import json
import time
from datetime import datetime

def test_memory_persistence():
    """Test that stored memories persist and can be retrieved"""
    
    print("🧪 MEMORY PERSISTENCE TEST")
    print("=" * 30)
    
    # Store a simple test fact
    test_fact = {
        "user_id": "global_user",
        "content": "TEST: User's name is J.P.",
        "metadata": {
            "type": "identity_fact",
            "source": "persistence_test",
            "timestamp": datetime.now().isoformat(),
            "keywords": "test name jp user identity",
            "importance": 0.99
        }
    }
    
    try:
        # Store the fact
        print("📝 Storing test fact...")
        response = requests.post(
            "http://localhost:5001/api/memory/store",
            json=test_fact,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Test fact stored successfully")
        else:
            print(f"❌ Storage failed: {response.status_code} - {response.text}")
            return
            
        # Wait a moment
        time.sleep(1)
        
        # Try to retrieve it immediately
        print("\n🔍 Retrieving test fact...")
        retrieve_payload = {
            "user_id": "global_user",
            "query": "J.P.",
            "limit": 10,
            "similarity_threshold": 0.0
        }
        
        response = requests.post(
            "http://localhost:5001/api/memory/retrieve",
            json=retrieve_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get("memories", [])
            
            print(f"Found {len(memories)} memories")
            
            # Look for our test fact
            test_found = False
            for memory in memories:
                content = memory.get("content", "")
                metadata = memory.get("metadata", {})
                if "TEST: User's name is J.P." in content:
                    test_found = True
                    print(f"✅ Test fact found!")
                    print(f"   Content: {content}")
                    print(f"   Type: {metadata.get('type', 'unknown')}")
                    print(f"   Score: {memory.get('similarity_score', 0):.3f}")
                    break
            
            if not test_found:
                print("❌ Test fact NOT found in retrieval")
                print("Available memories:")
                for i, memory in enumerate(memories[:3]):
                    content = memory.get("content", "")
                    print(f"   {i+1}. {content[:50]}...")
        else:
            print(f"❌ Retrieval failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")

if __name__ == "__main__":
    test_memory_persistence()
