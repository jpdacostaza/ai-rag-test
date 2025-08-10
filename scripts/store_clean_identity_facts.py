#!/usr/bin/env python3
"""
Store clean identity facts from existing conversation data
This will migrate the existing poor-quality memories to high-quality identity facts
"""

import requests
import json
from datetime import datetime

def store_clean_identity_facts():
    """Store clean, high-quality identity facts"""
    
    print("🔧 STORING CLEAN IDENTITY FACTS")
    print("=" * 40)
    
    # Clean, explicit identity facts to store
    identity_facts = [
        {
            "content": "User's name is J.P.",
            "metadata": {
                "type": "identity_fact",
                "source": "user_statement",
                "timestamp": datetime.now().isoformat(),
                "keywords": "name j.p. jp user",
                "importance": 0.95  # Very high importance
            }
        },
        {
            "content": "User works at Swift",
            "metadata": {
                "type": "identity_fact", 
                "source": "user_statement",
                "timestamp": datetime.now().isoformat(),
                "keywords": "work swift company job",
                "importance": 0.95  # Very high importance
            }
        },
        {
            "content": "Swift is a financial messaging company that provides banking services and interbank communication systems",
            "metadata": {
                "type": "context_fact",
                "source": "enhanced_knowledge", 
                "timestamp": datetime.now().isoformat(),
                "keywords": "swift financial messaging banking interbank",
                "importance": 0.8
            }
        }
    ]
    
    memories_stored = 0
    
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
                memories_stored += 1
                print(f"✅ Stored: {fact_data['content']}")
            else:
                print(f"❌ Failed to store: {fact_data['content']} - Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error storing fact: {str(e)}")
    
    print(f"\n🎯 Successfully stored {memories_stored} high-quality identity facts")
    
    # Test retrieval
    print("\n🔍 TESTING RETRIEVAL")
    print("=" * 20)
    
    test_queries = ["what do you know about me", "J.P.", "who am i"]
    
    for query in test_queries:
        try:
            payload = {
                "user_id": "global_user",
                "query": query,
                "limit": 5
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
                
                # Show identity facts first
                identity_facts = [m for m in memories if m.get("metadata", {}).get("type") == "identity_fact"]
                if identity_facts:
                    print("   🎯 Identity facts:")
                    for fact in identity_facts[:3]:
                        content = fact.get("content", "")
                        score = fact.get("similarity_score", 0)
                        print(f"      • {content} (score: {score:.3f})")
                else:
                    print("   ❌ No identity facts found")
                    
            else:
                print(f"❌ Retrieval failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing query '{query}': {str(e)}")

if __name__ == "__main__":
    store_clean_identity_facts()
