#!/usr/bin/env python3
"""
Test script to verify the new unified persona with memory and web search capabilities
"""

import requests
import json
import time

def test_persona_integration():
    """Test the new persona with memory awareness and web search"""
    
    print("🧪 TESTING NEW UNIFIED PERSONA INTEGRATION")
    print("=" * 50)
    
    # Test 1: Basic persona check
    print("\n1️⃣ Testing Persona Loading...")
    try:
        response = requests.post(
            "http://localhost:3000/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "qwen2.5:3b",
                "messages": [
                    {"role": "user", "content": "Hi! Can you describe your capabilities? Specifically tell me about your memory and web search features."}
                ],
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print("✅ Persona Response:")
            print(content[:300] + "..." if len(content) > 300 else content)
            
            # Check for key persona elements
            memory_mentions = content.lower().count('memory')
            search_mentions = content.lower().count('search')
            persistent_mentions = content.lower().count('persistent')
            
            print(f"\n📊 Persona Analysis:")
            print(f"   Memory mentions: {memory_mentions}")
            print(f"   Search mentions: {search_mentions}")
            print(f"   Persistent mentions: {persistent_mentions}")
            
            if memory_mentions >= 2 and search_mentions >= 1:
                print("✅ NEW PERSONA IS ACTIVE!")
            else:
                print("⚠️  Persona may not be fully loaded")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Web Search Function
    print("\n2️⃣ Testing Web Search Function...")
    try:
        response = requests.post(
            "http://localhost:3000/tools/web_search",
            headers={"Content-Type": "application/json"},
            json={
                "query": "AI developments August 2025",
                "max_results": 2
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Web Search Working!")
                print(f"   Query: {result.get('query')}")
                search_results = result.get('results', '')
                print(f"   Results preview: {search_results[:150]}...")
            else:
                print("❌ Web search failed")
        else:
            print(f"❌ Web search error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Web search error: {e}")
    
    # Test 3: Memory API Health
    print("\n3️⃣ Testing Memory API Health...")
    try:
        response = requests.get("http://localhost:5001/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print("✅ Memory API Healthy!")
            print(f"   Redis: {health.get('redis_connected')}")
            print(f"   ChromaDB: {health.get('chromadb_connected')}")
            print(f"   Memory Count: {health.get('memory_count')}")
        else:
            print(f"❌ Memory API error: {response.status_code}")
    except Exception as e:
        print(f"❌ Memory API error: {e}")
    
    # Test 4: Introduction with Memory Test
    print("\n4️⃣ Testing Introduction + Memory Awareness...")
    try:
        response = requests.post(
            "http://localhost:3000/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "qwen2.5:3b",
                "messages": [
                    {"role": "user", "content": "Hello! My name is J.P. and I work at Swift Technologies. I'm testing your memory capabilities. Can you search for recent AI news and remember my details?"}
                ],
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print("✅ Introduction + Memory Test:")
            print(content[:400] + "..." if len(content) > 400 else content)
            
            # Check for memory acknowledgment
            if any(phrase in content.lower() for phrase in ['remember', 'j.p.', 'swift']):
                print("✅ Memory acknowledgment detected!")
            else:
                print("⚠️  No clear memory acknowledgment")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🏁 INTEGRATION TEST COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    test_persona_integration()
