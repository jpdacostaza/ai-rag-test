#!/usr/bin/env python3
"""
Test Suite for Unified Authentication and Validation Service
===========================================================

Comprehensive tests for the AuthValidator service that consolidates scattered 
user validation logic across the memory system.

Test Coverage:
- User ID validation patterns (UUID, email, username, name)
- Priority-based user extraction from requests
- Pipeline injection handling
- Session management and consistency validation
- Configuration flexibility and validation levels
- Error handling and edge cases
- Backward compatibility with existing functions
"""

import pytest
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys
import os

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_validator import (
    AuthValidator,
    AuthConfig,
    UserContext,
    UserIDType,
    ValidationLevel,
    get_auth_validator,
    configure_auth_validator,
    validate_openwebui_user_id,
    extract_authenticated_user_id,
    extract_user_from_request
)


class TestAuthConfig:
    """Test authentication configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = AuthConfig()
        assert config.validation_level == ValidationLevel.MODERATE
        assert config.allow_anonymous == True
        assert config.min_user_id_length == 3
        assert config.max_user_id_length == 255
        assert "undefined" in config.invalid_patterns
        assert config.session_timeout_minutes == 1440
        assert config.pipeline_injection_key == "AUTHENTICATED_USER_ID"
    
    def test_config_validation(self):
        """Test configuration validation and post-init adjustments."""
        # Test invalid length settings
        config = AuthConfig(min_user_id_length=0, max_user_id_length=2)
        assert config.min_user_id_length == 1
        assert config.max_user_id_length >= config.min_user_id_length
    
    def test_custom_config(self):
        """Test custom configuration settings."""
        config = AuthConfig(
            validation_level=ValidationLevel.STRICT,
            allow_anonymous=False,
            min_user_id_length=5,
            debug_mode=True
        )
        assert config.validation_level == ValidationLevel.STRICT
        assert config.allow_anonymous == False
        assert config.min_user_id_length == 5
        assert config.debug_mode == True


class TestUserContext:
    """Test user context data structure."""
    
    def test_user_context_creation(self):
        """Test UserContext creation and properties."""
        context = UserContext(
            user_id="test@example.com",
            user_type=UserIDType.EMAIL,
            user_data={"name": "Test User"},
            validation_score=0.9
        )
        
        assert context.user_id == "test@example.com"
        assert context.user_type == UserIDType.EMAIL
        assert context.user_data["name"] == "Test User"
        assert context.validation_score == 0.9
        assert context.is_authenticated == True
        assert context.display_name == "Test User"
    
    def test_anonymous_user_context(self):
        """Test anonymous user context properties."""
        context = UserContext(
            user_id="anonymous",
            user_type=UserIDType.ANONYMOUS,
            validation_score=0.1
        )
        
        assert context.is_authenticated == False
        assert context.display_name == "anonymous"
    
    def test_display_name_fallback(self):
        """Test display name fallback logic."""
        context = UserContext(
            user_id="user123",
            user_type=UserIDType.USERNAME,
            user_data={}
        )
        assert context.display_name == "user123"  # Falls back to user_id


class TestUserIDValidation:
    """Test user ID validation patterns."""
    
    def setup_method(self):
        """Set up test validator."""
        self.validator = AuthValidator()
    
    def test_uuid_validation(self):
        """Test UUID format validation."""
        valid_uuids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
        ]
        
        for uuid_str in valid_uuids:
            assert self.validator.is_valid_user_id(uuid_str), f"UUID should be valid: {uuid_str}"
            assert self.validator._is_uuid_format(uuid_str), f"Should be recognized as UUID: {uuid_str}"
    
    def test_email_validation(self):
        """Test email format validation."""
        valid_emails = [
            "user@example.com",
            "test.user+tag@domain.co.uk",
            "admin@sub.domain.org",
            "user_123@test-domain.com"
        ]
        
        invalid_emails = [
            "invalid.email",
            "@domain.com",
            "user@",
            "user@domain",
            "user name@domain.com"
        ]
        
        for email in valid_emails:
            assert self.validator.is_valid_user_id(email), f"Email should be valid: {email}"
            assert self.validator._is_email_format(email), f"Should be recognized as email: {email}"
        
        for email in invalid_emails:
            assert not self.validator._is_email_format(email), f"Should be invalid email: {email}"
    
    def test_username_validation(self):
        """Test username format validation."""
        valid_usernames = [
            "user123",
            "test_user",
            "admin-user",
            "user.name",
            "a1b2c3"
        ]
        
        invalid_usernames = [
            "ab",  # Too short
            "_user",  # Starts with underscore
            "user_",  # Ends with underscore
            "-user",  # Starts with hyphen
            "user-",  # Ends with hyphen
            "user name",  # Contains space
            "user@name"  # Contains @
        ]
        
        for username in valid_usernames:
            assert self.validator.is_valid_user_id(username), f"Username should be valid: {username}"
            assert self.validator._is_username_format(username), f"Should be recognized as username: {username}"
        
        for username in invalid_usernames:
            assert not self.validator._is_username_format(username), f"Should be invalid username: {username}"
    
    def test_invalid_patterns(self):
        """Test rejection of invalid patterns."""
        invalid_ids = [
            "undefined",
            "null", 
            "none",
            "",
            "anonymous",
            "guest",
            "test"
        ]
        
        for invalid_id in invalid_ids:
            assert not self.validator.is_valid_user_id(invalid_id), f"Should reject invalid pattern: {invalid_id}"
    
    def test_length_constraints(self):
        """Test user ID length constraints."""
        # Too short
        assert not self.validator.is_valid_user_id("ab")
        
        # Too long (over 255 chars)
        long_id = "a" * 256
        assert not self.validator.is_valid_user_id(long_id)
        
        # Just right
        good_id = "abc"
        assert self.validator.is_valid_user_id(good_id)
    
    def test_validation_levels(self):
        """Test different validation strictness levels."""
        test_ids = {
            "550e8400-e29b-41d4-a716-446655440000": {  # UUID
                ValidationLevel.STRICT: True,
                ValidationLevel.MODERATE: True,
                ValidationLevel.PERMISSIVE: True
            },
            "user@example.com": {  # Email
                ValidationLevel.STRICT: True,
                ValidationLevel.MODERATE: True,
                ValidationLevel.PERMISSIVE: True
            },
            "username123": {  # Username
                ValidationLevel.STRICT: False,
                ValidationLevel.MODERATE: True,
                ValidationLevel.PERMISSIVE: True
            },
            "Some Name": {  # Display name
                ValidationLevel.STRICT: False,
                ValidationLevel.MODERATE: False,
                ValidationLevel.PERMISSIVE: True
            }
        }
        
        for user_id, expectations in test_ids.items():
            for level, expected in expectations.items():
                config = AuthConfig(validation_level=level)
                validator = AuthValidator(config)
                result = validator.is_valid_user_id(user_id)
                assert result == expected, f"Level {level.value}: {user_id} should be {expected}, got {result}"


class TestUserIDType:
    """Test user ID type determination."""
    
    def setup_method(self):
        """Set up test validator."""
        self.validator = AuthValidator()
    
    def test_user_type_determination(self):
        """Test correct user type identification."""
        test_cases = [
            ("550e8400-e29b-41d4-a716-446655440000", UserIDType.UUID),
            ("user@example.com", UserIDType.EMAIL),
            ("username123", UserIDType.USERNAME),
            ("Some Display Name", UserIDType.NAME),
            ("anonymous", UserIDType.ANONYMOUS)
        ]
        
        for user_id, expected_type in test_cases:
            determined_type = self.validator._determine_user_type(user_id)
            assert determined_type == expected_type, f"User ID '{user_id}' should be type {expected_type.value}, got {determined_type.value}"


class TestPipelineExtraction:
    """Test pipeline user ID extraction."""
    
    def setup_method(self):
        """Set up test validator."""
        self.validator = AuthValidator()
    
    def test_pipeline_injection_extraction(self):
        """Test extraction of pipeline-injected user IDs."""
        messages = [
            {"role": "system", "content": "AUTHENTICATED_USER_ID: user@example.com\nOther system info"},
            {"role": "user", "content": "Hello"}
        ]
        
        user_id, metadata = self.validator.extract_pipeline_user_id(messages)
        assert user_id == "user@example.com"
        assert metadata["source"] == "pipeline_injection"
        assert "system_message" in metadata["extracted_from"]
    
    def test_multiple_pipeline_injections(self):
        """Test that first pipeline injection is used."""
        messages = [
            {"role": "system", "content": "AUTHENTICATED_USER_ID: first@example.com"},
            {"role": "system", "content": "AUTHENTICATED_USER_ID: second@example.com"},
            {"role": "user", "content": "Hello"}
        ]
        
        user_id, metadata = self.validator.extract_pipeline_user_id(messages)
        assert user_id == "first@example.com"
    
    def test_no_pipeline_injection(self):
        """Test when no pipeline injection exists."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        user_id, metadata = self.validator.extract_pipeline_user_id(messages)
        assert user_id is None
        assert metadata == {}
    
    def test_invalid_pipeline_injection(self):
        """Test handling of invalid pipeline injection."""
        messages = [
            {"role": "system", "content": "AUTHENTICATED_USER_ID: invalid_id"},
            {"role": "user", "content": "Hello"}
        ]
        
        # Set strict validation to reject the invalid ID
        config = AuthConfig(validation_level=ValidationLevel.STRICT)
        validator = AuthValidator(config)
        
        user_id, metadata = validator.extract_pipeline_user_id(messages)
        assert user_id is None  # Should reject invalid format


