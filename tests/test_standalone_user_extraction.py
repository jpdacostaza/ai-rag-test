#!/usr/bin/env python3
"""
Standalone User ID Extraction Test

This test validates user ID extraction logic without requiring
the full system to be imported. It tests the core logic independently.
"""

import pytest
import json
from typing import Dict, List, Any, Optional


def extract_user_id_from_request(request_data: Dict[str, Any]) -> str:
    """
    Extract user ID from request data with priority handling.
    
    Priority order:
    1. Pipeline injection (AUTHENTICATED_USER_ID in system messages)
    2. Email from user object
    3. ID from user object
    4. Username from user object
    5. Name from user object
    6. "anonymous" fallback
    """
    # Check for pipeline injection in messages
    messages = request_data.get("messages", [])
    for msg in messages:
        if msg.get("role") == "system":
            content = msg.get("content", "")
            if "AUTHENTICATED_USER_ID:" in content:
                for line in content.split('\n'):
                    if "AUTHENTICATED_USER_ID:" in line:
                        user_id = line.split("AUTHENTICATED_USER_ID:")[1].strip()
                        if user_id:
                            return user_id
    
    # Check user object with priority
    user = request_data.get("user", {})
    if isinstance(user, dict):
        # Priority order: email > id > username > name
        for field in ["email", "id", "username", "name"]:
            value = user.get(field)
            if value and str(value).strip():
                return str(value).strip()
    
    return "anonymous"


class TestStandaloneUserExtraction:
    """Standalone tests for user ID extraction"""
    
    def test_pipeline_injection_priority(self):
        """Test pipeline injection has highest priority"""
        request = {
            "messages": [
                {"role": "system", "content": "You are helpful.\nAUTHENTICATED_USER_ID: pipeline_user_999"},
                {"role": "user", "content": "Hello"}
            ],
            "user": {
                "email": "other@example.com",
                "id": "other_id"
            }
        }
        
        result = extract_user_id_from_request(request)
        assert result == "pipeline_user_999"
    
    def test_email_priority_over_id(self):
        """Test email takes priority over ID"""
        request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "user": {
                "email": "priority@example.com",
                "id": "backup_id",
                "username": "backup_user"
            }
        }
        
        result = extract_user_id_from_request(request)
        assert result == "priority@example.com"
    
    def test_id_priority_over_username(self):
        """Test ID takes priority over username"""
        request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "user": {
                "id": "primary_id",
                "username": "backup_user",
                "name": "Backup Name"
            }
        }
        
        result = extract_user_id_from_request(request)
        assert result == "primary_id"
    
    def test_username_priority_over_name(self):
        """Test username takes priority over name"""
        request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "user": {
                "username": "primary_user",
                "name": "Backup Name"
            }
        }
        
        result = extract_user_id_from_request(request)
        assert result == "primary_user"
    
    def test_name_fallback(self):
        """Test name is used as fallback"""
        request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "user": {
                "name": "Only Name Available"
            }
        }
        
        result = extract_user_id_from_request(request)
        assert result == "Only Name Available"
    
    def test_anonymous_fallback(self):
        """Test anonymous fallback when no user data"""
        request = {
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        result = extract_user_id_from_request(request)
        assert result == "anonymous"
    
    def test_empty_user_fields(self):
        """Test handling of empty user fields"""
        request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "user": {
                "email": "",
                "id": "",
                "username": "",
                "name": ""
            }
        }
        
        result = extract_user_id_from_request(request)
        assert result == "anonymous"
    
    def test_none_user_fields(self):
        """Test handling of None user fields"""
        request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "user": {
                "email": None,
                "id": None,
                "username": None,
                "name": None
            }
        }
        
        result = extract_user_id_from_request(request)
        assert result == "anonymous"
    
    def test_whitespace_user_fields(self):
        """Test handling of whitespace-only user fields"""
        request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "user": {
                "email": "   ",
                "id": "\t",
                "username": "\n",
                "name": "  \t\n  "
            }
        }
        
        result = extract_user_id_from_request(request)
        assert result == "anonymous"
    
    def test_multiple_pipeline_injections(self):
        """Test first pipeline injection is used"""
        request = {
            "messages": [
                {"role": "system", "content": "AUTHENTICATED_USER_ID: first_user"},
                {"role": "system", "content": "AUTHENTICATED_USER_ID: second_user"},
                {"role": "user", "content": "Hello"}
            ]
        }
        
        result = extract_user_id_from_request(request)
        assert result == "first_user"
    
    def test_pipeline_injection_multiline(self):
        """Test pipeline injection in multiline system message"""
        request = {
            "messages": [
                {
                    "role": "system", 
                    "content": """You are a helpful assistant.
                    
AUTHENTICATED_USER_ID: multiline_user_123

Please be helpful and informative."""
                },
                {"role": "user", "content": "Hello"}
            ]
        }
        
        result = extract_user_id_from_request(request)
        assert result == "multiline_user_123"
    
    def test_invalid_user_object(self):
        """Test handling of invalid user object"""
        request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "user": "invalid_string_user"
        }
        
        result = extract_user_id_from_request(request)
        assert result == "anonymous"
    
    def test_null_user_object(self):
        """Test handling of null user object"""
        request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "user": None
        }
        
        result = extract_user_id_from_request(request)
        assert result == "anonymous"


