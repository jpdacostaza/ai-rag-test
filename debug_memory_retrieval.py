#!/usr/bin/env python3
"""
Debug what memories are being retrieved and why identity facts aren't showing up
"""

import requests
import json

def debug_memory_retrieval():
    """Debug memory retrieval to see what's actually stored"""
    
    print("🔍 DEBUGGING MEMORY RETRIEVAL")
    print("=" * 40)
    
    test_queries = [
        "What do you know about me?",
        "J.P.",
        "my name",
        "Swift",
        "work"
    ]
    
    for query in test_queries:
        try:
            payload = {
                "user_id": "global_user",
                "query": query,
                "limit": 10,
                "similarity_threshold": 0.0  # Get everything
            }
            
            response = requests.post(
                "http://localhost:5001/api/memory/retrieve",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                
                print(f"\n📝 Query: '{query}'")
                print(f"   Found {len(memories)} memories")
                
                for i, memory in enumerate(memories):
                    content = memory.get("content", "")
                    metadata = memory.get("metadata", {})
                    memory_type = metadata.get("type", "unknown")
                    similarity = memory.get("similarity_score", 0)
                    importance = metadata.get("importance", 0)
                    
                    print(f"   {i+1}. [{memory_type.upper()}] {content[:60]}...")
                    print(f"      Score: {similarity:.3f}, Importance: {importance}")
                    
                    # Show identity facts in detail
                    if memory_type == "identity_fact":
                        print(f"      🎯 IDENTITY FACT: {content}")
                        
            else:
                print(f"❌ Query '{query}' failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing query '{query}': {str(e)}")

    # Check if our clean facts exist
    print(f"\n🔍 SEARCHING FOR CLEAN IDENTITY FACTS")
    print("=" * 40)
    
    clean_facts = [
        "User's name is J.P.",
        "User works at Swift"
    ]
    
    for fact in clean_facts:
        try:
            payload = {
                "user_id": "global_user",
                "query": fact,
                "limit": 5,
                "similarity_threshold": 0.0
            }
            
            response = requests.post(
                "http://localhost:5001/api/memory/retrieve",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                
                found_exact = False
                for memory in memories:
                    if fact in memory.get("content", ""):
                        found_exact = True
                        print(f"✅ Found: '{fact}'")
                        print(f"   Score: {memory.get('similarity_score', 0):.3f}")
                        break
                
                if not found_exact:
                    print(f"❌ Missing: '{fact}'")
                    
            else:
                print(f"❌ Search for '{fact}' failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error searching for '{fact}': {str(e)}")

if __name__ == "__main__":
    debug_memory_retrieval()
