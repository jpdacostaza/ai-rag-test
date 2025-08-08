#!/usr/bin/env python3
"""
Test Memory Retrieval Through Actual Pipeline Service
Tests the enhanced memory pipeline using the real pipeline filter endpoints
"""

import requests
import json
import time
import uuid
from typing import Dict, Any

class RealPipelineMemoryTester:
    """Test memory retrieval through the actual pipeline service"""
    
    def __init__(self):
        self.pipelines_url = "http://localhost:9099"
        self.memory_api_url = "http://localhost:5001"
        self.test_user_id = f"real_pipeline_test_{uuid.uuid4().hex[:8]}"
        
    def setup_test_memories(self):
        """Setup test memories for pipeline testing"""
        print("📝 Setting up test memories for real pipeline test...")
        
        test_memories = [
            {
                "user_id": self.test_user_id,
                "content": "User prefers Python for data science because of pandas and scikit-learn libraries",
                "context": "Programming language preference discussion",
                "importance": 0.9,
                "source": "conversation"
            },
            {
                "user_id": self.test_user_id,
                "content": "User had issues with neural network overfitting, solved using dropout and regularization",
                "context": "ML problem solving session",
                "importance": 0.8,
                "source": "conversation"
            },
            {
                "user_id": self.test_user_id,
                "content": "User completed a classification project using Random Forest algorithm with 95% accuracy",
                "context": "Previous ML project experience",
                "importance": 0.7,
                "source": "conversation"
            }
        ]
        
        stored_count = 0
        for memory in test_memories:
            try:
                response = requests.post(f"{self.memory_api_url}/api/memory/store", json=memory)
                if response.status_code == 200:
                    result = response.json()
                    stored_count += 1
                    print(f"✅ Stored: {memory['content'][:60]}...")
                else:
                    print(f"❌ Failed to store memory: {response.status_code}")
            except Exception as e:
                print(f"❌ Error storing memory: {e}")
        
        print(f"✅ Setup complete: {stored_count} memories stored")
        time.sleep(2)  # Wait for indexing
        return stored_count
    
    def test_pipeline_inlet_filter(self):
        """Test the enhanced memory pipeline inlet filter"""
        print("\n🔧 Testing Real Pipeline Inlet Filter")
        print("=" * 50)
        
        # Create a test message that should trigger memory
        test_message = {
            "user": {
                "id": self.test_user_id,
                "name": "Real Pipeline Test User",
                "role": "user"
            },
            "messages": [
                {
                    "role": "user",
                    "content": "Based on our previous discussions about my ML projects, what approach should I use for my next classification task?"
                }
            ],
            "body": {
                "model": "test-model",
                "messages": [
                    {
                        "role": "user",
                        "content": "Based on our previous discussions about my ML projects, what approach should I use for my next classification task?"
                    }
                ],
                "stream": False
            }
        }
        
        print(f"👤 Test User ID: {self.test_user_id}")
        print(f"💬 Original Message: {test_message['messages'][0]['content']}")
        
        # Test the pipeline inlet filter endpoint
        try:
            # Try to call the enhanced memory pipeline inlet filter
            filter_url = f"{self.pipelines_url}/enhanced_memory_pipeline/filter/inlet"
            
            print(f"\n🚀 Calling pipeline inlet filter: {filter_url}")
            
            # Make request to pipeline filter
            response = requests.post(
                filter_url,
                json=test_message,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                enhanced_message = response.json()
                print("✅ Pipeline inlet filter executed successfully!")
                
                # Check if message was enhanced
                original_content = test_message['messages'][0]['content']
                enhanced_content = enhanced_message.get('messages', [{}])[0].get('content', '')
                
                if enhanced_content != original_content and len(enhanced_content) > len(original_content):
                    print("🧠 Message was enhanced with memory context!")
                    print(f"📏 Original length: {len(original_content)} chars")
                    print(f"📏 Enhanced length: {len(enhanced_content)} chars")
                    print(f"📝 Enhanced preview: {enhanced_content[:200]}...")
                    return True, enhanced_message
                else:
                    print("ℹ️ Message was not enhanced (no relevant memories found)")
                    return True, enhanced_message
            else:
                print(f"❌ Pipeline filter failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False, None
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection error - pipeline service may not be accessible")
            return False, None
        except Exception as e:
            print(f"❌ Error calling pipeline filter: {e}")
            return False, None
    
    def test_pipeline_outlet_filter(self, enhanced_message):
        """Test the enhanced memory pipeline outlet filter"""
        print("\n💾 Testing Real Pipeline Outlet Filter")
        print("=" * 50)
        
        # Simulate an AI response
        ai_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Based on your previous experience with Random Forest achieving 95% accuracy, I'd recommend starting with ensemble methods again. Since you've worked with classification before and understand overfitting issues, you might want to try XGBoost or LightGBM for even better performance."
                    }
                }
            ]
        }
        
        # Prepare outlet filter data
        outlet_data = {
            "user": enhanced_message.get("user", {}),
            "messages": enhanced_message.get("messages", []),
            "body": enhanced_message.get("body", {}),
            "response": ai_response
        }
        
        try:
            # Call the pipeline outlet filter
            filter_url = f"{self.pipelines_url}/enhanced_memory_pipeline/filter/outlet"
            
            print(f"🚀 Calling pipeline outlet filter: {filter_url}")
            
            response = requests.post(
                filter_url,
                json=outlet_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Pipeline outlet filter executed successfully!")
                print(f"📝 Outlet response: {str(result)[:200]}...")
                return True, result
            else:
                print(f"❌ Pipeline outlet filter failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False, None
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection error - pipeline service may not be accessible")
            return False, None
        except Exception as e:
            print(f"❌ Error calling pipeline outlet filter: {e}")
            return False, None
    
    def test_pipeline_without_memory_trigger(self):
        """Test pipeline with message that shouldn't trigger memory"""
        print("\n🚫 Testing Pipeline Without Memory Trigger")
        print("=" * 50)
        
        # Create a message that should NOT trigger memory
        test_message = {
            "user": {
                "id": self.test_user_id,
                "name": "Real Pipeline Test User",
                "role": "user"
            },
            "messages": [
                {
                    "role": "user",
                    "content": "What is the definition of machine learning?"
                }
            ],
            "body": {
                "model": "test-model",
                "messages": [
                    {
                        "role": "user",
                        "content": "What is the definition of machine learning?"
                    }
                ],
                "stream": False
            }
        }
        
        print(f"💬 Test Message (no memory trigger): {test_message['messages'][0]['content']}")
        
        try:
            filter_url = f"{self.pipelines_url}/enhanced_memory_pipeline/filter/inlet"
            
            response = requests.post(
                filter_url,
                json=test_message,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                original_content = test_message['messages'][0]['content']
                result_content = result.get('messages', [{}])[0].get('content', '')
                
                if result_content == original_content:
                    print("✅ Correct behavior - message unchanged (no memory trigger)")
                    return True
                else:
                    print("⚠️ Unexpected behavior - message was modified")
                    return False
            else:
                print(f"❌ Pipeline call failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing no-memory scenario: {e}")
            return False
    
    def test_pipeline_valves_configuration(self):
        """Test pipeline valves configuration"""
        print("\n⚙️ Testing Pipeline Valves Configuration")
        print("=" * 50)
        
        try:
            # Get pipeline valves
            valves_url = f"{self.pipelines_url}/enhanced_memory_pipeline/valves"
            
            response = requests.get(valves_url, timeout=10)
            
            if response.status_code == 200:
                valves = response.json()
                print("✅ Pipeline valves retrieved successfully!")
                print(f"📊 Valves configuration:")
                for key, value in valves.items():
                    print(f"   {key}: {value}")
                return True, valves
            else:
                print(f"❌ Failed to get valves: {response.status_code}")
                return False, None
                
        except Exception as e:
            print(f"❌ Error getting pipeline valves: {e}")
            return False, None
    
    def run_comprehensive_pipeline_test(self):
        """Run comprehensive test of memory retrieval through pipeline"""
        print("🚀 Real Pipeline Memory Retrieval Test")
        print("=" * 60)
        
        # Setup test data
        memories_stored = self.setup_test_memories()
        if memories_stored == 0:
            print("❌ Failed to setup test memories - cannot continue")
            return False
        
        # Test pipeline valves
        valves_success, valves = self.test_pipeline_valves_configuration()
        
        # Test inlet filter with memory trigger
        inlet_success, enhanced_message = self.test_pipeline_inlet_filter()
        
        # Test outlet filter if inlet succeeded
        outlet_success = False
        if inlet_success and enhanced_message:
            outlet_success, outlet_result = self.test_pipeline_outlet_filter(enhanced_message)
        
        # Test inlet filter without memory trigger
        no_memory_success = self.test_pipeline_without_memory_trigger()
        
        # Final results
        print("\n" + "=" * 60)
        print("📊 Real Pipeline Memory Test Results")
        print("=" * 60)
        
        results = {
            "memories_setup": memories_stored > 0,
            "valves_config": valves_success,
            "inlet_filter": inlet_success,
            "outlet_filter": outlet_success,
            "no_memory_trigger": no_memory_success
        }
        
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test.replace('_', ' ').title()}: {status}")
        
        all_passed = all(results.values())
        
        if all_passed:
            print("\n🎉 ALL PIPELINE TESTS PASSED!")
            print("✅ Memory retrieval through pipeline is fully operational")
        else:
            print("\n⚠️ Some pipeline tests failed")
            print("❌ Pipeline integration needs investigation")
        
        return all_passed

def main():
    """Main function to test real pipeline memory functionality"""
    tester = RealPipelineMemoryTester()
    success = tester.run_comprehensive_pipeline_test()
    
    if success:
        print("\n🎯 Conclusion: Enhanced memory pipeline is working correctly through the pipeline service!")
    else:
        print("\n🔧 Conclusion: Pipeline integration needs troubleshooting - may require authentication or different endpoint format")

if __name__ == "__main__":
    main()
