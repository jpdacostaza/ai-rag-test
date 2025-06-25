"""
User Profile Management System for Persistent Memory
"""

from typing import Dict, Any, Optional
import json
import os
from datetime import datetime
from pathlib import Path
import re

class UserProfileManager:
    def __init__(self, profiles_dir: str = "user_profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)
        
    def save_user_info(self, user_id: str, info: Dict[str, Any]) -> bool:
        """Save user information to persistent storage"""
        try:
            profile_path = self.profiles_dir / f"{user_id}.json"
            
            # Load existing profile if it exists
            existing_data = {}
            if profile_path.exists():
                with open(profile_path, 'r') as f:
                    existing_data = json.load(f)
            
            # Update with new info
            existing_data.update(info)
            existing_data['last_updated'] = datetime.now().isoformat()
            
            # Save back
            with open(profile_path, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving user profile: {e}")
            return False
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user information from persistent storage"""
        try:
            profile_path = self.profiles_dir / f"{user_id}.json"
            
            if profile_path.exists():
                with open(profile_path, 'r') as f:
                    return json.load(f)
            
            return None
        except Exception as e:
            print(f"Error loading user profile: {e}")
            return None
    
    def update_conversation_context(self, user_id: str, key: str, value: Any):
        """Update specific conversation context"""
        info = self.get_user_info(user_id) or {}
        
        if 'conversation_context' not in info:
            info['conversation_context'] = {}
            
        info['conversation_context'][key] = value
        self.save_user_info(user_id, info)
    
    def extract_user_info(self, message: str) -> Dict[str, Any]:
        """Extract user information from message"""
        info = {}
        
        # Name extraction patterns
        name_patterns = [
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"i am (\w+)",
            r"call me (\w+)",
            r"this is (\w+)",
            r"name's (\w+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message.lower())
            if match:
                info['name'] = match.group(1).capitalize()
                break
        
        # Location extraction
        location_patterns = [
            r"i live in ([^.!?]+)",
            r"i'm from ([^.!?]+)",
            r"i am from ([^.!?]+)",
            r"located in ([^.!?]+)"
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, message.lower())
            if match:
                info['location'] = match.group(1).strip()
                break
        
        # Job/profession extraction
        job_patterns = [
            r"i work as (?:a |an )?([^.!?]+)",
            r"i'm (?:a |an )?([^.!?]+)",
            r"my job is ([^.!?]+)",
            r"i am (?:a |an )?([^.!?]+)"
        ]
        
        for pattern in job_patterns:
            match = re.search(pattern, message.lower())
            if match:
                job = match.group(1).strip()
                # Filter out common words that aren't jobs
                if job not in ['here', 'fine', 'good', 'okay', 'well']:
                    info['profession'] = job
                    break
        
        # Age extraction
        age_patterns = [
            r"i am (\d+) years old",
            r"i'm (\d+) years old",
            r"my age is (\d+)",
            r"(\d+) years old"
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, message.lower())
            if match:
                info['age'] = int(match.group(1))
                break
        
        # Interests extraction
        interest_patterns = [
            r"i like ([^.!?]+)",
            r"i love ([^.!?]+)",
            r"i enjoy ([^.!?]+)",
            r"my hobby is ([^.!?]+)",
            r"i'm interested in ([^.!?]+)"
        ]
        
        interests = []
        for pattern in interest_patterns:
            matches = re.findall(pattern, message.lower())
            interests.extend([match.strip() for match in matches])
        
        if interests:
            info['interests'] = interests
        
        return info
    
    def get_user_greeting(self, user_id: str) -> str:
        """Generate a personalized greeting based on user profile"""
        profile = self.get_user_info(user_id)
        
        if not profile:
            return "Hello! I'm here to help you."
        
        name = profile.get('name', 'friend')
        greeting = f"Hello {name}!"
        
        # Add context if available
        if 'last_updated' in profile:
            last_seen = datetime.fromisoformat(profile['last_updated'])
            days_ago = (datetime.now() - last_seen).days
            
            if days_ago == 0:
                greeting += " Good to see you again today."
            elif days_ago == 1:
                greeting += " Welcome back! I remember our conversation from yesterday."
            elif days_ago < 7:
                greeting += f" Welcome back! It's been {days_ago} days since we last talked."
            else:
                greeting += " It's been a while! I still remember our previous conversations."
        
        return greeting
    
    def build_context_for_llm(self, user_id: str) -> str:
        """Build context string for LLM based on user profile"""
        profile = self.get_user_info(user_id)
        
        if not profile:
            return ""
        
        context_parts = []
        
        if 'name' in profile:
            context_parts.append(f"The user's name is {profile['name']}.")
        
        if 'location' in profile:
            context_parts.append(f"They live in {profile['location']}.")
        
        if 'profession' in profile:
            context_parts.append(f"They work as {profile['profession']}.")
        
        if 'age' in profile:
            context_parts.append(f"They are {profile['age']} years old.")
        
        if 'interests' in profile:
            interests = ", ".join(profile['interests'])
            context_parts.append(f"Their interests include: {interests}.")
        
        if 'conversation_context' in profile:
            ctx = profile['conversation_context']
            for key, value in ctx.items():
                context_parts.append(f"Previous context - {key}: {value}")
        
        return " ".join(context_parts)

# Global instance
user_profile_manager = UserProfileManager()
