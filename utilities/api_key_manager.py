"""
OpenWebUI API Key Manager
Secure storage and retrieval of API keys for project automation and user lookup.
"""

import json
import os
from typing import Optional, Dict, Any
from pathlib import Path


class APIKeyManager:
    """Manages OpenWebUI API keys with secure storage and user lookup."""
    
    def __init__(self, config_file: str = "openwebui_api_keys.json"):
        """
        Initialize the API Key Manager.
        
        Args:
            config_file: Path to the JSON config file storing API keys
        """
        self.config_file = Path(config_file)
        self.keys_data = self._load_keys()
    
    def _load_keys(self) -> Dict[str, Any]:
        """Load API keys from config file or create empty structure."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load {self.config_file}: {e}")
                return self._create_empty_config()
        else:
            return self._create_empty_config()
    
    def _create_empty_config(self) -> Dict[str, Any]:
        """Create empty configuration structure."""
        return {
            "default": {
                "api_key": "",
                "base_url": "http://localhost:3000",
                "description": "Default OpenWebUI instance"
            },
            "users": {},
            "environments": {
                "development": {
                    "api_key": "",
                    "base_url": "http://localhost:3000"
                },
                "production": {
                    "api_key": "",
                    "base_url": "https://your-openwebui-domain.com"
                }
            }
        }
    
    def save_keys(self) -> bool:
        """Save current keys to config file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.keys_data, f, indent=2)
            
            # Set file permissions to be readable only by owner (on Unix-like systems)
            if os.name != 'nt':  # Not Windows
                os.chmod(self.config_file, 0o600)
            
            return True
        except IOError as e:
            print(f"Error saving keys to {self.config_file}: {e}")
            return False
    
    def add_user_key(self, username: str, api_key: str, base_url: str = "http://localhost:3000", 
                     email: str = "", description: str = "") -> bool:
        """
        Add or update a user's API key.
        
        Args:
            username: User identifier
            api_key: OpenWebUI API key
            base_url: OpenWebUI instance URL
            email: User's email (optional)
            description: Description/notes (optional)
        
        Returns:
            True if saved successfully
        """
        self.keys_data["users"][username] = {
            "api_key": api_key,
            "base_url": base_url,
            "email": email,
            "description": description
        }
        return self.save_keys()
    
    def add_environment_key(self, env_name: str, api_key: str, base_url: str) -> bool:
        """
        Add or update an environment's API key.
        
        Args:
            env_name: Environment name (e.g., 'development', 'staging', 'production')
            api_key: OpenWebUI API key
            base_url: OpenWebUI instance URL
        
        Returns:
            True if saved successfully
        """
        self.keys_data["environments"][env_name] = {
            "api_key": api_key,
            "base_url": base_url
        }
        return self.save_keys()
    
    def set_default_key(self, api_key: str, base_url: str = "http://localhost:3000", 
                       description: str = "Default OpenWebUI instance") -> bool:
        """
        Set the default API key.
        
        Args:
            api_key: OpenWebUI API key
            base_url: OpenWebUI instance URL
            description: Description
        
        Returns:
            True if saved successfully
        """
        self.keys_data["default"] = {
            "api_key": api_key,
            "base_url": base_url,
            "description": description
        }
        return self.save_keys()
    
    def get_key_by_user(self, username: str) -> Optional[Dict[str, str]]:
        """
        Get API key and config for a specific user.
        
        Args:
            username: User identifier
        
        Returns:
            Dictionary with api_key, base_url, etc. or None if not found
        """
        return self.keys_data.get("users", {}).get(username)
    
    def get_key_by_environment(self, env_name: str) -> Optional[Dict[str, str]]:
        """
        Get API key and config for a specific environment.
        
        Args:
            env_name: Environment name
        
        Returns:
            Dictionary with api_key, base_url, etc. or None if not found
        """
        return self.keys_data.get("environments", {}).get(env_name)
    
    def get_default_key(self) -> Optional[Dict[str, str]]:
        """
        Get the default API key and config.
        
        Returns:
            Dictionary with api_key, base_url, etc. or None if not set
        """
        default = self.keys_data.get("default", {})
        if default.get("api_key"):
            return default
        return None
    
    def get_key(self, user: Optional[str] = None, environment: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Get API key with fallback logic.
        
        Priority:
        1. Environment variable OPENWEBUI_API_KEY + OPENWEBUI_BASE_URL
        2. Specific user key (if provided)
        3. Specific environment key (if provided)
        4. Default key from config
        
        Args:
            user: Username to look up
            environment: Environment name to look up
        
        Returns:
            Dictionary with api_key, base_url, etc. or None if not found
        """
        # Check environment variables first
        env_key = os.getenv("OPENWEBUI_API_KEY")
        if env_key:
            return {
                "api_key": env_key,
                "base_url": os.getenv("OPENWEBUI_BASE_URL", "http://localhost:3000"),
                "source": "environment_variable"
            }
        
        # Check user-specific key
        if user:
            user_key = self.get_key_by_user(user)
            if user_key and user_key.get("api_key"):
                user_key["source"] = f"user:{user}"
                return user_key
        
        # Check environment-specific key
        if environment:
            env_key = self.get_key_by_environment(environment)
            if env_key and env_key.get("api_key"):
                env_key["source"] = f"environment:{environment}"
                return env_key
        
        # Fall back to default
        default_key = self.get_default_key()
        if default_key:
            default_key["source"] = "default"
            return default_key
        
        return None
    
    def list_users(self) -> Dict[str, Dict[str, str]]:
        """List all configured users."""
        return self.keys_data.get("users", {})
    
    def list_environments(self) -> Dict[str, Dict[str, str]]:
        """List all configured environments."""
        return self.keys_data.get("environments", {})
    
    def remove_user(self, username: str) -> bool:
        """Remove a user's API key."""
        if username in self.keys_data.get("users", {}):
            del self.keys_data["users"][username]
            return self.save_keys()
        return False
    
    def remove_environment(self, env_name: str) -> bool:
        """Remove an environment's API key."""
        if env_name in self.keys_data.get("environments", {}):
            del self.keys_data["environments"][env_name]
            return self.save_keys()
        return False
    
    def validate_key(self, api_key: str, base_url: str) -> bool:
        """
        Validate an API key by making a test request.
        
        Args:
            api_key: API key to validate
            base_url: Base URL for the OpenWebUI instance
        
        Returns:
            True if key is valid
        """
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Test with a simple API call
            response = requests.get(f"{base_url}/api/v1/users/user", headers=headers, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Key validation failed: {e}")
            return False


def setup_api_keys_interactive():
    """Interactive setup for API keys."""
    manager = APIKeyManager()
    
    print("🔑 OpenWebUI API Key Setup")
    print("=" * 40)
    
    # Check if we have any existing keys
    if manager.get_default_key():
        print("✅ Default key already configured")
        users = manager.list_users()
        if users:
            print(f"✅ {len(users)} user(s) configured: {', '.join(users.keys())}")
    else:
        print("⚠️  No API keys configured yet")
    
    print("\nOptions:")
    print("1. Set default API key")
    print("2. Add user-specific API key")
    print("3. Add environment-specific API key")
    print("4. List configured keys")
    print("5. Test a key")
    print("6. Exit")
    
    while True:
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            api_key = input("Enter default API key: ").strip()
            base_url = input("Enter base URL [http://localhost:3000]: ").strip() or "http://localhost:3000"
            description = input("Enter description [Default OpenWebUI instance]: ").strip() or "Default OpenWebUI instance"
            
            if manager.set_default_key(api_key, base_url, description):
                print("✅ Default key saved successfully")
            else:
                print("❌ Failed to save default key")
        
        elif choice == "2":
            username = input("Enter username: ").strip()
            api_key = input("Enter API key: ").strip()
            base_url = input("Enter base URL [http://localhost:3000]: ").strip() or "http://localhost:3000"
            email = input("Enter email (optional): ").strip()
            description = input("Enter description (optional): ").strip()
            
            if manager.add_user_key(username, api_key, base_url, email, description):
                print(f"✅ Key for user '{username}' saved successfully")
            else:
                print(f"❌ Failed to save key for user '{username}'")
        
        elif choice == "3":
            env_name = input("Enter environment name: ").strip()
            api_key = input("Enter API key: ").strip()
            base_url = input("Enter base URL: ").strip()
            
            if manager.add_environment_key(env_name, api_key, base_url):
                print(f"✅ Key for environment '{env_name}' saved successfully")
            else:
                print(f"❌ Failed to save key for environment '{env_name}'")
        
        elif choice == "4":
            print("\n📋 Configured Keys:")
            
            default = manager.get_default_key()
            if default:
                print(f"  Default: {default['base_url']} (key: ...{default['api_key'][-8:]})")
            
            users = manager.list_users()
            if users:
                print("  Users:")
                for username, config in users.items():
                    email_part = f" ({config.get('email', 'no email')})" if config.get('email') else ""
                    print(f"    {username}{email_part}: {config['base_url']} (key: ...{config['api_key'][-8:]})")
            
            environments = manager.list_environments()
            if environments:
                print("  Environments:")
                for env_name, config in environments.items():
                    print(f"    {env_name}: {config['base_url']} (key: ...{config['api_key'][-8:]})")
        
        elif choice == "5":
            api_key = input("Enter API key to test: ").strip()
            base_url = input("Enter base URL [http://localhost:3000]: ").strip() or "http://localhost:3000"
            
            print("🧪 Testing API key...")
            if manager.validate_key(api_key, base_url):
                print("✅ API key is valid")
            else:
                print("❌ API key validation failed")
        
        elif choice == "6":
            break
        
        else:
            print("Invalid option. Please select 1-6.")


if __name__ == "__main__":
    setup_api_keys_interactive()