class TestMemoryIsolationLogic:
    """Test memory isolation logic"""
    
    def test_user_memory_separation(self):
        """Test that user memory keys are properly separated"""
        def generate_memory_key(user_id: str, content_type: str = "general") -> str:
            """Generate memory key for user isolation"""
            return f"memory:{user_id}:{content_type}"
        
        user1_id = "user1@example.com"
        user2_id = "user2@example.com"
        
        user1_key = generate_memory_key(user1_id, "conversations")
        user2_key = generate_memory_key(user2_id, "conversations")
        
        assert user1_key != user2_key
        assert user1_id in user1_key
        assert user2_id in user2_key
        assert user1_id not in user2_key
        assert user2_id not in user1_key
    
    def test_memory_search_isolation(self):
        """Test memory search with user isolation"""
        # Mock memory store
        memory_store = {
            "memory:alice@test.com:general": [
                {"content": "Alice likes coffee", "timestamp": "2025-01-01"}
            ],
            "memory:bob@test.com:general": [
                {"content": "Bob likes tea", "timestamp": "2025-01-01"}
            ]
        }
        
        def search_user_memories(user_id: str, query: str):
            """Search memories for specific user"""
            user_key = f"memory:{user_id}:general"
            user_memories = memory_store.get(user_key, [])
            
            # Simple search logic
            results = []
            for memory in user_memories:
                if query.lower() in memory["content"].lower():
                    results.append(memory)
            
            return results
        
        # Alice searches for "coffee"
        alice_results = search_user_memories("alice@test.com", "coffee")
        assert len(alice_results) == 1
        assert "Alice likes coffee" in alice_results[0]["content"]
        
        # Bob searches for "coffee" (should find nothing)
        bob_results = search_user_memories("bob@test.com", "coffee")
        assert len(bob_results) == 0
        
        # Bob searches for "tea"
        bob_tea_results = search_user_memories("bob@test.com", "tea")
        assert len(bob_tea_results) == 1
        assert "Bob likes tea" in bob_tea_results[0]["content"]


class TestSystemMessageInjection:
    """Test system message injection logic"""
    
    def test_inject_user_id_new_system_message(self):
        """Test injecting user ID into new system message"""
        def inject_user_id(messages: List[Dict], user_id: str) -> List[Dict]:
            """Inject user ID into system message"""
            new_messages = messages.copy()
            
            system_message = {
                "role": "system",
                "content": f"AUTHENTICATED_USER_ID: {user_id}"
            }
            
            # Insert at beginning if no system message exists
            if not new_messages or new_messages[0]["role"] != "system":
                new_messages.insert(0, system_message)
            else:
                # Update existing system message
                new_messages[0]["content"] += f"\nAUTHENTICATED_USER_ID: {user_id}"
            
            return new_messages
        
        original_messages = [
            {"role": "user", "content": "Hello"}
        ]
        
        result = inject_user_id(original_messages, "test_user_123")
        
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert "AUTHENTICATED_USER_ID: test_user_123" in result[0]["content"]
        assert result[1]["role"] == "user"
        assert result[1]["content"] == "Hello"
    
    def test_inject_user_id_existing_system_message(self):
        """Test injecting user ID into existing system message"""
        def inject_user_id(messages: List[Dict], user_id: str) -> List[Dict]:
            """Inject user ID into system message"""
            new_messages = messages.copy()
            
            if new_messages and new_messages[0]["role"] == "system":
                # Update existing system message
                new_messages[0]["content"] += f"\nAUTHENTICATED_USER_ID: {user_id}"
            else:
                # Insert new system message
                system_message = {
                    "role": "system",
                    "content": f"AUTHENTICATED_USER_ID: {user_id}"
                }
                new_messages.insert(0, system_message)
            
            return new_messages
        
        original_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"}
        ]
        
        result = inject_user_id(original_messages, "test_user_456")
        
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert "You are a helpful assistant." in result[0]["content"]
        assert "AUTHENTICATED_USER_ID: test_user_456" in result[0]["content"]


def run_standalone_tests():
    """Run standalone tests with pytest"""
    print("🧪 Running Standalone User ID Extraction Tests")
    print("=" * 60)
    
    # Run pytest on this file
    import pytest
    import sys
    
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    
    print("\n" + "=" * 60)
    if exit_code == 0:
        print("✅ All standalone tests passed!")
        print("🎉 User ID extraction logic is working correctly")
    else:
        print("❌ Some standalone tests failed")
        print("🔧 Please review the test output above")
    
    return exit_code == 0


if __name__ == "__main__":
    success = run_standalone_tests()
    exit(0 if success else 1)
