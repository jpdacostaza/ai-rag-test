"""
User profiles management placeholder.
"""
from typing import Dict, Any, Optional
import re


class UserProfileManager:
    """Simple user profile manager."""
    
    def __init__(self):
        self.profiles = {}
    
    def get_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile."""
        return self.profiles.get(user_id, {"user_id": user_id, "preferences": {}})
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user info for memory context."""
        profile = self.get_profile(user_id)
        if profile and len(profile) > 2:  # More than just user_id and empty preferences
            return profile
        return None
    
    def build_context_for_llm(self, user_id: str) -> Optional[str]:
        """Build context string for LLM."""
        profile = self.get_user_info(user_id)
        if not profile:
            return None
        
        context_parts = []
        for key, value in profile.items():
            if key != "user_id" and value:
                context_parts.append(f"{key}: {value}")
        
        return "; ".join(context_parts) if context_parts else None
    
    def extract_user_info(self, message: str) -> Dict[str, Any]:
        """Extract user information from a message."""
        user_info = {}
        message_lower = message.lower()
        
        # Name extraction patterns
        name_patterns = [
            r"my name is (\w+)",
            r"i am (\w+)",
            r"i'm (\w+)",
            r"call me (\w+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match:
                user_info["name"] = match.group(1).title()
                break
        
        # Location extraction
        location_patterns = [
            r"i live in ([^,.!?]+)",
            r"i'm from ([^,.!?]+)",
            r"from ([^,.!?]+)"
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, message_lower)
            if match:
                user_info["location"] = match.group(1).strip().title()
                break
        
        # Age extraction
        age_match = re.search(r"(\d+) years old", message_lower)
        if age_match:
            user_info["age"] = age_match.group(1)
        
        return user_info
    
    def update_profile(self, user_id: str, profile_data: Dict[str, Any]):
        """Update user profile."""
        if user_id not in self.profiles:
            self.profiles[user_id] = {"user_id": user_id, "preferences": {}}
        self.profiles[user_id].update(profile_data)


# Global instance
user_profile_manager = UserProfileManager()
