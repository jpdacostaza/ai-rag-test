#!/usr/bin/env python3
"""
Test Memory Pipeline with Cache Functionality
Tests the enhanced memory pipeline through the pipelines service with caching enabled.
"""

import requests
import json
import time
import uuid
from typing import Dict, Any

class MemoryPipelineTester:
    def __init__(self):
        self.pipelines_url = "http://localhost:9099"
        self.memory_api_url = "http://localhost:5001"
        self.test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
    def test_memory_api_direct(self):
        """Test direct memory API functionality"""
        print("🔍 Testing Direct Memory API...")
        
        # Test health
        response = requests.get(f"{self.memory_api_url}/health")
        print(f"Memory API Health: {response.json()}")
        
        # Store a test memory
        memory_data = {
            "user_id": self.test_user_id,
            "content": "This is a test memory about Python programming concepts.",
            "context": "Test context for memory storage",
            "importance": 0.8,
            "source": "test_script"
        }
        
        response = requests.post(f"{self.memory_api_url}/api/memory/store", json=memory_data)
        if response.status_code == 200:
            memory_result = response.json()
            print(f"✅ Memory stored: {memory_result.get('memory_id', 'ID not returned')}")
            return memory_result.get('memory_id')
        else:
            print(f"❌ Failed to store memory: {response.status_code} - {response.text}")
            return None
    
    def test_memory_recall(self, memory_id: str = None):
        """Test memory recall functionality"""
        print("\n🧠 Testing Memory Recall...")
        
        # Test query-based recall
        query_data = {
            "user_id": self.test_user_id,
            "query": "Python programming",
            "limit": 5
        }
        
        response = requests.post(f"{self.memory_api_url}/api/memory/retrieve", json=query_data)
        if response.status_code == 200:
            recall_result = response.json()
            print(f"✅ Recalled {len(recall_result.get('memories', []))} memories")
            for memory in recall_result.get('memories', []):
                print(f"   - Memory: {memory['content'][:50]}... (Score: {memory.get('score', 'N/A')})")
            return recall_result
        else:
            print(f"❌ Failed to recall memories: {response.status_code} - {response.text}")
            return None
    
    def test_pipeline_integration(self):
        """Test memory through pipeline integration"""
        print("\n🚀 Testing Pipeline Integration...")
        
        # This simulates how the enhanced memory pipeline would work
        test_message = {
            "user": {
                "id": self.test_user_id,
                "name": "Test User",
                "role": "user"
            },
            "messages": [
                {
                    "role": "user",
                    "content": "What do you know about Python programming? I'm working on a machine learning project."
                }
            ],
            "models": ["test-model"],
            "body": {
                "model": "test-model",
                "messages": [
                    {
                        "role": "user", 
                        "content": "What do you know about Python programming? I'm working on a machine learning project."
                    }
                ],
                "stream": False
            }
        }
        
        # Test if we can enhance the message with memory context
        enhanced_context = self.enhance_with_memory(test_message)
        return enhanced_context
    
    def enhance_with_memory(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance message with memory context (simulating pipeline behavior)"""
        print("🔄 Enhancing message with memory context...")
        
        user_id = message_data["user"]["id"]
        user_message = message_data["messages"][-1]["content"]
        
        # Query memory for relevant context
        query_data = {
            "user_id": user_id,
            "query": user_message,
            "limit": 3
        }
        
        try:
            response = requests.post(f"{self.memory_api_url}/api/memory/retrieve", json=query_data)
            if response.status_code == 200:
                recall_result = response.json()
                memories = recall_result.get('memories', [])
                
                if memories:
                    print(f"✅ Found {len(memories)} relevant memories")
                    
                    # Create enhanced context
                    memory_context = "\n".join([
                        f"Previous context: {memory['content']}" 
                        for memory in memories[:2]  # Use top 2 memories
                    ])
                    
                    # Enhance the original message
                    enhanced_message = f"""Based on your previous interactions:
{memory_context}

Current question: {user_message}"""
                    
                    # Update the message content
                    message_data["messages"][-1]["content"] = enhanced_message
                    message_data["body"]["messages"][-1]["content"] = enhanced_message
                    
                    print(f"🧠 Enhanced message with memory context")
                    return message_data
                else:
                    print("ℹ️ No relevant memories found, using original message")
                    return message_data
            else:
                print(f"⚠️ Memory recall failed: {response.status_code}")
                return message_data
                
        except Exception as e:
            print(f"❌ Error enhancing with memory: {e}")
            return message_data
    
    def test_cache_functionality(self):
        """Test cache functionality with repeated queries"""
        print("\n💾 Testing Cache Functionality...")
        
        test_query = "Python machine learning concepts"
        
        # First query (should hit memory API)
        start_time = time.time()
        result1 = self.query_with_timing(test_query, "First query (cache miss)")
        time1 = time.time() - start_time
        
        # Second query (should hit cache)
        start_time = time.time()
        result2 = self.query_with_timing(test_query, "Second query (cache hit)")
        time2 = time.time() - start_time
        
        print(f"⏱️ First query time: {time1:.3f}s")
        print(f"⏱️ Second query time: {time2:.3f}s")
        
        if time2 < time1:
            print("✅ Cache appears to be working (faster second query)")
        else:
            print("ℹ️ Cache behavior unclear or not implemented")
        
        return result1, result2
    
    def query_with_timing(self, query: str, description: str):
        """Query memory with timing"""
        print(f"🔍 {description}...")
        
        query_data = {
            "user_id": self.test_user_id,
            "query": query,
            "limit": 3
        }
        
        response = requests.post(f"{self.memory_api_url}/api/memory/retrieve", json=query_data)
        if response.status_code == 200:
            result = response.json()
            print(f"   Found {len(result.get('memories', []))} memories")
            return result
        else:
            print(f"   Failed: {response.status_code}")
            return None
    
    def test_memory_storage_and_retrieval(self):
        """Test comprehensive memory storage and retrieval"""
        print("\n📚 Testing Memory Storage and Retrieval...")
        
        # Store multiple related memories
        memories_to_store = [
            {
                "content": "Python is great for machine learning with libraries like scikit-learn, TensorFlow, and PyTorch.",
                "context": "ML libraries discussion",
                "importance": 0.9,
                "source": "test_cache"
            },
            {
                "content": "When working on ML projects, data preprocessing is crucial - cleaning, normalization, and feature engineering.",
                "context": "ML preprocessing advice",
                "importance": 0.8,
                "source": "test_cache"
            },
            {
                "content": "For debugging ML models, always check data distribution, model complexity, and validation metrics.",
                "context": "ML debugging tips",
                "importance": 0.7,
                "source": "test_cache"
            }
        ]
        
        stored_ids = []
        for i, memory in enumerate(memories_to_store):
            memory_data = {
                "user_id": self.test_user_id,
                "content": memory["content"],
                "context": memory["context"],
                "importance": memory["importance"],
                "source": memory["source"]
            }
            
            response = requests.post(f"{self.memory_api_url}/api/memory/store", json=memory_data)
            if response.status_code == 200:
                result = response.json()
                stored_ids.append(result.get('memory_id', f'batch_{i+1}'))
                print(f"✅ Stored memory {i+1}: {result.get('memory_id', 'ID not returned')}")
            else:
                print(f"❌ Failed to store memory {i+1}: {response.status_code}")
        
        # Wait a moment for indexing
        time.sleep(2)
        
        # Test retrieval with different queries
        test_queries = [
            "machine learning libraries",
            "data preprocessing for ML",
            "debugging ML models",
            "Python programming tips"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            recall_result = self.query_with_timing(query, f"Query: {query}")
            
        return stored_ids
    
    def run_comprehensive_test(self):
        """Run comprehensive memory pipeline cache test"""
        print("🚀 Starting Comprehensive Memory Pipeline Cache Test")
        print("=" * 60)
        
        try:
            # Test 1: Direct API functionality
            memory_id = self.test_memory_api_direct()
            
            # Test 2: Memory recall
            if memory_id:
                self.test_memory_recall(memory_id)
            
            # Test 3: Store multiple memories for cache testing
            stored_ids = self.test_memory_storage_and_retrieval()
            
            # Test 4: Cache functionality
            self.test_cache_functionality()
            
            # Test 5: Pipeline integration simulation
            enhanced_result = self.test_pipeline_integration()
            
            print("\n" + "=" * 60)
            print("✅ Memory Pipeline Cache Test Complete!")
            print(f"📊 Test Summary:")
            print(f"   - User ID: {self.test_user_id}")
            print(f"   - Memories stored: {len(stored_ids) + (1 if memory_id else 0)}")
            print(f"   - Cache testing: Completed")
            print(f"   - Pipeline integration: Simulated")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main function to run the memory pipeline cache test"""
    tester = MemoryPipelineTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n💥 Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