class TestUserObjectExtraction:
    """Test user object extraction."""
    
    def setup_method(self):
        """Set up test validator."""
        self.validator = AuthValidator()
    
    def test_user_object_priority_order(self):
        """Test that email has priority over other fields."""
        user_obj = {
            "id": "user123",
            "email": "user@example.com",
            "username": "username",
            "name": "User Name"
        }
        
        user_id, user_data = self.validator.extract_user_from_object(user_obj)
        assert user_id == "user@example.com"  # Email should have priority
        assert user_data == user_obj
    
    def test_user_object_fallback_chain(self):
        """Test fallback chain when higher priority fields are missing."""
        # Test id fallback
        user_obj = {"id": "550e8400-e29b-41d4-a716-446655440000", "username": "username"}
        user_id, user_data = self.validator.extract_user_from_object(user_obj)
        assert user_id == "550e8400-e29b-41d4-a716-446655440000"
        
        # Test username fallback
        user_obj = {"username": "username123", "name": "User Name"}
        user_id, user_data = self.validator.extract_user_from_object(user_obj)
        assert user_id == "username123"
        
        # Test name fallback (in permissive mode)
        config = AuthConfig(validation_level=ValidationLevel.PERMISSIVE)
        validator = AuthValidator(config)
        user_obj = {"name": "User Name"}
        user_id, user_data = validator.extract_user_from_object(user_obj)
        assert user_id == "User Name"
    
    def test_empty_user_object(self):
        """Test handling of empty or invalid user objects."""
        # Empty object
        user_id, user_data = self.validator.extract_user_from_object({})
        assert user_id is None
        assert user_data == {}
        
        # Non-dict object
        user_id, user_data = self.validator.extract_user_from_object("not_a_dict")
        assert user_id is None
        assert user_data == {}
        
        # Object with empty values
        user_obj = {"id": "", "email": None, "username": "   ", "name": ""}
        user_id, user_data = self.validator.extract_user_from_object(user_obj)
        assert user_id is None


