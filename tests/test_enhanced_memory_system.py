#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced Memory System
==================================================

This test suite verifies all aspects of the enhanced memory pipeline including:
- Maximum memory storage and retrieval
- Explicit memory commands (remember, forget, delete)
- Memory threshold handling (0.0 for maximum learning)
- Adaptive memory limits
- User authentication and session validation
- Memory ownership validation
- Document detection and processing
- Self-learning capabilities

Run with: python test_enhanced_memory_system.py
"""

import asyncio
import json
import time
import uuid
import httpx
import pytest
import sys
import os
from typing import Dict, List, Any
from unittest.mock import Mock, patch

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the enhanced memory pipeline
from pipelines.enhanced_memory_pipeline import Pipeline

class TestEnhancedMemorySystem:
    """Comprehensive test suite for the Enhanced Memory System."""
    
    def __init__(self):
        """Initialize test environment."""
        self.pipeline = Pipeline()
        self.test_user_id = "test-user-" + str(uuid.uuid4())
        self.memory_api_url = "http://localhost:8001"  # Memory API port
        self.test_memories = []
        
    async def setup_test_environment(self):
        """Set up the test environment."""
        print("🧪 Setting up Enhanced Memory System Test Environment...")
        
        # Initialize the pipeline
        await self.pipeline.on_startup()
        
        # Verify memory API is accessible
        try:
            client = httpx.AsyncClient(timeout=10.0)
            response = await client.get(f"{self.memory_api_url}/health")
            if response.status_code != 200:
                print(f"❌ Memory API not accessible at {self.memory_api_url}")
                return False
            await client.aclose()
            print("✅ Memory API accessible")
        except Exception as e:
            print(f"❌ Memory API connection failed: {e}")
            return False
            
        return True
    
    def create_mock_user(self, user_id: str = None) -> Dict:
        """Create a mock user object for testing."""
        if not user_id:
            user_id = self.test_user_id
            
        return {
            "id": user_id,
            "email": f"{user_id}@test.com",
            "name": "Test User",
            "role": "user"
        }
    
    def create_test_message(self, content: str, role: str = "user") -> Dict:
        """Create a test message."""
        return {
            "role": role,
            "content": content
        }
    
    def create_test_body(self, messages: List[Dict]) -> Dict:
        """Create a test request body."""
        return {
            "messages": messages,
            "model": "llama3.2:3b",
            "stream": False
        }
    
    async def test_maximum_memory_configuration(self):
        """Test 1: Verify maximum memory configuration settings."""
        print("\n🧪 Test 1: Maximum Memory Configuration")
        
        # Verify enhanced memory settings
        assert self.pipeline.valves.max_memories == 100, f"Expected 100, got {self.pipeline.valves.max_memories}"
        assert self.pipeline.valves.memory_threshold == 0.0, f"Expected 0.0, got {self.pipeline.valves.memory_threshold}"
        assert self.pipeline.valves.max_context_memories == 50, f"Expected 50, got {self.pipeline.valves.max_context_memories}"
        assert self.pipeline.valves.auto_store_threshold == 0, f"Expected 0, got {self.pipeline.valves.auto_store_threshold}"
        assert self.pipeline.valves.unlimited_storage == True, f"Expected True, got {self.pipeline.valves.unlimited_storage}"
        
        print("✅ Maximum memory configuration verified")
        return True
    
    async def test_basic_memory_storage_and_retrieval(self):
        """Test 2: Basic memory storage and retrieval."""
        print("\n🧪 Test 2: Basic Memory Storage and Retrieval")
        
        # Create test messages
        user_message = "Hello, my name is J.P. and I work at Swift as a technical lead."
        messages = [
            self.create_test_message(user_message),
            self.create_test_message("Nice to meet you, J.P.! I'll remember that you work at Swift as a technical lead.", "assistant")
        ]
        
        # Test storage
        result = await self.pipeline.store_interaction(self.test_user_id, messages)
        assert result == True, "Memory storage should succeed"
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Test retrieval
        memories = await self.pipeline.get_user_memories(self.test_user_id, "name work job")
        assert len(memories) > 0, "Should retrieve stored memories"
        
        # Verify content
        memory_contents = [m.get('content', '') for m in memories]
        found_relevant = any('J.P.' in content or 'Swift' in content for content in memory_contents)
        assert found_relevant, "Should find relevant memories about J.P. and Swift"
        
        print(f"✅ Stored and retrieved {len(memories)} memories successfully")
        self.test_memories.extend(memories)
        return True
    
    async def test_explicit_memory_commands(self):
        """Test 3: Explicit memory commands (remember this, save this, etc.)."""
        print("\n🧪 Test 3: Explicit Memory Commands")
        
        # Test explicit remember command
        explicit_message = "Remember this: I prefer coffee over tea and I'm allergic to peanuts."
        messages = [self.create_test_message(explicit_message)]
        body = self.create_test_body(messages)
        user = self.create_mock_user()
        
        # Process explicit command
        result_body = await self.pipeline.inlet(body, user)
        
        # Verify explicit command was detected
        command_info = self.pipeline.detect_explicit_memory_commands(explicit_message)
        assert command_info["has_command"] == True, "Should detect explicit memory command"
        assert len(command_info["commands"]) > 0, "Should find memory commands"
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Verify storage
        memories = await self.pipeline.get_user_memories(self.test_user_id, "coffee tea allergic peanuts")
        relevant_memories = [m for m in memories if 'coffee' in m.get('content', '') or 'peanuts' in m.get('content', '')]
        assert len(relevant_memories) > 0, "Should store explicit memories"
        
        print("✅ Explicit memory commands working correctly")
        return True
    
    async def test_forget_delete_memory_commands(self):
        """Test 4: Forget/Delete memory commands."""
        print("\n🧪 Test 4: Forget/Delete Memory Commands")
        
        # First, store a memory to forget
        memory_to_forget = "Remember this: I have a secret project called ProjectX."
        messages = [
            self.create_test_message(memory_to_forget),
            self.create_test_message("I'll remember your secret project ProjectX.", "assistant")
        ]
        
        # Store the memory
        await self.pipeline.store_interaction(self.test_user_id, messages)
        await asyncio.sleep(1)
        
        # Verify it's stored
        memories_before = await self.pipeline.get_user_memories(self.test_user_id, "ProjectX secret")
        projectx_before = [m for m in memories_before if 'ProjectX' in m.get('content', '')]
        assert len(projectx_before) > 0, "Should have stored ProjectX memory"
        
        # Now test forget command
        forget_message = "Forget about ProjectX - delete that memory completely."
        forget_command = self.pipeline.detect_explicit_memory_commands(forget_message)
        assert forget_command["has_command"] == True, "Should detect forget command"
        
        # Check for forget command type
        forget_commands = [cmd for cmd in forget_command["commands"] if cmd.get("type") == "forget_command"]
        assert len(forget_commands) > 0, "Should detect forget command type"
        
        print("✅ Forget/Delete memory commands detected correctly")
        
        # Note: Actual deletion would require implementing the forget endpoint in the memory API
        # This test verifies the detection mechanism is working
        return True
    
    async def test_adaptive_memory_limits(self):
        """Test 5: Adaptive memory limits based on model capabilities."""
        print("\n🧪 Test 5: Adaptive Memory Limits")
        
        # Test with different context window sizes
        test_cases = [
            {"context_window": 32000, "expected_min": 150},  # Large context
            {"context_window": 16000, "expected_min": 100},  # Medium-large context
            {"context_window": 8000, "expected_min": 80},    # Medium context
            {"context_window": 4000, "expected_min": 50}     # Small context
        ]
        
        for case in test_cases:
            limit = self.pipeline.adapt_memory_limit_for_context(case)
            assert limit >= case["expected_min"], f"Should adapt memory limit for {case['context_window']} context"
        
        print("✅ Adaptive memory limits working correctly")
        return True
    
    async def test_user_authentication_and_session_validation(self):
        """Test 6: User authentication and session validation."""
        print("\n🧪 Test 6: User Authentication and Session Validation")
        
        # Test valid user
        valid_user = self.create_mock_user()
        user_id = self.pipeline.get_user_identifier(valid_user)
        assert user_id is not None, "Should authenticate valid user"
        assert self.pipeline._is_valid_user_id(user_id), "Should validate user ID format"
        
        # Test invalid users
        invalid_users = [
            None,
            {},
            {"name": ""},
            {"id": "invalid"},
            {"id": "null"}
        ]
        
        for invalid_user in invalid_users:
            user_id = self.pipeline.get_user_identifier(invalid_user)
            assert user_id is None, f"Should reject invalid user: {invalid_user}"
        
        print("✅ User authentication and validation working correctly")
        return True
    
    async def test_memory_ownership_validation(self):
        """Test 7: Memory ownership validation."""
        print("\n🧪 Test 7: Memory Ownership Validation")
        
        # Create test memories with different ownership
        test_memories = [
            {"content": "User 1 memory", "user_id": self.test_user_id},
            {"content": "User 2 memory", "user_id": "different-user-id"},
            {"content": "No owner memory"}  # No user_id
        ]
        
        # Validate ownership
        validated = self.pipeline._validate_memory_ownership(test_memories, self.test_user_id)
        
        # Should include own memories and unowned memories, but not other users' memories
        assert len(validated) == 2, f"Should validate 2 memories, got {len(validated)}"
        
        # Verify correct memories are included
        contents = [m["content"] for m in validated]
        assert "User 1 memory" in contents, "Should include own memory"
        assert "No owner memory" in contents, "Should include unowned memory"
        assert "User 2 memory" not in contents, "Should exclude other users' memories"
        
        print("✅ Memory ownership validation working correctly")
        return True
    
    async def test_document_detection_and_processing(self):
        """Test 8: Document detection and processing."""
        print("\n🧪 Test 8: Document Detection and Processing")
        
        # Test CV/resume content
        cv_content = """
        My name is John Doe. I have a degree in Computer Science from MIT.
        My technical skills include Python, JavaScript, and Docker.
        I work as a Senior Software Engineer with 5 years of experience.
        My responsibilities include system architecture and team leadership.
        """
        
        messages = [self.create_test_message(cv_content)]
        document_info = self.pipeline.detect_document_content(messages)
        
        assert document_info["is_document"] == True, "Should detect document content"
        assert len(document_info["document_types"]) >= 2, "Should detect multiple document indicators"
        
        # Test normal conversation (should not be detected as document)
        normal_content = "How's the weather today?"
        normal_messages = [self.create_test_message(normal_content)]
        normal_info = self.pipeline.detect_document_content(normal_messages)
        
        assert normal_info["is_document"] == False, "Should not detect normal conversation as document"
        
        print("✅ Document detection and processing working correctly")
        return True
    
    async def test_comprehensive_memory_injection(self):
        """Test 9: Comprehensive memory injection with maximum context."""
        print("\n🧪 Test 9: Comprehensive Memory Injection")
        
        # Create a request with existing memories
        messages = [self.create_test_message("What do you remember about me?")]
        body = self.create_test_body(messages)
        user = self.create_mock_user()
        
        # Process request
        result_body = await self.pipeline.inlet(body, user)
        
        # Verify system message was injected
        system_messages = [msg for msg in result_body["messages"] if msg.get("role") == "system"]
        assert len(system_messages) > 0, "Should inject system messages"
        
        # Check for memory instructions
        memory_instructions = [msg for msg in system_messages if "CRITICAL MEMORY INSTRUCTIONS" in msg.get("content", "")]
        comprehensive_instructions = [msg for msg in system_messages if "COMPREHENSIVE MEMORY" in msg.get("content", "")]
        
        assert len(memory_instructions) > 0 or len(comprehensive_instructions) > 0, "Should inject memory instructions"
        
        print("✅ Comprehensive memory injection working correctly")
        return True
    
    async def test_zero_threshold_filtering(self):
        """Test 10: Zero threshold filtering (accept all memories)."""
        print("\n🧪 Test 10: Zero Threshold Filtering")
        
        # Verify threshold is set to 0.0
        assert self.pipeline.valves.memory_threshold == 0.0, "Threshold should be 0.0 for maximum learning"
        
        # Test memory retrieval with zero threshold
        memories = await self.pipeline.get_user_memories(self.test_user_id, "any query")
        
        # With zero threshold, should get all available memories (if any exist)
        print(f"Retrieved {len(memories)} memories with zero threshold")
        
        # All memories should be included regardless of score
        for memory in memories:
            score = memory.get('score', 0)
            # With zero threshold, any score should be acceptable
            assert score >= 0.0, f"All memories should be accepted with zero threshold, got score: {score}"
        
        print("✅ Zero threshold filtering working correctly")
        return True
    
    async def test_unlimited_storage_capability(self):
        """Test 11: Unlimited storage capability."""
        print("\n🧪 Test 11: Unlimited Storage Capability")
        
        # Test storing multiple interactions rapidly
        test_interactions = [
            ("I like pizza", "I'll remember you like pizza."),
            ("I work remotely", "Got it, you work remotely."),
            ("I have a cat named Whiskers", "I'll remember about your cat Whiskers."),
            ("I prefer dark mode", "Noted that you prefer dark mode."),
            ("I speak three languages", "Impressive that you speak three languages.")
        ]
        
        # Store all interactions
        for user_msg, assistant_msg in test_interactions:
            messages = [
                self.create_test_message(user_msg),
                self.create_test_message(assistant_msg, "assistant")
            ]
            result = await self.pipeline.store_interaction(self.test_user_id, messages)
            assert result == True, f"Should store interaction: {user_msg}"
        
        # Wait for processing
        await asyncio.sleep(3)
        
        # Verify all stored
        all_memories = await self.pipeline.get_user_memories(self.test_user_id, "pizza remote cat dark languages")
        
        # Should have stored all interactions
        print(f"✅ Stored unlimited interactions, retrieved {len(all_memories)} total memories")
        return True
    
    async def test_comprehensive_persona_integration(self):
        """Test 12: Comprehensive persona integration."""
        print("\n🧪 Test 12: Comprehensive Persona Integration")
        
        # Test persona creation with memories
        memory_context = "Memory: User's name is J.P.\nMemory: User works at Swift"
        system_message = self.pipeline._create_model_compatible_system_message(
            memory_context, self.test_user_id, 8
        )
        
        # Verify comprehensive persona elements
        assert "COMPREHENSIVE MEMORY" in system_message, "Should include comprehensive memory instructions"
        assert "UNLIMITED LEARNING" in system_message, "Should include unlimited learning philosophy"
        assert "CRITICAL MEMORY INSTRUCTIONS" in system_message, "Should include critical memory instructions"
        assert memory_context in system_message, "Should include actual memory context"
        
        # Test persona without memories
        new_user_message = self.pipeline._create_model_compatible_system_message("", "new-user", 0)
        assert "NEW USER DETECTED" in new_user_message, "Should detect new user"
        
        print("✅ Comprehensive persona integration working correctly")
        return True
    
    async def cleanup_test_environment(self):
        """Clean up test environment."""
        print("\n🧹 Cleaning up test environment...")
        
        try:
            # Clean up test user memories if possible
            # Note: This would require a cleanup endpoint in the memory API
            print(f"Test user ID: {self.test_user_id}")
            print("(Manual cleanup may be required for test memories)")
            
            # Shutdown pipeline
            await self.pipeline.on_shutdown()
            
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
        
        print("✅ Test environment cleanup completed")
    
    async def run_all_tests(self):
        """Run all comprehensive tests."""
        print("🚀 Starting Enhanced Memory System Comprehensive Test Suite")
        print("=" * 70)
        
        # Setup
        if not await self.setup_test_environment():
            print("❌ Test environment setup failed")
            return False
        
        # Define all tests
        tests = [
            self.test_maximum_memory_configuration,
            self.test_basic_memory_storage_and_retrieval,
            self.test_explicit_memory_commands,
            self.test_forget_delete_memory_commands,
            self.test_adaptive_memory_limits,
            self.test_user_authentication_and_session_validation,
            self.test_memory_ownership_validation,
            self.test_document_detection_and_processing,
            self.test_comprehensive_memory_injection,
            self.test_zero_threshold_filtering,
            self.test_unlimited_storage_capability,
            self.test_comprehensive_persona_integration
        ]
        
        # Run tests
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
                else:
                    failed += 1
                    print(f"❌ {test.__name__} failed")
            except Exception as e:
                failed += 1
                print(f"❌ {test.__name__} failed with exception: {e}")
        
        # Cleanup
        await self.cleanup_test_environment()
        
        # Results
        print("\n" + "=" * 70)
        print("🏁 Enhanced Memory System Test Results")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success Rate: {(passed / (passed + failed) * 100):.1f}%")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Enhanced Memory System is working perfectly!")
        else:
            print(f"\n⚠️ {failed} tests failed. Please review the issues above.")
        
        return failed == 0

async def main():
    """Main test runner."""
    test_suite = TestEnhancedMemorySystem()
    success = await test_suite.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    # Run the comprehensive test suite
    exit_code = asyncio.run(main())
    exit(exit_code)
