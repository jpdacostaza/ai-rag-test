#!/usr/bin/env python3
"""
Web Search Memory Storage Test
=============================
Tests if web search results are being saved to memory storage
"""

import asyncio
import httpx
import json

async def test_memory_storage_with_web_search():
    """Test if web search results get stored in memory"""
    
    print("🔍 Testing Web Search Memory Storage")
    print("=" * 50)
    
    # Test 1: Check if memory API is accessible
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:5001/health")
            if response.status_code == 200:
                print("✅ Memory API is accessible")
            else:
                print("❌ Memory API not responding correctly")
                return
    except Exception as e:
        print(f"❌ Cannot connect to Memory API: {e}")
        return
    
    # Test 2: Simulate a web search interaction through the pipeline
    print("\n📡 Simulating Pipeline Chat with Web Search Trigger")
    
    test_payload = {
        "model": "gemma3:4b",
        "messages": [
            {
                "role": "user", 
                "content": "search the web for latest artificial intelligence developments"
            }
        ],
        "user": {"id": "test_user_websearch", "name": "Test User"}
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Send to pipelines (which should trigger web search)
            response = await client.post(
                "http://localhost:9099/chat/completions",
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Pipeline processed request successfully")
                
                # Check if response contains web search results
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0].get("message", {}).get("content", "")
                    if any(keyword in content.lower() for keyword in ["artificial intelligence", "web search", "search results"]):
                        print("✅ Response appears to contain web search information")
                        print(f"  Sample: {content[:200]}...")
                    else:
                        print("⚠️  Response doesn't clearly show web search results")
                
            else:
                print(f"❌ Pipeline request failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return
                
    except Exception as e:
        print(f"❌ Pipeline request failed: {e}")
        return
    
    # Test 3: Check if the interaction was stored in memory
    print("\n💾 Checking Memory Storage")
    
    try:
        # Wait a bit for storage to complete
        await asyncio.sleep(2)
        
        async with httpx.AsyncClient() as client:
            # Get memories for the test user
            response = await client.post(
                "http://localhost:5001/api/memory/get_memories",
                json={
                    "user_id": "test_user_websearch",
                    "query": "artificial intelligence",
                    "max_memories": 5
                }
            )
            
            if response.status_code == 200:
                memories = response.json()
                print(f"✅ Retrieved {len(memories)} memories for test user")
                
                # Check if any memory contains web search information
                web_search_found = False
                raw_search_found = False
                
                for memory in memories:
                    content = memory.get("content", "").lower()
                    memory_type = memory.get("metadata", {}).get("type", "")
                    
                    # Check for processed web search in conversation
                    if any(keyword in content for keyword in ["web search", "search results", "artificial intelligence", "duckduckgo"]):
                        web_search_found = True
                        print("✅ Found memory containing processed web search information:")
                        print(f"  Content: {memory.get('content', '')[:200]}...")
                        print(f"  Importance: {memory.get('importance_score', 'N/A')}")
                        print(f"  Type: {memory_type}")
                    
                    # Check for raw web search results
                    if memory_type == "web_search_raw":
                        raw_search_found = True
                        print("✅ Found raw web search results in memory:")
                        print(f"  Content: {memory.get('content', '')[:200]}...")
                        print(f"  Query: {memory.get('metadata', {}).get('query', 'N/A')}")
                        print(f"  Search Engine: {memory.get('metadata', {}).get('search_engine', 'N/A')}")
                
                if web_search_found or raw_search_found:
                    print(f"\n📊 Search Memory Summary:")
                    print(f"  Processed search info: {'✅' if web_search_found else '❌'}")
                    print(f"  Raw search results: {'✅' if raw_search_found else '❌'}")
                elif len(memories) > 0:
                    print("⚠️  Memories found but no web search content detected")
                    print("  Latest memory:")
                    print(f"  Content: {memories[0].get('content', '')[:200]}...")
                elif not memories:
                    print("⚠️  No memories found for test user")
                    
            else:
                print(f"❌ Memory retrieval failed: {response.status_code}")
                print(f"  Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Memory retrieval failed: {e}")
    
    # Test 4: Test direct storage of raw search results
    print("\n🔬 Testing Direct Raw Search Storage")
    
    try:
        # Import the web search function
        import sys
        sys.path.insert(0, '.')
        from utilities.enhanced_web_search import search_web
        
        # Perform a direct search
        raw_search_result = await search_web("machine learning trends", max_results=2)
        print(f"✅ Direct search completed: {len(raw_search_result)} characters")
        
        # Test storing this as raw memory
        async with httpx.AsyncClient() as client:
            raw_memory_payload = {
                "user_id": "test_user_websearch",
                "content": f"Raw web search for 'machine learning trends':\n\n{raw_search_result}",
                "metadata": {
                    "type": "web_search_raw",
                    "query": "machine learning trends",
                    "search_engine": "duckduckgo",
                    "importance_override": 0.3
                }
            }
            
            response = await client.post(
                "http://localhost:5001/api/memory/store_memory",
                json=raw_memory_payload
            )
            
            if response.status_code == 200:
                print("✅ Successfully stored raw search results directly to memory")
            else:
                print(f"❌ Failed to store raw search: {response.status_code} - {response.text}")
        
    except Exception as e:
        print(f"❌ Direct raw search storage test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Enhanced Memory Storage Test Complete")
    print("💡 This test shows both conversation-integrated and raw search storage")

if __name__ == "__main__":
    asyncio.run(test_memory_storage_with_web_search())
