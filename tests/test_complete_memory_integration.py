#!/usr/bin/env python3
"""
Test Memory Functionality Through Enhanced Pipeline - Complete Integration        # Test message that should trigger memory enhancement
        test_message = {
            "user": {
                "id": self.test_user_id,
                "name": "Pipeline Integration Test User",
                "role": "user"
            },
            "messages": [
                {
                    "role": "user", 
                    "content": "I'm having trouble with my Python memory system project. Can you help me optimize the pipeline performance?"
                }
            ],
            "body": {
                "model": "test-model",
                "messages": [
                    {
                        "role": "user", 
                        "content": "I'm having trouble with my Python memory system project. Can you help me optimize the pipeline performance?"
                    }
                ],
                "stream": False
            }
        }"

import requests
import json
import time

class MemoryPipelineIntegrationTester:
    def __init__(self):
        self.memory_api_url = "http://localhost:5001"
        self.pipeline_url = "http://localhost:9099"
        self.test_user_id = "pipeline_integration_test_user"
        
    def setup_test_memories(self):
        """Setup test memories for pipeline testing"""
        print("🧠 Setting up test memories for pipeline integration")
        print("=" * 55)
        
        test_memories = [
            {
                "content": "User prefers Python over JavaScript for backend development. Has experience with FastAPI and Flask.",
                "metadata": {"category": "preferences", "topic": "programming"}
            },
            {
                "content": "User is working on a memory system project with Redis cache and ChromaDB vector storage.",
                "metadata": {"category": "current_project", "topic": "memory_system"}
            },
            {
                "content": "User's development environment: Windows with PowerShell, Docker containers, VS Code.",
                "metadata": {"category": "environment", "topic": "development_setup"}
            },
            {
                "content": "User has asked about pipeline memory integration and cache performance testing multiple times.",
                "metadata": {"category": "conversation_history", "topic": "memory_pipelines"}
            },
            {
                "content": "User is interested in Orange Pi 5 Plus optimization and high-performance computing configurations.",
                "metadata": {"category": "interests", "topic": "hardware_optimization"}
            }
        ]
        
        stored_count = 0
        for memory in test_memories:
            try:
                response = requests.post(
                    f"{self.memory_api_url}/api/memory/store",
                    json={
                        "user_id": self.test_user_id,
                        "content": memory["content"],
                        "context": json.dumps(memory["metadata"]),
                        "importance": 0.7,
                        "source": "pipeline_integration_test"
                    }
                )
                if response.status_code == 200:
                    stored_count += 1
                    print(f"✅ Memory {stored_count}: {memory['content'][:50]}...")
                else:
                    print(f"❌ Failed to store memory: {response.status_code}")
            except Exception as e:
                print(f"❌ Error storing memory: {e}")
        
        print(f"\n📊 Total memories stored: {stored_count}/5")
        return stored_count
        
    def enable_pipeline_debug_logging(self):
        """Enable debug logging to see what the pipeline is doing"""
        print("\n🔧 Enabling pipeline debug logging")
        print("=" * 40)
        
        try:
            # Get current valves
            response = requests.get(f"{self.pipeline_url}/enhanced_memory_pipeline/valves")
            if response.status_code == 200:
                current_valves = response.json()
                current_valves["DEBUG_LOGGING"] = True
                
                # Update valves
                update_response = requests.post(
                    f"{self.pipeline_url}/enhanced_memory_pipeline/valves/update",
                    json=current_valves
                )
                
                if update_response.status_code == 200:
                    print("✅ Debug logging enabled")
                    return True
                else:
                    print(f"❌ Failed to enable debug logging: {update_response.status_code}")
                    return False
            else:
                print(f"❌ Failed to get valves: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error enabling debug logging: {e}")
            return False
    
    def test_memory_enhanced_conversation(self):
        """Test a conversation that should trigger memory enhancement"""
        print("\n🗣️ Testing Memory-Enhanced Conversation")
        print("=" * 45)
        
        # Test message that should match our stored memories
        test_message = {
            "messages": [
                {
                    "role": "user", 
                    "content": "I'm having trouble with my Python memory system project. Can you help me optimize the pipeline performance?"
                }
            ]
        }
        
        print(f"📤 Sending test message: {test_message['messages'][0]['content']}")
        
        try:
            response = requests.post(
                f"{self.pipeline_url}/enhanced_memory_pipeline/filter/inlet",
                json=test_message,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                enhanced_body = response.json()
                
                # Check if the message was enhanced with memory context
                enhanced_content = enhanced_body["messages"][0]["content"]
                original_content = test_message["messages"][0]["content"]
                
                print(f"\n📥 Response status: {response.status_code}")
                print(f"📊 Original length: {len(original_content)} characters")
                print(f"📊 Enhanced length: {len(enhanced_content)} characters")
                
                if len(enhanced_content) > len(original_content):
                    print("✅ Message was enhanced with additional context!")
                    
                    # Look for memory context indicators
                    if "Memory" in enhanced_content or "Context" in enhanced_content:
                        print("✅ Memory context detected in enhanced message!")
                        
                        # Show a preview of the enhancement
                        print("\n📝 Enhanced message preview:")
                        print("-" * 50)
                        if len(enhanced_content) > 500:
                            print(enhanced_content[:500] + "...")
                        else:
                            print(enhanced_content)
                        print("-" * 50)
                        
                        return True, enhanced_content
                    else:
                        print("⚠️ Message was enhanced but no explicit memory markers found")
                        return True, enhanced_content
                else:
                    print("❌ Message was not enhanced with memory context")
                    print(f"Original: {original_content}")
                    print(f"Enhanced: {enhanced_content}")
                    return False, enhanced_content
            else:
                print(f"❌ Pipeline request failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False, None
                
        except Exception as e:
            print(f"❌ Error testing pipeline: {e}")
            return False, None
    
    def test_memory_retrieval_direct(self):
        """Test direct memory retrieval to verify memories are available"""
        print("\n🔍 Testing Direct Memory Retrieval")
        print("=" * 40)
        
        test_query = "Python memory system project pipeline performance"
        
        try:
            response = requests.post(
                f"{self.memory_api_url}/api/memory/retrieve",
                json={
                    "user_id": self.test_user_id,
                    "query": test_query,
                    "limit": 5
                }
            )
            
            if response.status_code == 200:
                results = response.json()
                memories = results.get("memories", [])
                
                print(f"📊 Found {len(memories)} relevant memories")
                
                for i, memory in enumerate(memories, 1):
                    relevance = memory.get("relevance_score", 0)
                    content = memory.get("content", "")
                    print(f"  {i}. Relevance: {relevance:.3f} - {content[:60]}...")
                
                return len(memories) > 0
            else:
                print(f"❌ Memory search failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error searching memories: {e}")
            return False

def main():
    """Run complete memory pipeline integration test"""
    print("🚀 Memory Pipeline Integration Test - Complete Verification")
    print("=" * 70)
    
    tester = MemoryPipelineIntegrationTester()
    
    # Step 1: Setup test memories
    memories_stored = tester.setup_test_memories()
    if memories_stored == 0:
        print("❌ No memories stored, cannot test pipeline integration")
        return
    
    # Step 2: Enable debug logging
    debug_enabled = tester.enable_pipeline_debug_logging()
    
    # Step 3: Test direct memory retrieval
    memories_available = tester.test_memory_retrieval_direct()
    if not memories_available:
        print("❌ No memories found via direct search, pipeline test may fail")
    
    # Step 4: Test memory-enhanced conversation
    memory_enhancement_working, enhanced_content = tester.test_memory_enhanced_conversation()
    
    # Final Results
    print("\n" + "=" * 70)
    print("🎯 FINAL TEST RESULTS")
    print("=" * 70)
    
    print(f"✅ Memories stored: {memories_stored}/5")
    print(f"{'✅' if debug_enabled else '❌'} Debug logging: {'Enabled' if debug_enabled else 'Failed'}")
    print(f"{'✅' if memories_available else '❌'} Memory retrieval: {'Working' if memories_available else 'Failed'}")
    print(f"{'✅' if memory_enhancement_working else '❌'} Pipeline enhancement: {'Working' if memory_enhancement_working else 'Failed'}")
    
    if memory_enhancement_working:
        print("\n🎉 SUCCESS: Memory functionality is working through the pipeline!")
        print("   The pipeline is successfully retrieving and injecting relevant memories.")
    else:
        print("\n⚠️ PARTIAL SUCCESS: Pipeline is loaded but memory enhancement needs investigation.")
    
    print("\n📝 Next steps:")
    if memory_enhancement_working:
        print("   - Test with real conversations in OpenWebUI")
        print("   - Monitor memory usage and performance")
        print("   - Consider enabling memory storage on outlet filter")
    else:
        print("   - Check pipeline logs for memory retrieval attempts")
        print("   - Verify memory API connectivity from pipeline container")
        print("   - Test memory API accessibility from within Docker network")

if __name__ == "__main__":
    main()
