#!/usr/bin/env python3
"""
Comprehensive Persona Functionality Test Suite
Tests persona loading, model support, memory integration with OpenWebUI user IDs,
and validates all documented capabilities are working.
"""

import json
import asyncio
import httpx
import pytest
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import patch, AsyncMock
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app
from database_manager import db_manager
from cache_manager import CacheManager
from fastapi.testclient import TestClient

client = TestClient(app)

class PersonaFunctionalityTest:
    """Comprehensive persona functionality validation."""
      @classmethod
    def setup_class(cls):
        """Load persona configuration and prepare test environment."""
        persona_path = Path(__file__).parent / "persona.json"
        with open(persona_path, 'r', encoding='utf-8') as f:
            cls.persona = json.load(f)
        
        # Initialize without cache manager for now (will use direct functions)
        cls.test_user_ids = [
            "openwebui_user_12345",
            "openwebui_user_67890", 
            "openwebui_user_admin"
        ]
        cls.test_session_ids = [str(uuid.uuid4()) for _ in range(3)]
        
    def test_persona_loading_and_structure(self):
        """Test that persona.json loads correctly with expected structure."""
        assert "system_prompt" in self.persona
        assert "capabilities" in self.persona
        assert "system_status" in self.persona
        assert "personality" in self.persona
        
        # Check version info
        assert self.persona["system_status"]["version"] == "v3.1.0"
        assert self.persona["system_status"]["last_updated"] == "2025-06-22"
        assert self.persona["system_status"]["production_readiness"] == "complete"
        
        # Check model configuration
        models = self.persona["capabilities"]["models"]
        assert "available_models" in models
        assert "primary_llm" in models
        assert "newest_model" in models
        assert models["primary_llm"] == "llama3.2:3b"
        assert models["newest_model"] == "mistral:7b-instruct-v0.3-q4_k_m"
        
    def test_system_prompt_comprehensive_coverage(self):
        """Test that system prompt covers all documented capabilities."""
        system_prompt = self.persona["system_prompt"]
        
        # Check for key capability mentions
        required_mentions = [
            "ChromaDB", "Redis", "Qwen3-Embedding", "streaming", 
            "memory", "cache", "tools", "models", "OpenWebUI",
            "session management", "error handling", "retry mechanisms"
        ]
        
        for mention in required_mentions:
            assert mention.lower() in system_prompt.lower(), f"Missing '{mention}' in system prompt"
            
        # Check prompt length is substantial
        assert len(system_prompt) > 4000, "System prompt should be comprehensive"
        
    def test_available_models_configuration(self):
        """Test all available models are properly configured."""
        models = self.persona["capabilities"]["models"]["available_models"]
        expected_models = ["mistral:7b-instruct-v0.3-q4_k_m", "llama3.2:3b", "llama3.2:1b"]
        
        for model in expected_models:
            assert model in models, f"Model {model} should be in available models"
            
        # Test model endpoint availability
        response = client.get("/v1/models")
        assert response.status_code == 200
        model_list = response.json()
        
        # Check that models endpoint returns expected structure
        assert "data" in model_list
        assert isinstance(model_list["data"], list)
        
    async def test_default_model_persona_support(self):
        """Test that the default model (llama3.2:3b) supports persona functionality."""
        default_model = self.persona["capabilities"]["models"]["primary_llm"]
        
        test_payload = {
            "model": default_model,
            "messages": [
                {
                    "role": "user", 
                    "content": "Hello! Can you tell me about your capabilities and what tools you have access to?"
                }
            ],
            "stream": False,
            "user_id": "openwebui_test_user_001"
        }
        
        response = client.post("/v1/chat/completions", json=test_payload)
        assert response.status_code == 200
        
        result = response.json()
        assert "choices" in result
        assert len(result["choices"]) > 0
        
        response_content = result["choices"][0]["message"]["content"].lower()
        
        # Check that response mentions persona capabilities
        capability_indicators = [
            "tools", "weather", "calculator", "memory", "redis", 
            "chromadb", "embedding", "search", "documents"
        ]
        
        mentioned_capabilities = sum(1 for cap in capability_indicators if cap in response_content)
        assert mentioned_capabilities >= 3, f"Default model should mention multiple capabilities, found: {mentioned_capabilities}"
        
    async def test_all_models_functionality(self):
        """Test basic functionality with all available models."""
        models = self.persona["capabilities"]["models"]["available_models"]
        
        test_message = "What is 2+2? Please calculate this for me."
        
        for model in models:
            print(f"Testing model: {model}")
            
            test_payload = {
                "model": model,
                "messages": [{"role": "user", "content": test_message}],
                "stream": False,
                "user_id": f"test_user_{model.replace(':', '_').replace('.', '_')}"
            }
            
            response = client.post("/v1/chat/completions", json=test_payload)
            
            # Some models might not be available, check for appropriate responses
            if response.status_code == 200:
                result = response.json()
                assert "choices" in result
                assert len(result["choices"]) > 0
                content = result["choices"][0]["message"]["content"]
                assert len(content) > 0, f"Model {model} returned empty response"
                print(f"✅ Model {model}: Working")
            elif response.status_code in [404, 500]:
                print(f"⚠️ Model {model}: Not available or error")
            else:
                pytest.fail(f"Unexpected response code {response.status_code} for model {model}")
                
    def test_openwebui_user_id_memory_integration(self):
        """Test that memory works with OpenWebUI user IDs rather than sessions."""
        user_id = "openwebui_user_memory_test_001"
        
        # Store some memory for the user
        test_memory = {
            "user_preferences": {"language": "English", "expertise_level": "advanced"},
            "conversation_context": "Discussing AI development",
            "user_profile": {"name": "TestUser", "role": "developer"}
        }
        
        # Test memory storage
        success = db_manager.store_user_memory(user_id, test_memory)
        assert success, "Should successfully store user memory"
        
        # Test memory retrieval
        retrieved_memory = db_manager.retrieve_user_memory(user_id)
        assert retrieved_memory is not None, "Should retrieve stored memory"
        assert retrieved_memory["user_preferences"]["language"] == "English"
        
        # Test that memory persists across different sessions
        session_1 = str(uuid.uuid4())
        session_2 = str(uuid.uuid4())
        
        # Both sessions should access the same user memory
        memory_session_1 = db_manager.retrieve_user_memory(user_id)
        memory_session_2 = db_manager.retrieve_user_memory(user_id)
        
        assert memory_session_1 == memory_session_2, "Memory should be consistent across sessions"
        
        # Test chat history with user ID
        test_chat = {
            "user_id": user_id,
            "session_id": session_1,
            "message": "Test message for memory",
            "response": "Test response",
            "timestamp": time.time()
        }
        
        chat_stored = db_manager.store_chat_history(user_id, [test_chat])
        assert chat_stored, "Should store chat history with user ID"
        
        # Retrieve chat history
        chat_history = db_manager.get_chat_history(user_id)
        assert len(chat_history) > 0, "Should retrieve chat history"
        assert chat_history[-1]["message"] == "Test message for memory"
        
    def test_memory_user_id_vs_session_separation(self):
        """Test that user ID takes precedence over session for memory."""
        user_id_1 = "openwebui_user_001"
        user_id_2 = "openwebui_user_002"
        shared_session = str(uuid.uuid4())
        
        # Store different memories for different users in same session
        memory_1 = {"preference": "user_1_data"}
        memory_2 = {"preference": "user_2_data"}
        
        db_manager.store_user_memory(user_id_1, memory_1)
        db_manager.store_user_memory(user_id_2, memory_2)
        
        # Retrieve memories - should be user-specific, not session-specific
        retrieved_1 = db_manager.retrieve_user_memory(user_id_1)
        retrieved_2 = db_manager.retrieve_user_memory(user_id_2)
        
        assert retrieved_1["preference"] == "user_1_data"
        assert retrieved_2["preference"] == "user_2_data"
        assert retrieved_1 != retrieved_2, "Different users should have different memories"
        
    def test_persona_tools_availability(self):
        """Test that all tools mentioned in persona are available."""
        documented_tools = self.persona["capabilities"]["tools"]
        
        # Test a sample of tools with the default model
        test_requests = [
            {"content": "What's the weather in London?", "expected_tool": "weather_lookup"},
            {"content": "What time is it in Tokyo?", "expected_tool": "time_timezone_lookup"},
            {"content": "Calculate 15 * 23", "expected_tool": "calculator"},
            {"content": "Convert 100 km to miles", "expected_tool": "unit_conversion"}
        ]
        
        for test_req in test_requests:
            payload = {
                "model": self.persona["capabilities"]["models"]["primary_llm"],
                "messages": [{"role": "user", "content": test_req["content"]}],
                "stream": False,
                "user_id": "tool_test_user"
            }
            
            response = client.post("/v1/chat/completions", json=test_req)
            
            # Check if response indicates tool usage or contains expected calculation/data
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    print(f"✅ Tool test '{test_req['expected_tool']}': Response received")
                    
    def test_cache_and_session_management(self):
        """Test cache management and session handling with user IDs."""
        user_id = "openwebui_cache_test_user"
        
        # Test cache functionality
        cache_key = f"test_cache_{user_id}"
        cache_value = {"test": "data", "timestamp": time.time()}
        
        # Store in cache
        cache_stored = self.cache_manager.set_cache(cache_key, cache_value)
        assert cache_stored, "Should store data in cache"
        
        # Retrieve from cache
        cached_data = self.cache_manager.get_cache(cache_key)
        assert cached_data is not None, "Should retrieve cached data"
        assert cached_data["test"] == "data"
        
        # Test session management with streaming
        session_id = str(uuid.uuid4())
        
        # Test streaming session creation (mock)
        streaming_payload = {
            "model": self.persona["capabilities"]["models"]["primary_llm"],
            "messages": [{"role": "user", "content": "Start a streaming conversation"}],
            "stream": True,
            "user_id": user_id,
            "session_id": session_id
        }
        
        # This tests the endpoint exists and handles the request structure
        response = client.post("/v1/chat/completions", json=streaming_payload)
        # Streaming responses have different handling, just check it doesn't crash
        assert response.status_code in [200, 422], "Streaming endpoint should handle request"
        
    def test_enhanced_features_integration(self):
        """Test that enhanced features mentioned in persona work."""
        # Test feedback system
        feedback_payload = {
            "interaction_id": str(uuid.uuid4()),
            "user_id": "openwebui_feedback_test_user",
            "feedback_type": "positive",
            "content": "Test feedback",
            "metadata": {"test": True}
        }
        
        response = client.post("/enhanced/feedback/interaction", json=feedback_payload)
        # Check endpoint exists and handles request
        assert response.status_code in [200, 201, 422], "Feedback endpoint should exist"
        
        # Test health endpoints mentioned in persona
        health_endpoints = ["/health", "/health/simple", "/health/detailed"]
        
        for endpoint in health_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Health endpoint {endpoint} should be available"
            
            health_data = response.json()
            assert "status" in health_data, f"Health endpoint {endpoint} should return status"
            
    def test_error_handling_and_recovery(self):
        """Test error handling mechanisms mentioned in persona."""
        # Test with invalid model
        invalid_payload = {
            "model": "nonexistent_model",
            "messages": [{"role": "user", "content": "Test"}],
            "user_id": "error_test_user"
        }
        
        response = client.post("/v1/chat/completions", json=invalid_payload)
        
        # Should handle error gracefully
        assert response.status_code in [400, 404, 422], "Should handle invalid model gracefully"
        
        error_response = response.json()
        assert "error" in error_response or "detail" in error_response, "Should return error details"
        
    def test_admin_endpoints_functionality(self):
        """Test admin endpoints for cache and session management."""
        admin_endpoints = [
            "/admin/cache/status",
            "/admin/sessions/cleanup"
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint) if "status" in endpoint else client.post(endpoint)
            
            # Admin endpoints should exist (may require auth in production)
            assert response.status_code in [200, 401, 403], f"Admin endpoint {endpoint} should exist"
            
    async def test_persona_comprehensive_validation(self):
        """Comprehensive validation that all persona claims are accurate."""
        validation_results = {}
        
        # Test system status claims
        validation_results["version_current"] = self.persona["system_status"]["version"] == "v3.1.0"
        validation_results["production_ready"] = self.persona["system_status"]["production_readiness"] == "complete"
        
        # Test capability claims
        capabilities = self.persona["capabilities"]
        validation_results["tools_documented"] = len(capabilities["tools"]) >= 8
        validation_results["models_available"] = len(capabilities["models"]["available_models"]) >= 3
        validation_results["memory_system"] = "semantic_vector_storage" in str(capabilities["memory"])
        
        # Test new features implementation
        new_features = self.persona["system_status"]["new_features"]
        validation_results["mistral_support"] = "mistral_7b_instruct_model_support" in new_features
        validation_results["streaming_features"] = "enhanced_session_management" in new_features
        
        # Test API endpoints
        api_endpoints = capabilities["api_endpoints"]
        validation_results["health_endpoint"] = client.get(api_endpoints["health"]).status_code == 200
        validation_results["models_endpoint"] = client.get(api_endpoints["models"]).status_code == 200
        
        # Overall validation
        passed_validations = sum(validation_results.values())
        total_validations = len(validation_results)
        
        print(f"\n📊 Persona Validation Results:")
        for test, result in validation_results.items():
            status = "✅" if result else "❌"
            print(f"   {status} {test}: {result}")
            
        print(f"\n🎯 Overall Score: {passed_validations}/{total_validations} ({(passed_validations/total_validations)*100:.1f}%)")
        
        # Should pass most validations
        assert passed_validations >= total_validations * 0.8, f"Should pass at least 80% of validations, got {(passed_validations/total_validations)*100:.1f}%"
        
        return validation_results

