#!/usr/bin/env python3
"""
Complete memory system test with immediate verification
"""

import requests
import json
import time
from datetime import datetime

def complete_memory_test():
    """Store identity facts and test retrieval immediately"""
    
    print("🧪 COMPLETE MEMORY SYSTEM TEST")
    print("=" * 40)
    
    # Clear identity facts to store
    identity_facts = [
        {
            "content": "User's name is J.P.",
            "metadata": {
                "type": "identity_fact",
                "source": "user_introduction",
                "timestamp": datetime.now().isoformat(),
                "keywords": "name jp j.p. user identity",
                "importance": 0.95
            }
        },
        {
            "content": "User works at Swift",
            "metadata": {
                "type": "identity_fact", 
                "source": "user_introduction",
                "timestamp": datetime.now().isoformat(),
                "keywords": "work swift company job employer",
                "importance": 0.95
            }
        }
    ]
    
    print("📝 STORING IDENTITY FACTS")
    print("-" * 25)
    
    stored_count = 0
    for fact_data in identity_facts:
        memory_payload = {
            "user_id": "global_user",
            "content": fact_data["content"],
            "metadata": fact_data["metadata"]
        }
        
        try:
            response = requests.post(
                "http://localhost:5001/api/memory/store",
                json=memory_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                stored_count += 1
                print(f"✅ Stored: {fact_data['content']}")
            else:
                print(f"❌ Failed: {fact_data['content']} - {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error storing: {str(e)}")
    
    print(f"\n🎯 Stored {stored_count} identity facts")
    
    # Wait a moment for indexing
    time.sleep(2)
    
    print(f"\n🔍 TESTING RETRIEVAL")
    print("-" * 20)
    
    test_queries = [
        "What do you know about me",
        "J.P.",
        "my name", 
        "where do I work",
        "Swift"
    ]
    
    for query in test_queries:
        try:
            payload = {
                "user_id": "global_user",
                "query": query,
                "limit": 8,
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
                
                # Look for identity facts specifically
                identity_facts_found = []
                other_memories = []
                
                for memory in memories:
                    content = memory.get("content", "")
                    metadata = memory.get("metadata", {})
                    memory_type = metadata.get("type", "unknown")
                    score = memory.get("similarity_score", 0)
                    
                    if memory_type == "identity_fact":
                        identity_facts_found.append((content, score))
                    else:
                        other_memories.append((content, score))
                
                if identity_facts_found:
                    print(f"   🎯 Found {len(identity_facts_found)} identity facts:")
                    for content, score in identity_facts_found[:3]:
                        print(f"      • {content} (score: {score:.3f})")
                else:
                    print(f"   ❌ No identity facts found")
                    print(f"   📄 Found {len(other_memories)} other memories")
                    for content, score in other_memories[:2]:
                        print(f"      • {content[:50]}... (score: {score:.3f})")
                    
            else:
                print(f"❌ Query failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing query: {str(e)}")

    print(f"\n🎯 SUMMARY")
    print("-" * 10)
    print("If identity facts show up above, the memory system is working!")
    print("If not, there may be a similarity matching or storage issue.")

if __name__ == "__main__":
    complete_memory_test()