class TestRequestUserExtraction:
    """Test full request user extraction with priority system."""
    
    def setup_method(self):
        """Set up test validator."""
        self.validator = AuthValidator()
    
    def test_pipeline_injection_highest_priority(self):
        """Test that pipeline injection has highest priority."""
        request_data = {
            "messages": [
                {"role": "system", "content": "AUTHENTICATED_USER_ID: pipeline@example.com"}
            ],
            "__user__": {
                "email": "user@example.com",
                "id": "user123"
            },
            "user_id": "direct_user"
        }
        
        context = self.validator.extract_and_validate_user(request_data)
        assert context.user_id == "pipeline@example.com"
        assert context.user_type == UserIDType.PIPELINE_INJECTION
        assert context.validation_score == 1.0
    
    def test_user_object_priority(self):
        """Test user object extraction when no pipeline injection."""
        request_data = {
            "__user__": {
                "email": "user@example.com",
                "id": "user123"
            },
            "user_id": "direct_user"
        }
        
        context = self.validator.extract_and_validate_user(request_data)
        assert context.user_id == "user@example.com"  # Email has priority
        assert context.user_type == UserIDType.EMAIL
        assert context.validation_score == 0.9
    
    def test_direct_user_id_fallback(self):
        """Test direct user_id field fallback."""
        request_data = {
            "user_id": "550e8400-e29b-41d4-a716-446655440000"
        }
        
        context = self.validator.extract_and_validate_user(request_data)
        assert context.user_id == "550e8400-e29b-41d4-a716-446655440000"
        assert context.user_type == UserIDType.UUID
        assert context.validation_score == 0.8
    
    def test_message_metadata_fallback(self):
        """Test message metadata fallback."""
        request_data = {
            "messages": [
                {"role": "user", "content": "Hello", "user_id": "msg_user@example.com"}
            ]
        }
        
        context = self.validator.extract_and_validate_user(request_data)
        assert context.user_id == "msg_user@example.com"
        assert context.user_type == UserIDType.EMAIL
        assert context.validation_score == 0.7
    
    def test_anonymous_fallback(self):
        """Test anonymous fallback when no user found."""
        request_data = {
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        context = self.validator.extract_and_validate_user(request_data)
        assert context.user_id == "anonymous"
        assert context.user_type == UserIDType.ANONYMOUS
        assert context.validation_score == 0.1
        assert not context.is_authenticated
    
    def test_no_anonymous_allowed(self):
        """Test error when anonymous not allowed."""
        config = AuthConfig(allow_anonymous=False)
        validator = AuthValidator(config)
        
        request_data = {
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        # With error handling, this should return the default anonymous context
        # rather than raising an exception
        context = validator.extract_and_validate_user(request_data)
        
        # The error handler should have logged the failure and returned default
        assert context.user_id == "anonymous"
        assert context.user_type == UserIDType.ANONYMOUS


class TestSessionManagement:
    """Test session management functionality."""
    
    def setup_method(self):
        """Set up test validator."""
        self.validator = AuthValidator()
    
    def test_session_creation(self):
        """Test session creation and retrieval."""
        user_context = UserContext("user@example.com", UserIDType.EMAIL)
        
        session_id = self.validator.create_session(user_context)
        assert session_id is not None
        assert user_context.session_id == session_id
        
        retrieved_context = self.validator.get_session(session_id)
        assert retrieved_context is not None
        assert retrieved_context.user_id == "user@example.com"
    
    def test_session_expiration(self):
        """Test session expiration handling."""
        config = AuthConfig(session_timeout_minutes=1)  # 1 minute timeout
        validator = AuthValidator(config)
        
        user_context = UserContext("user@example.com", UserIDType.EMAIL)
        # Simulate old session
        user_context.extracted_at = datetime.now() - timedelta(minutes=2)
        
        session_id = str(uuid.uuid4())
        validator._active_sessions[session_id] = user_context
        
        # Should return None for expired session
        retrieved_context = validator.get_session(session_id)
        assert retrieved_context is None
        assert session_id not in validator._active_sessions
    
    def test_session_cleanup(self):
        """Test cleanup of expired sessions."""
        config = AuthConfig(session_timeout_minutes=1)
        validator = AuthValidator(config)
        
        # Create expired session
        old_context = UserContext("old@example.com", UserIDType.EMAIL)
        old_context.extracted_at = datetime.now() - timedelta(minutes=2)
        old_session = str(uuid.uuid4())
        validator._active_sessions[old_session] = old_context
        
        # Create valid session
        new_context = UserContext("new@example.com", UserIDType.EMAIL)
        new_session = validator.create_session(new_context)
        
        # Cleanup should remove only expired session
        cleaned = validator.cleanup_expired_sessions()
        assert cleaned == 1
        assert old_session not in validator._active_sessions
        assert new_session in validator._active_sessions


class TestSessionConsistency:
    """Test session consistency validation."""
    
    def setup_method(self):
        """Set up test validator."""
        self.validator = AuthValidator()
    
    def test_consistent_session(self):
        """Test validation of consistent session."""
        user_context = UserContext("user@example.com", UserIDType.EMAIL)
        request_data = {
            "__user__": {"email": "user@example.com", "name": "User"},
            "user_id": "user@example.com"
        }
        
        is_consistent = self.validator.validate_session_consistency(user_context, request_data)
        assert is_consistent == True
    
    def test_inconsistent_session(self):
        """Test detection of inconsistent session."""
        user_context = UserContext("user1@example.com", UserIDType.EMAIL)
        request_data = {
            "__user__": {"email": "user2@example.com"},
            "user_id": "user3@example.com"
        }
        
        is_consistent = self.validator.validate_session_consistency(user_context, request_data)
        assert is_consistent == False
    
    def test_session_consistency_disabled(self):
        """Test when session consistency checking is disabled."""
        config = AuthConfig(require_session_consistency=False)
        validator = AuthValidator(config)
        
        user_context = UserContext("user1@example.com", UserIDType.EMAIL)
        request_data = {
            "__user__": {"email": "user2@example.com"},
            "user_id": "user3@example.com"
        }
        
        is_consistent = validator.validate_session_consistency(user_context, request_data)
        assert is_consistent == True  # Should always return True when disabled


class TestBackwardCompatibility:
    """Test backward compatibility functions."""
    
    def test_validate_openwebui_user_id_compatibility(self):
        """Test backward compatible validation function."""
        # Test valid IDs
        assert validate_openwebui_user_id("user@example.com") == True
        assert validate_openwebui_user_id("550e8400-e29b-41d4-a716-446655440000") == True
        assert validate_openwebui_user_id("username123") == True
        
        # Test invalid IDs
        assert validate_openwebui_user_id("") == False
        assert validate_openwebui_user_id("null") == False
        assert validate_openwebui_user_id("ab") == False
    
    def test_extract_authenticated_user_id_compatibility(self):
        """Test backward compatible extraction function."""
        messages = [
            {"role": "system", "content": "AUTHENTICATED_USER_ID: user@example.com"},
            {"role": "user", "content": "Hello"}
        ]
        
        user_id = extract_authenticated_user_id(messages)
        assert user_id == "user@example.com"
        
        # Test with no pipeline injection
        messages = [{"role": "user", "content": "Hello"}]
        user_id = extract_authenticated_user_id(messages)
        assert user_id is None
    
    def test_extract_user_from_request_compatibility(self):
        """Test full request extraction compatibility function."""
        request_data = {
            "__user__": {"email": "user@example.com"},
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        context = extract_user_from_request(request_data)
        assert context.user_id == "user@example.com"
        assert context.user_type == UserIDType.EMAIL
        assert context.is_authenticated == True


class TestGlobalValidator:
    """Test global validator instance management."""
    
    def test_get_auth_validator_singleton(self):
        """Test that get_auth_validator returns singleton."""
        validator1 = get_auth_validator()
        validator2 = get_auth_validator()
        assert validator1 is validator2
    
    def test_configure_auth_validator(self):
        """Test configuring global validator."""
        config = AuthConfig(validation_level=ValidationLevel.STRICT)
        validator = configure_auth_validator(config)
        assert validator.config.validation_level == ValidationLevel.STRICT
        
        # Should be same instance returned by get_auth_validator
        global_validator = get_auth_validator()
        assert global_validator is validator


class TestValidationSummary:
    """Test validation summary and statistics."""
    
    def test_validation_summary(self):
        """Test validation summary generation."""
        validator = AuthValidator()
        
        # Create some sessions
        context1 = UserContext("user1@example.com", UserIDType.EMAIL)
        context2 = UserContext("user2@example.com", UserIDType.EMAIL)
        validator.create_session(context1)
        validator.create_session(context2)
        
        summary = validator.get_validation_summary()
        assert "config" in summary
        assert "active_sessions" in summary
        assert "validation_patterns" in summary
        assert summary["active_sessions"] == 2
        assert summary["config"]["validation_level"] == "moderate"


def run_all_tests():
    """Run all auth validator tests."""
    print("🧪 Running AuthValidator Test Suite")
    print("=" * 50)
    
    # Run tests using pytest programmatically
    import subprocess
    import sys
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"\n🎯 Test Result: {'✅ PASSED' if result.returncode == 0 else '❌ FAILED'}")
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False


if __name__ == "__main__":
    run_all_tests()
