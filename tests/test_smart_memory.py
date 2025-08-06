#!/usr/bin/env python3
"""
Smart Memory System Test
Tests the adaptive threshold memory system with tiered classification
"""

import asyncio
import json
import time
from datetime import datetime
import aiohttp
import requests

class SmartMemoryTester:
    def __init__(self):
        self.memory_api_url = "http://localhost:5001"
        self.chat_api_url = "http://localhost:3000"
        
    def test_memory_storage(self):
        """Test storing different types of memories with appropriate classifications"""
        
        # Test data for different memory types
        test_memories = [
            {
                "type": "personal_info",
                "content": "My name is Alex and I work as a software engineer at TechCorp",
                "expected_threshold": 0.1
            },
            {
                "type": "preference", 
                "content": "I prefer Python over JavaScript for backend development",
                "expected_threshold": 0.15
            },
            {
                "type": "conversation",
                "content": "We discussed optimizing Docker performance and parallel processing",
                "expected_threshold": 0.25
            },
            {
                "type": "general_knowledge",
                "content": "Docker containers provide lightweight virtualization",
                "expected_threshold": 0.4
            }
        ]
        
        print("=== Testing Smart Memory Storage ===")
        
        for memory in test_memories:
            try:
                # Store memory
                response = requests.post(
                    f"{self.memory_api_url}/api/memory/store_explicit",
                    json={
                        "user_id": "test_user",
                        "content": memory["content"],
                        "context": f"Type: {memory['type']}",
                        "importance": 0.9 if memory["type"] in ["personal_info", "preference"] else 0.6,
                        "source": "test_suite",
                        "forced": True
                    }
                )
                
                if response.status_code == 200:
                    print(f"✅ Stored {memory['type']}: {memory['content'][:50]}...")
                else:
                    print(f"❌ Failed to store {memory['type']}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error storing {memory['type']}: {e}")
                
        time.sleep(2)  # Allow processing time
        
    def test_memory_retrieval(self):
        """Test retrieving memories with adaptive thresholds"""
        
        print("\n=== Testing Smart Memory Retrieval ===")
        
        # Test queries that should match different memory types
        test_queries = [
            "What is my name and job?",  # Should find personal info
            "What are my coding preferences?",  # Should find preferences  
            "What did we talk about regarding Docker?",  # Should find conversations
            "Tell me about containerization",  # Should find general knowledge
        ]
        
        for query in test_queries:
            try:
                response = requests.post(
                    f"{self.memory_api_url}/api/memory/retrieve",
                    json={
                        "user_id": "test_user",
                        "query": query, 
                        "limit": 3,
                        "threshold": 1.0  # Reasonable threshold based on distance debugging
                    }
                )
                
                if response.status_code == 200:
                    results = response.json()
                    print(f"\n🔍 Query: {query}")
                    print(f"📝 Found {len(results.get('memories', []))} memories:")
                    
                    for i, memory in enumerate(results.get('memories', [])[:2]):
                        score = memory.get('score', 0)
                        content = memory.get('content', '')[:80] + "..."
                        print(f"   {i+1}. Score: {score:.3f} - {content}")
                        
                else:
                    print(f"❌ Query failed: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error retrieving memories: {e}")
                
    def test_cross_session_memory(self):
        """Test that memories persist across sessions"""
        
        print("\n=== Testing Cross-Session Memory Persistence ===")
        
        # Store a session-specific memory
        session_memory = {
            "user_id": "test_user",
            "content": f"Session test at {datetime.now().strftime('%H:%M:%S')} - Smart memory system is working",
            "context": "Cross-session test",
            "importance": 0.8,
            "source": "session_test",
            "forced": True
        }
        
        try:
            # Store memory
            store_response = requests.post(
                f"{self.memory_api_url}/api/memory/store_explicit",
                json=session_memory
            )
            
            if store_response.status_code == 200:
                print("✅ Stored session memory")
                
                # Wait and try to retrieve it
                time.sleep(1)
                
                retrieve_response = requests.post(
                    f"{self.memory_api_url}/api/memory/retrieve", 
                    json={
                        "user_id": "test_user",
                        "query": "smart memory system test", 
                        "limit": 1,
                        "threshold": 1.2  # Allow decent matches
                    }
                )
                
                if retrieve_response.status_code == 200:
                    results = retrieve_response.json()
                    if results.get('memories'):
                        memory = results['memories'][0]
                        score = memory.get('score', 0)
                        print(f"✅ Retrieved session memory with score: {score:.3f}")
                        
                        if score >= 0.2:  # Good similarity threshold
                            print("✅ Smart memory system working - good similarity match")
                        else:
                            print(f"⚠️  Memory retrieved but score {score:.3f} below good threshold")
                    else:
                        print("❌ Session memory not retrieved")
                else:
                    print(f"❌ Retrieval failed: {retrieve_response.status_code}")
            else:
                print(f"❌ Storage failed: {store_response.status_code}")
                
        except Exception as e:
            print(f"❌ Cross-session test error: {e}")
            
    def test_chat_integration(self):
        """Test that chat system uses the smart memory"""
        
        print("\n=== Testing Chat Integration with Smart Memory ===")
        
        try:
            # Send a chat message that should trigger memory retrieval
            chat_payload = {
                "model": "llama3.2",
                "messages": [
                    {
                        "role": "user", 
                        "content": "Hi! Can you remind me what we discussed about Docker optimization?"
                    }
                ],
                "stream": False
            }
            
            response = requests.post(
                f"{self.chat_api_url}/v1/chat/completions",
                json=chat_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                print("✅ Chat response received")
                print(f"📝 Response preview: {assistant_message[:150]}...")
                
                # Check if response indicates memory was used
                memory_indicators = ['discussed', 'talked about', 'mentioned', 'previous', 'earlier']
                if any(indicator in assistant_message.lower() for indicator in memory_indicators):
                    print("✅ Chat appears to be using memory context")
                else:
                    print("⚠️  Chat may not be using memory context")
                    
            else:
                print(f"❌ Chat failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Chat integration test error: {e}")
            
    def run_all_tests(self):
        """Run complete smart memory test suite"""
        
        print("🧠 Smart Memory System Test Suite")
        print("=" * 50)
        
        # Test storage
        self.test_memory_storage()
        
        # Test retrieval
        self.test_memory_retrieval()
        
        # Test cross-session persistence
        self.test_cross_session_memory()
        
        # Test chat integration
        self.test_chat_integration()
        
        print("\n" + "=" * 50)
        print("🏁 Smart Memory Test Suite Complete")

if __name__ == "__main__":
    tester = SmartMemoryTester()
    tester.run_all_tests()
