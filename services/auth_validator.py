"""
Unified Authentication and Validation Service
============================================

Consolidates all scattered user ID validation, authentication patterns, and session management
into a single, consistent service. Eliminates duplication across 8+ locations in the memory system.

Key Features:
- Priority-based user ID extraction (pipeline > email > id > username > name > anonymous)  
- Consistent validation patterns across all components
- Session management and consistency validation
- Security patterns for authentication handling
- Configurable validation rules and formats
- Integration with completed error handling patterns

Usage:
    from services.auth_validator import AuthValidator, get_auth_validator
    
    validator = get_auth_validator()
    user_id, user_data = validator.extract_and_validate_user(request_data)
    if validator.is_valid_user_id(user_id):
        # Proceed with authenticated operations
"""

import re
import uuid
import logging
from typing import Dict, Any, Optional, Tuple, List, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

# Import completed error handling patterns
from utilities.error_patterns import (
    handle_service_errors,
    ServiceType,
    ErrorHandlerConfig,
    ErrorAction
)

# Configure logging
logger = logging.getLogger(__name__)


class UserIDType(Enum):
    """Types of user identifiers in order of priority."""
    PIPELINE_INJECTION = "pipeline_injection"  # Highest priority - injected by pipelines
    EMAIL = "email"                             # Email addresses
    UUID = "uuid"                              # UUID format user IDs
    USERNAME = "username"                      # Alphanumeric usernames
    NAME = "name"                              # Display names
    ANONYMOUS = "anonymous"                    # Fallback anonymous users


class ValidationLevel(Enum):
    """Validation strictness levels."""
    STRICT = "strict"       # Only UUID and email formats allowed
    MODERATE = "moderate"   # UUID, email, and valid usernames allowed
    PERMISSIVE = "permissive"  # Any non-empty string allowed


@dataclass
class AuthConfig:
    """Configuration for authentication validation."""
    validation_level: ValidationLevel = ValidationLevel.MODERATE
    allow_anonymous: bool = True
    min_user_id_length: int = 3
    max_user_id_length: int = 255
    invalid_patterns: Set[str] = field(default_factory=lambda: {
        "undefined", "null", "none", "", "anonymous", "guest", "test"
    })
    session_timeout_minutes: int = 1440  # 24 hours
    require_session_consistency: bool = True
    pipeline_injection_key: str = "AUTHENTICATED_USER_ID"
    debug_mode: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.min_user_id_length < 1:
            self.min_user_id_length = 1
        if self.max_user_id_length < self.min_user_id_length:
            self.max_user_id_length = self.min_user_id_length + 100