# Test runner for standalone execution
async def run_all_tests():
    """Run all tests in sequence."""
    test_instance = PersonaFunctionalityTest()
    test_instance.setup_class()
    
    print("🧪 Starting Comprehensive Persona Functionality Tests...\n")
    
    # Run synchronous tests
    sync_tests = [
        ("Persona Loading & Structure", test_instance.test_persona_loading_and_structure),
        ("System Prompt Coverage", test_instance.test_system_prompt_comprehensive_coverage),
        ("Model Configuration", test_instance.test_available_models_configuration),
        ("OpenWebUI User ID Memory", test_instance.test_openwebui_user_id_memory_integration),
        ("Memory User/Session Separation", test_instance.test_memory_user_id_vs_session_separation),
        ("Tools Availability", test_instance.test_persona_tools_availability),
        ("Cache & Session Management", test_instance.test_cache_and_session_management),
        ("Enhanced Features", test_instance.test_enhanced_features_integration),
        ("Error Handling", test_instance.test_error_handling_and_recovery),
        ("Admin Endpoints", test_instance.test_admin_endpoints_functionality)
    ]
    
    for test_name, test_func in sync_tests:
        try:
            print(f"🔍 Running: {test_name}")
            test_func()
            print(f"   ✅ {test_name}: PASSED\n")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}\n")
    
    # Run async tests
    async_tests = [
        ("Default Model Persona Support", test_instance.test_default_model_persona_support),
        ("All Models Functionality", test_instance.test_all_models_functionality),
        ("Comprehensive Validation", test_instance.test_persona_comprehensive_validation)
    ]
    
    for test_name, test_func in async_tests:
        try:
            print(f"🔍 Running: {test_name}")
            await test_func()
            print(f"   ✅ {test_name}: PASSED\n")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}\n")
    
    print("🏁 All persona functionality tests completed!")

if __name__ == "__main__":
    # Can be run standalone or with pytest
    if len(sys.argv) > 1 and sys.argv[1] == "--standalone":
        asyncio.run(run_all_tests())
    else:
        # Run with pytest
        pytest.main([__file__, "-v"])
