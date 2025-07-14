#!/usr/bin/env python3
"""
Memory Pipeline Integration Test
================================

Tests memory store and retrieve functionality through the pipeline using the model.
This test validates the complete flow:
1. Send a conversation request through the pipeline
2. Verify memory storage occurs
3. Send a follow-up request that should use stored memories
4. Validate memory retrieval and context injection

Features tested:
- Pipeline integration with memory system
- Model response generation with memory context
- Memory storage during conversations
- Memory retrieval for context enhancement
- Cross-conversation memory persistence
"""

import asyncio
import time
import json
import httpx
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime

# Configuration
PIPELINES_URL = "http://localhost:9099"
MEMORY_API_URL = "http://localhost:5001"
BACKEND_URL = "http://localhost:3000"
OLLAMA_URL = "http://localhost:11434"

class MemoryPipelineTest:
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        self.test_user_id = f"test_user_{int(time.time())}"
        self.conversation_id = f"test_conv_{int(time.time())}"
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        elapsed = time.time() - self.start_time
        emoji = {
            "INFO": "📝", "SUCCESS": "✅", "WARNING": "⚠️", 
            "ERROR": "❌", "DEBUG": "🔍", "TEST": "🧪", "MEMORY": "🧠"
        }.get(level, "📝")
        print(f"[{timestamp}] {emoji} [{level}] [{elapsed:.1f}s] {message}")
    
    async def check_services_health(self) -> bool:
        """Check if all required services are healthy."""
        self.log("Checking service health...", "TEST")
        
        services = [
            ("Memory API", MEMORY_API_URL, "/health"),
            ("Pipelines", PIPELINES_URL, "/"),
            ("Ollama", OLLAMA_URL, "/api/tags"),
        ]
        
        all_healthy = True
        async with httpx.AsyncClient(timeout=10.0) as client:
            for name, url, endpoint in services:
                try:
                    response = await client.get(f"{url}{endpoint}")
                    if response.status_code == 200:
                        self.log(f"{name}: Healthy", "SUCCESS")
                    else:
                        self.log(f"{name}: Unhealthy ({response.status_code})", "ERROR")
                        all_healthy = False
                except Exception as e:
                    self.log(f"{name}: Connection failed - {e}", "ERROR")
                    all_healthy = False
        
        return all_healthy
    
    async def get_available_models(self) -> List[str]:
        """Get list of available Ollama models."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{OLLAMA_URL}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    self.log(f"Available models: {', '.join(models)}", "INFO")
                    return models
                else:
                    self.log(f"Failed to get models: {response.status_code}", "ERROR")
                    return []
        except Exception as e:
            self.log(f"Error getting models: {e}", "ERROR")
            return []
    
    async def send_pipeline_request(self, message: str, model_name: str) -> Optional[Dict[str, Any]]:
        """Send a request through the pipeline system."""
        try:
            # Create request payload matching OpenWebUI format
            request_payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                "stream": False,
                "user": {
                    "id": self.test_user_id,
                    "name": "Test User",
                    "email": "test@example.com",
                    "role": "user"
                },
                "chat_id": self.conversation_id,
                "session_id": f"session_{self.conversation_id}",
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                self.log(f"Sending request to pipeline: {message[:50]}...", "TEST")
                
                response = await client.post(
                    f"{PIPELINES_URL}/api/v1/chat/completions",
                    json=request_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.log("Pipeline request successful", "SUCCESS")
                    return result
                else:
                    self.log(f"Pipeline request failed: {response.status_code}", "ERROR")
                    self.log(f"Response: {response.text}", "DEBUG")
                    return None
                    
        except Exception as e:
            self.log(f"Pipeline request error: {e}", "ERROR")
            return None
    
    async def check_memory_storage(self, expected_content: str) -> bool:
        """Check if memories were stored correctly."""
        try:
            await asyncio.sleep(2)  # Wait for memory processing
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                retrieval_request = {
                    "user_id": self.test_user_id,
                    "query": expected_content,
                    "limit": 10,
                    "threshold": 0.3
                }
                
                response = await client.post(
                    f"{MEMORY_API_URL}/api/memory/retrieve",
                    json=retrieval_request
                )
                
                if response.status_code == 200:
                    data = response.json()
                    memories = data.get("memories", [])
                    
                    if memories:
                        self.log(f"Found {len(memories)} stored memories", "MEMORY")
                        for i, memory in enumerate(memories[:3]):  # Show first 3
                            content = memory.get("content", "")[:100]
                            self.log(f"  Memory {i+1}: {content}...", "DEBUG")
                        return True
                    else:
                        self.log("No memories found in storage", "WARNING")
                        return False
                else:
                    self.log(f"Memory check failed: {response.status_code}", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"Memory check error: {e}", "ERROR")
            return False
    
    async def test_memory_store_flow(self, model_name: str) -> bool:
        """Test memory storage during conversation."""
        self.log("Testing memory storage flow...", "TEST")
        
        # Send a message with personal information that should be stored
        personal_message = (
            "Hello! My name is Alice Johnson and I work as a software engineer at TechCorp. "
            "I'm 28 years old and I live in San Francisco. I love hiking and photography. "
            "I'm currently working on a machine learning project about image recognition."
        )
        
        response = await self.send_pipeline_request(personal_message, model_name)
        if not response:
            return False
        
        # Extract the assistant's response
        assistant_response = ""
        if "choices" in response and response["choices"]:
            message = response["choices"][0].get("message", {})
            assistant_response = message.get("content", "")
            self.log(f"Assistant response: {assistant_response[:100]}...", "INFO")
        
        # Check if memory was stored
        memory_stored = await self.check_memory_storage("Alice Johnson software engineer")
        
        if memory_stored:
            self.log("Memory storage test PASSED", "SUCCESS")
            return True
        else:
            self.log("Memory storage test FAILED", "ERROR")
            return False
    
    async def test_memory_retrieve_flow(self, model_name: str) -> bool:
        """Test memory retrieval and context injection."""
        self.log("Testing memory retrieval flow...", "TEST")
        
        # Send a follow-up message that should trigger memory retrieval
        followup_message = (
            "What do you remember about my job and hobbies? "
            "Can you remind me what project I'm working on?"
        )
        
        response = await self.send_pipeline_request(followup_message, model_name)
        if not response:
            return False
        
        # Extract the assistant's response
        assistant_response = ""
        if "choices" in response and response["choices"]:
            message = response["choices"][0].get("message", {})
            assistant_response = message.get("content", "")
            self.log(f"Follow-up response: {assistant_response[:200]}...", "INFO")
        
        # Check if the response contains information from stored memories
        memory_indicators = [
            "Alice Johnson", "alice", "software engineer", "TechCorp", 
            "San Francisco", "hiking", "photography", "machine learning", 
            "image recognition"
        ]
        
        response_lower = assistant_response.lower()
        found_indicators = [indicator for indicator in memory_indicators 
                          if indicator.lower() in response_lower]
        
        if found_indicators:
            self.log(f"Memory retrieval PASSED - Found: {', '.join(found_indicators)}", "SUCCESS")
            return True
        else:
            self.log("Memory retrieval FAILED - No stored information found in response", "ERROR")
            self.log(f"Full response: {assistant_response}", "DEBUG")
            return False
    
    async def test_cross_conversation_persistence(self, model_name: str) -> bool:
        """Test that memories persist across different conversation sessions."""
        self.log("Testing cross-conversation persistence...", "TEST")
        
        # Change conversation ID to simulate new conversation
        old_conversation_id = self.conversation_id
        self.conversation_id = f"test_conv_new_{int(time.time())}"
        
        # Send a message in the new conversation asking about previous info
        new_conversation_message = (
            "Hi there! I think we've talked before. "
            "Do you remember anything about my background or interests?"
        )
        
        response = await self.send_pipeline_request(new_conversation_message, model_name)
        if not response:
            self.conversation_id = old_conversation_id  # Restore
            return False
        
        # Extract the assistant's response
        assistant_response = ""
        if "choices" in response and response["choices"]:
            message = response["choices"][0].get("message", {})
            assistant_response = message.get("content", "")
            self.log(f"Cross-conversation response: {assistant_response[:200]}...", "INFO")
        
        # Check if the response contains information from previous conversation
        memory_indicators = ["Alice", "software engineer", "TechCorp", "San Francisco"]
        
        response_lower = assistant_response.lower()
        found_indicators = [indicator for indicator in memory_indicators 
                          if indicator.lower() in response_lower]
        
        self.conversation_id = old_conversation_id  # Restore
        
        if found_indicators:
            self.log(f"Cross-conversation persistence PASSED - Found: {', '.join(found_indicators)}", "SUCCESS")
            return True
        else:
            self.log("Cross-conversation persistence FAILED", "ERROR")
            return False
    
    async def run_full_test_suite(self) -> Dict[str, bool]:
        """Run the complete memory pipeline test suite."""
        self.log("Starting Memory Pipeline Integration Test", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Test User ID: {self.test_user_id}", "INFO")
        self.log(f"Conversation ID: {self.conversation_id}", "INFO")
        self.log("=" * 60, "INFO")
        
        # Check service health first
        services_healthy = await self.check_services_health()
        if not services_healthy:
            self.log("Aborting test - services not healthy", "ERROR")
            return {"Services Health": False}
        
        # Get available models
        models = await self.get_available_models()
        if not models:
            self.log("Aborting test - no models available", "ERROR")
            return {"Services Health": True, "Models Available": False}
        
        # Use the first available model (prefer llama3.2 if available)
        model_name = "llama3.2:3b" if "llama3.2:3b" in models else models[0]
        self.log(f"Using model: {model_name}", "INFO")
        
        # Run test sequence
        tests = [
            ("Services Health", True),  # Already checked
            ("Models Available", True),  # Already checked
            ("Memory Store Flow", await self.test_memory_store_flow(model_name)),
            ("Memory Retrieve Flow", await self.test_memory_retrieve_flow(model_name)),
            ("Cross-Conversation Persistence", await self.test_cross_conversation_persistence(model_name)),
        ]
        
        results = {}
        for test_name, result in tests:
            results[test_name] = result
        
        # Print summary
        self.log("=" * 60, "INFO")
        self.log("MEMORY PIPELINE TEST SUMMARY", "INFO")
        self.log("=" * 60, "INFO")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        self.log(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)", "INFO")
        self.log("", "INFO")
        
        for test_name, result in results.items():
            status = "PASS" if result else "FAIL"
            self.log(f"  [{status}] {test_name}", "SUCCESS" if result else "ERROR")
        
        self.log("=" * 60, "INFO")
        if success_rate == 100:
            self.log("🎉 ALL TESTS PASSED - Memory pipeline fully functional!", "SUCCESS")
        elif success_rate >= 60:
            self.log("⚠️  PARTIAL SUCCESS - Some issues detected", "WARNING")
        else:
            self.log("❌ CRITICAL ISSUES - Memory pipeline needs attention", "ERROR")
        
        total_time = time.time() - self.start_time
        self.log(f"Total test time: {total_time:.1f} seconds", "INFO")
        self.log("=" * 60, "INFO")
        
        return results

async def main():
    """Main test execution."""
    test_suite = MemoryPipelineTest()
    results = await test_suite.run_full_test_suite()
    
    # Exit with appropriate code
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    asyncio.run(main())