@dataclass
class UserContext:
    """User context information extracted from requests."""
    user_id: str
    user_type: UserIDType
    user_data: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    extracted_at: datetime = field(default_factory=datetime.now)
    validation_score: float = 1.0  # 0.0 = invalid, 1.0 = fully valid
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is properly authenticated."""
        return (
            self.user_type != UserIDType.ANONYMOUS and
            self.validation_score >= 0.7 and
            self.user_id not in {"anonymous", "guest", "unknown"}
        )
    
    @property
    def display_name(self) -> str:
        """Get user display name."""
        return (
            self.user_data.get("name") or
            self.user_data.get("display_name") or
            self.user_data.get("username") or
            self.user_id
        )


class AuthValidator:
    """
    Unified authentication and validation service.
    
    Consolidates all scattered user validation logic into a single, consistent interface.
    Integrates with the completed error handling patterns for robust error management.
    """
    
    def __init__(self, config: Optional[AuthConfig] = None):
        """Initialize the auth validator with configuration."""
        self.config = config or AuthConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Compile regex patterns for performance
        self._uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        self._email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        self._username_pattern = re.compile(
            r'^[a-zA-Z0-9][a-zA-Z0-9._-]{1,}[a-zA-Z0-9]$'
        )
        
        # Session tracking
        self._active_sessions: Dict[str, UserContext] = {}
        
        if self.config.debug_mode:
            self.logger.info("AuthValidator initialized with debug mode enabled")
    
    def _log_debug(self, message: str) -> None:
        """Log debug message if debug mode is enabled."""
        if self.config.debug_mode:
            self.logger.debug(f"[AUTH_VALIDATOR] {message}")
    
    @handle_service_errors(
        config=ErrorHandlerConfig(
            service_type=ServiceType.VALIDATION,
            action=ErrorAction.RETURN_DEFAULT,
            default_value=False
        ),
        service_name="AuthValidator",
        operation_name="user_id_validation"
    )
    def is_valid_user_id(self, user_id: str) -> bool:
        """
        Validate user ID format and content.
        
        Args:
            user_id: The user identifier to validate
            
        Returns:
            bool: True if user ID is valid according to current config
        """
        if not user_id or not isinstance(user_id, str):
            return False
        
        # Check length constraints
        if not (self.config.min_user_id_length <= len(user_id) <= self.config.max_user_id_length):
            self._log_debug(f"User ID length invalid: {len(user_id)} chars")
            return False
        
        # Check for invalid patterns
        if user_id.lower() in self.config.invalid_patterns:
            self._log_debug(f"User ID matches invalid pattern: {user_id}")
            return False
        
        # Validation based on strictness level
        if self.config.validation_level == ValidationLevel.STRICT:
            # Only UUID and email formats
            return self._is_uuid_format(user_id) or self._is_email_format(user_id)
        
        elif self.config.validation_level == ValidationLevel.MODERATE:
            # UUID, email, and valid usernames
            return (
                self._is_uuid_format(user_id) or
                self._is_email_format(user_id) or
                self._is_username_format(user_id)
            )
        
        elif self.config.validation_level == ValidationLevel.PERMISSIVE:
            # Any non-empty string that doesn't match invalid patterns
            return bool(user_id.strip())
        
        return False
    
    def _is_uuid_format(self, user_id: str) -> bool:
        """Check if user ID is a valid UUID format."""
        return bool(self._uuid_pattern.match(user_id))
    
    def _is_email_format(self, user_id: str) -> bool:
        """Check if user ID is a valid email format."""
        return bool(self._email_pattern.match(user_id))
    
    def _is_username_format(self, user_id: str) -> bool:
        """Check if user ID is a valid username format."""
        return bool(self._username_pattern.match(user_id)) and len(user_id) >= 3
    
    def _determine_user_type(self, user_id: str) -> UserIDType:
        """Determine the type of user identifier."""
        if user_id == "anonymous":
            return UserIDType.ANONYMOUS
        elif self._is_uuid_format(user_id):
            return UserIDType.UUID
        elif self._is_email_format(user_id):
            return UserIDType.EMAIL
        elif self._is_username_format(user_id):
            return UserIDType.USERNAME
        else:
            return UserIDType.NAME
    
    @handle_service_errors(
        config=ErrorHandlerConfig(
            service_type=ServiceType.VALIDATION,
            action=ErrorAction.RETURN_DEFAULT,
            default_value=(None, {})
        ),
        service_name="AuthValidator",
        operation_name="pipeline_user_extraction"
    )
    def extract_pipeline_user_id(self, messages: List[Dict[str, Any]]) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Extract user ID from pipeline injection in messages.
        
        This is the highest priority extraction method, used by Enhanced Memory Pipeline.
        
        Args:
            messages: List of messages to search for pipeline injection
            
        Returns:
            Tuple of (user_id, metadata) or (None, {}) if not found
        """
        if not messages:
            return None, {}
        
        for msg in messages:
            if not isinstance(msg, dict):
                continue
                
            if msg.get("role") != "system":
                continue
                
            content = msg.get("content", "")
            if not isinstance(content, str):
                continue
            
            # Look for pipeline injection pattern
            if self.config.pipeline_injection_key in content:
                # Extract user ID from content
                for line in content.split('\n'):
                    if self.config.pipeline_injection_key in line:
                        try:
                            user_id = line.split(f"{self.config.pipeline_injection_key}:")[1].strip()
                            if user_id and self.is_valid_user_id(user_id):
                                self._log_debug(f"✅ Found pipeline-injected user ID: {user_id}")
                                metadata = {
                                    "source": "pipeline_injection",
                                    "extracted_from": "system_message",
                                    "message_content": content[:100] + "..." if len(content) > 100 else content
                                }
                                return user_id, metadata
                        except (IndexError, AttributeError) as e:
                            self._log_debug(f"Failed to parse pipeline injection: {e}")
                            continue
        
        return None, {}
    
    @handle_service_errors(
        config=ErrorHandlerConfig(
            service_type=ServiceType.VALIDATION,
            action=ErrorAction.RETURN_DEFAULT,
            default_value=(None, {})
        ),
        service_name="AuthValidator",
        operation_name="user_object_extraction"
    )
    def extract_user_from_object(self, user_obj: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Extract user ID from user object with priority order.
        
        Priority: email > id > username > name
        
        Args:
            user_obj: User object containing user information
            
        Returns:
            Tuple of (user_id, user_data) or (None, {}) if no valid ID found
        """
        if not isinstance(user_obj, dict):
            return None, {}
        
        # Priority order for user ID extraction
        priority_fields = ["email", "id", "username", "name"]
        
        for field in priority_fields:
            value = user_obj.get(field)
            if value and isinstance(value, str) and value.strip():
                candidate_id = value.strip()
                if self.is_valid_user_id(candidate_id):
                    self._log_debug(f"✅ Extracted user ID from {field}: {candidate_id}")
                    return candidate_id, user_obj
        
        self._log_debug("❌ No valid user ID found in user object")
        return None, user_obj
    
    @handle_service_errors(
        config=ErrorHandlerConfig(
            service_type=ServiceType.VALIDATION,
            action=ErrorAction.RETURN_DEFAULT,
            default_value=UserContext("anonymous", UserIDType.ANONYMOUS)
        ),
        service_name="AuthValidator",
        operation_name="request_user_extraction"
    )
    def extract_and_validate_user(self, request_data: Dict[str, Any]) -> UserContext:
        """
        Extract and validate user from request data using priority system.
        
        Priority Order:
        1. Pipeline injection (AUTHENTICATED_USER_ID in system messages)
        2. __user__ object (email > id > username > name)
        3. Direct user_id field
        4. Messages metadata
        5. Anonymous fallback
        
        Args:
            request_data: Request data containing user information
            
        Returns:
            UserContext: Validated user context with metadata
        """
        self._log_debug("Starting user extraction from request data")
        
        # Priority 1: Pipeline injection (highest priority)
        messages = request_data.get("messages", [])
        if messages:
            user_id, metadata = self.extract_pipeline_user_id(messages)
            if user_id:
                user_type = UserIDType.PIPELINE_INJECTION
                validation_score = 1.0  # Highest confidence
                self._log_debug(f"✅ Pipeline injection user: {user_id}")
                return UserContext(
                    user_id=user_id,
                    user_type=user_type,
                    user_data=metadata,
                    validation_score=validation_score
                )
        
        # Priority 2: __user__ object
        user_obj = request_data.get("__user__")
        if user_obj:
            user_id, user_data = self.extract_user_from_object(user_obj)
            if user_id:
                user_type = self._determine_user_type(user_id)
                validation_score = 0.9  # High confidence
                self._log_debug(f"✅ User object extraction: {user_id} (type: {user_type.value})")
                return UserContext(
                    user_id=user_id,
                    user_type=user_type,
                    user_data=user_data,
                    validation_score=validation_score
                )
        
        # Priority 3: Direct user_id field
        direct_user_id = request_data.get("user_id")
        if direct_user_id and self.is_valid_user_id(direct_user_id):
            user_type = self._determine_user_type(direct_user_id)
            validation_score = 0.8  # Good confidence
            self._log_debug(f"✅ Direct user_id field: {direct_user_id}")
            return UserContext(
                user_id=direct_user_id,
                user_type=user_type,
                user_data={"source": "direct_field"},
                validation_score=validation_score
            )
        
        # Priority 4: Messages metadata
        for msg in messages:
            if isinstance(msg, dict) and "user_id" in msg:
                candidate_id = msg["user_id"]
                if self.is_valid_user_id(candidate_id):
                    user_type = self._determine_user_type(candidate_id)
                    validation_score = 0.7  # Moderate confidence
                    self._log_debug(f"✅ Message metadata user: {candidate_id}")
                    return UserContext(
                        user_id=candidate_id,
                        user_type=user_type,
                        user_data={"source": "message_metadata"},
                        validation_score=validation_score
                    )
        
        # Priority 5: Anonymous fallback
        if self.config.allow_anonymous:
            self._log_debug("⚠️ Falling back to anonymous user")
            return UserContext(
                user_id="anonymous",
                user_type=UserIDType.ANONYMOUS,
                user_data={"source": "anonymous_fallback"},
                validation_score=0.1  # Low confidence
            )
        
        # No valid user found and anonymous not allowed
        raise ValueError("No valid user authentication found and anonymous access is disabled")
    
    @handle_service_errors(
        config=ErrorHandlerConfig(
            service_type=ServiceType.VALIDATION,
            action=ErrorAction.RETURN_DEFAULT,
            default_value=True
        ),
        service_name="AuthValidator",
        operation_name="session_validation"
    )
    def validate_session_consistency(self, user_context: UserContext, request_data: Dict[str, Any]) -> bool:
        """
        Validate that user session is consistent across request.
        
        Args:
            user_context: Validated user context
            request_data: Original request data
            
        Returns:
            bool: True if session is consistent
        """
        if not self.config.require_session_consistency:
            return True
        
        try:
            # Collect all user IDs mentioned in the request
            found_ids = set()
            
            # Check __user__ object
            user_obj = request_data.get("__user__")
            if isinstance(user_obj, dict):
                for field in ["id", "email", "username", "name"]:
                    value = user_obj.get(field)
                    if value and isinstance(value, str) and value.strip():
                        found_ids.add(value.strip())
            
            # Check direct user_id
            direct_id = request_data.get("user_id")
            if direct_id:
                found_ids.add(direct_id)
            
            # Check messages
            messages = request_data.get("messages", [])
            for msg in messages:
                if isinstance(msg, dict) and "user_id" in msg:
                    found_ids.add(msg["user_id"])
            
            # Validate consistency
            if len(found_ids) <= 1:
                # Consistent - no conflicts
                return True
            
            # Check if all IDs refer to the same user
            if user_context.user_id in found_ids:
                # The extracted user ID is among the found IDs
                return True
            
            self._log_debug(f"❌ Session inconsistency: found {found_ids}, extracted {user_context.user_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"Session validation error: {e}")
            return True  # Fail open for robustness
    
    def create_session(self, user_context: UserContext) -> str:
        """
        Create a new session for the user.
        
        Args:
            user_context: Validated user context
            
        Returns:
            str: Session ID
        """
        session_id = str(uuid.uuid4())
        user_context.session_id = session_id
        self._active_sessions[session_id] = user_context
        
        self._log_debug(f"✅ Created session {session_id} for user {user_context.user_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[UserContext]:
        """
        Get user context for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            UserContext or None if session not found/expired
        """
        user_context = self._active_sessions.get(session_id)
        if not user_context:
            return None
        
        # Check session timeout
        session_age = datetime.now() - user_context.extracted_at
        if session_age.total_seconds() > (self.config.session_timeout_minutes * 60):
            self._log_debug(f"Session {session_id} expired for user {user_context.user_id}")
            del self._active_sessions[session_id]
            return None
        
        return user_context
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            int: Number of sessions cleaned up
        """
        now = datetime.now()
        timeout_seconds = self.config.session_timeout_minutes * 60
        expired_sessions = []
        
        for session_id, user_context in self._active_sessions.items():
            session_age = now - user_context.extracted_at
            if session_age.total_seconds() > timeout_seconds:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self._active_sessions[session_id]
        
        if expired_sessions:
            self._log_debug(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of validation statistics.
        
        Returns:
            dict: Validation summary with statistics
        """
        return {
            "config": {
                "validation_level": self.config.validation_level.value,
                "allow_anonymous": self.config.allow_anonymous,
                "require_session_consistency": self.config.require_session_consistency,
                "session_timeout_minutes": self.config.session_timeout_minutes,
            },
            "active_sessions": len(self._active_sessions),
            "validation_patterns": {
                "uuid_pattern": self._uuid_pattern.pattern,
                "email_pattern": self._email_pattern.pattern,
                "username_pattern": self._username_pattern.pattern,
            },
        }


# Global auth validator instance
_auth_validator: Optional[AuthValidator] = None


def get_auth_validator(config: Optional[AuthConfig] = None) -> AuthValidator:
    """
    Get the global AuthValidator instance.
    
    Args:
        config: Optional configuration (only used on first call)
        
    Returns:
        AuthValidator: Global validator instance
    """
    global _auth_validator
    if _auth_validator is None:
        _auth_validator = AuthValidator(config)
    return _auth_validator


def configure_auth_validator(config: AuthConfig) -> AuthValidator:
    """
    Configure the global auth validator with new settings.
    
    Args:
        config: New authentication configuration
        
    Returns:
        AuthValidator: Newly configured validator instance
    """
    global _auth_validator
    _auth_validator = AuthValidator(config)
    return _auth_validator


# Convenience functions for backward compatibility
def validate_openwebui_user_id(user_id: str) -> bool:
    """
    Validate OpenWebUI user ID using the global validator.
    
    Maintains backward compatibility with existing validation functions.
    
    Args:
        user_id: User identifier to validate
        
    Returns:
        bool: True if valid
    """
    validator = get_auth_validator()
    return validator.is_valid_user_id(user_id)


def extract_authenticated_user_id(messages: List[Dict[str, Any]]) -> Optional[str]:
    """
    Extract authenticated user ID from messages using the global validator.
    
    Maintains backward compatibility with existing extraction functions.
    
    Args:
        messages: List of messages to extract from
        
    Returns:
        Optional[str]: Extracted user ID or None
    """
    validator = get_auth_validator()
    user_id, _ = validator.extract_pipeline_user_id(messages)
    return user_id


def extract_user_from_request(request_data: Dict[str, Any]) -> UserContext:
    """
    Extract and validate user from request data using the global validator.
    
    Args:
        request_data: Request data to extract from
        
    Returns:
        UserContext: Validated user context
    """
    validator = get_auth_validator()
    return validator.extract_and_validate_user(request_data)
