#!/usr/bin/env python3
"""
OpenWebUI API Key Auto-Discovery and Installer Setup
===================================================

This script automatically:
1. Waits for OpenWebUI to be ready
2. Detects/extracts API keys from the running instance
3. Updates the api_function_installer.py with correct credentials
4. Restarts the function installer container

Eliminates the need for manual API key configuration.
"""

import asyncio
import httpx
import json
import os
import time
import sqlite3
import base64
import hashlib
import re
from pathlib import Path
from typing import Dict, Optional

# Configuration
OPENWEBUI_URL = "http://openwebui:8080"
OPENWEBUI_CONTAINER = "backend-openwebui"
INSTALLER_CONTAINER = "backend-api-function-installer"
DB_PATH = "/app/backend/data/webui.db"
INSTALLER_SCRIPT = "/app/scripts/api_function_installer.py"

MAX_RETRIES = 60
RETRY_DELAY = 10

def log(message: str, level: str = "INFO"):
    """Enhanced logging."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [API-DISCOVERY] [{level}] {message}")
    # Also flush to ensure immediate output
    import sys
    sys.stdout.flush()

def debug_environment():
    """Debug environment and dependencies."""
    log("[DEBUG] Starting environment check")
    log(f"Python version: {os.sys.version}")
    log(f"Current working directory: {os.getcwd()}")
    
    # Only show relevant environment variables
    openwebui_vars = {k: v for k, v in os.environ.items() if 'OPENWEBUI' in k.upper() or 'API' in k.upper()}
    if openwebui_vars:
        log("[DEBUG] Environment variables related to OpenWebUI:")
        for key, value in openwebui_vars.items():
            log(f"  {key}={value}")
    
    log("[DEBUG] Checking file system access...")
    try:
        os.makedirs("/app/backend/storage/openwebui", exist_ok=True)
        log("[SUCCESS] Can create storage directories")
    except Exception as e:
        log(f"[ERROR] Cannot create storage directories: {e}", "ERROR")
    
    log("[DEBUG] Testing network connectivity...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('openwebui', 8080))
        sock.close()
        if result == 0:
            log("[SUCCESS] Can connect to openwebui:8080")
        else:
            log(f"[ERROR] Cannot connect to openwebui:8080 (error: {result})", "ERROR")
    except Exception as e:
        log(f"[ERROR] Network test failed: {e}", "ERROR")

def wait_for_openwebui_basic():
    """Wait for OpenWebUI basic health check."""
    log("Waiting for OpenWebUI basic health...")
    
    for attempt in range(MAX_RETRIES):
        try:
            log(f"[DEBUG] Health check attempt {attempt + 1}/{MAX_RETRIES}")
            with httpx.Client(timeout=10) as client:
                response = client.get(f"{OPENWEBUI_URL}/health")
                log(f"[DEBUG] Health response: {response.status_code}")
                if response.status_code == 200:
                    log("[SUCCESS] OpenWebUI health endpoint responding")
                    return True
        except Exception as e:
            log(f"Attempt {attempt + 1}/{MAX_RETRIES} - OpenWebUI not ready: {e}", "DEBUG")
        
        time.sleep(RETRY_DELAY)
    
    return False

def wait_for_openwebui_setup():
    """Wait for OpenWebUI to be ready and attempt to set up admin user."""
    log("Checking OpenWebUI setup status...")
    
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=10) as client:
                log(f"[DEBUG] Setup check attempt {attempt + 1}/{MAX_RETRIES}")
                
                # First, try to check if we can access the API
                try:
                    response = client.get(f"{OPENWEBUI_URL}/api/v1/users/")
                    log(f"[DEBUG] Users API response: {response.status_code}")
                    
                    if response.status_code == 401:
                        # This means the API is working but requires auth - good!
                        log("[SUCCESS] OpenWebUI API is ready (requires authentication)")
                        return True
                    elif response.status_code == 200:
                        # API is accessible - check if there are users
                        try:
                            users = response.json()
                            if len(users) > 0:
                                log(f"[SUCCESS] OpenWebUI has {len(users)} existing users")
                                return True
                        except:
                            pass
                except httpx.RequestError as e:
                    log(f"[DEBUG] API request failed: {e}")
                    
                # Try to access the main page to see if OpenWebUI is responding
                try:
                    main_response = client.get(f"{OPENWEBUI_URL}/")
                    log(f"[DEBUG] Main page response: {main_response.status_code}")
                    
                    if main_response.status_code == 200:
                        # OpenWebUI is responding, let's assume it's ready
                        log("[SUCCESS] OpenWebUI main page accessible - assuming ready")
                        return True
                except httpx.RequestError as e:
                    log(f"[DEBUG] Main page request failed: {e}")
                    
        except Exception as e:
            log(f"Setup check {attempt + 1}/{MAX_RETRIES}: {e}", "DEBUG")
        
        if attempt < MAX_RETRIES - 1:
            log(f"[INFO] Waiting {RETRY_DELAY} seconds before next check...")
            time.sleep(RETRY_DELAY)
    
    log("[WARNING] OpenWebUI setup check failed, but proceeding anyway", "WARN")
    return True  # Proceed anyway - maybe the API endpoints changed
    
    log("[WARNING] Timeout waiting for OpenWebUI setup completion", "WARN")
    return False

def extract_api_keys_from_db() -> Optional[Dict[str, str]]:
    """Extract API keys from OpenWebUI database."""
    try:
        if not os.path.exists(DB_PATH):
            log(f"Database not found at {DB_PATH} - OpenWebUI not initialized yet", "DEBUG")
            return None
            
        log("Checking database for admin users with API keys...")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get first admin user
        cursor.execute("""
            SELECT id, email, api_key 
            FROM user 
            WHERE role = 'admin' 
            ORDER BY created_at ASC 
            LIMIT 1
        """)
        
        user = cursor.fetchone()
        if user:
            user_id, email, api_key = user
            
            if api_key:
                log(f"[SUCCESS] Found API key for admin user: {email}")
                
                # Try to get JWT token or create one
                # Note: JWT tokens are usually created dynamically
                # We'll use a placeholder or generate one if needed
                
                conn.close()
                return {
                    "api_key": api_key,
                    "admin_email": email,
                    "user_id": user_id,
                    "jwt_token": None  # Will try to get this via API
                }
        
        conn.close()
        log("No admin user with API key found yet", "DEBUG")
        return None
        
    except Exception as e:
        log(f"Error extracting from database: {e}", "DEBUG")
        return None

def try_api_key_login(email: str, api_key: str) -> Optional[str]:
    """Try to authenticate with API key and get JWT token."""
    try:
        log(f"Attempting API authentication for {email}...")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        with httpx.Client(timeout=10) as client:
            # Try to authenticate and get user info
            response = client.get(f"{OPENWEBUI_URL}/api/v1/users/user", headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                log(f"[SUCCESS] API key authentication successful for {email}")
                return api_key  # API key works as bearer token
            else:
                log(f"API key authentication failed: {response.status_code}", "DEBUG")
                return None
                
    except Exception as e:
        log(f"Error during API authentication: {e}", "DEBUG")
        return None

def create_api_key_via_signup() -> Optional[Dict[str, str]]:
    """Try to create admin account and get API key."""
    try:
        log("Attempting to create admin account...")
        
        # Default admin credentials
        admin_data = {
            "name": "Administrator",
            "email": "admin@localhost.local",
            "password": "admin123456",
            "role": "admin"
        }
        
        with httpx.Client(timeout=10) as client:
            # Check if signup is available
            response = client.post(f"{OPENWEBUI_URL}/api/v1/auths/signup", json=admin_data)
            
            if response.status_code in [200, 201]:
                signup_result = response.json()
                log("[SUCCESS] Admin account created successfully")
                
                # Now try to login and get API key
                login_data = {
                    "email": admin_data["email"],
                    "password": admin_data["password"]
                }
                
                login_response = client.post(f"{OPENWEBUI_URL}/api/v1/auths/signin", json=login_data)
                
                if login_response.status_code == 200:
                    login_result = login_response.json()
                    token = login_result.get("token")
                    
                    if token:
                        log("[SUCCESS] Login successful, got JWT token")
                        
                        # Try to get or create API key
                        headers = {"Authorization": f"Bearer {token}"}
                        api_key_response = client.get(f"{OPENWEBUI_URL}/api/v1/users/api-key", headers=headers)
                        
                        if api_key_response.status_code == 200:
                            api_key_data = api_key_response.json()
                            api_key = api_key_data.get("api_key")
                            
                            if api_key:
                                return {
                                    "api_key": api_key,
                                    "admin_email": admin_data["email"],
                                    "jwt_token": token
                                }
                
                return {
                    "admin_email": admin_data["email"],
                    "jwt_token": login_result.get("token"),
                    "api_key": None
                }
                        
    except Exception as e:
        log(f"Error creating admin account: {e}", "DEBUG")
        return None

def update_installer_script(credentials: Dict[str, str]) -> bool:
    """Update the API function installer script with discovered credentials."""
    try:
        log("Updating API function installer with discovered credentials...")
        
        if not os.path.exists(INSTALLER_SCRIPT):
            log(f"Installer script not found: {INSTALLER_SCRIPT}", "ERROR")
            return False
        
        # Read current script
        with open(INSTALLER_SCRIPT, 'r') as f:
            content = f.read()
        
        # Update credentials
        if credentials.get("admin_email"):
            content = content.replace(
                'ADMIN_EMAIL = "admin@theroot.za.net"',
                f'ADMIN_EMAIL = "{credentials["admin_email"]}"'
            )
        
        if credentials.get("jwt_token"):
            # Find and replace JWT token
            jwt_pattern = r'JWT_TOKEN = "eyJ[^"]*"'
            if re.search(jwt_pattern, content):
                content = re.sub(jwt_pattern, f'JWT_TOKEN = "{credentials["jwt_token"]}"', content)
        
        if credentials.get("api_key"):
            # Find and replace API key
            api_pattern = r'API_KEY = "sk-[^"]*"'
            if re.search(api_pattern, content):
                content = re.sub(api_pattern, f'API_KEY = "{credentials["api_key"]}"', content)
        
        # Write updated script
        with open(INSTALLER_SCRIPT, 'w') as f:
            f.write(content)
        
        log("[SUCCESS] API function installer script updated with new credentials")
        return True
        
    except Exception as e:
        log(f"Error updating installer script: {e}", "ERROR")
        return False

def restart_installer_container() -> bool:
    """Restart the API function installer container."""
    try:
        log("Restarting API function installer container...")
        
        import subprocess
        
        # Stop the container
        result = subprocess.run(
            ["docker", "restart", INSTALLER_CONTAINER],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            log("[SUCCESS] API function installer container restarted successfully")
            return True
        else:
            log(f"Failed to restart container: {result.stderr}", "ERROR")
            return False
            
    except Exception as e:
        log(f"Error restarting container: {e}", "ERROR")
        return False

def main():
    """Main auto-discovery and setup function."""
    log("[STARTUP] Starting API Key Auto-Discovery")
    
    # Only run debug environment check if no admin exists yet
    credentials = extract_api_keys_from_db()
    if not credentials:
        log("=" * 50)
        debug_environment()
    
    # Step 1: Wait for OpenWebUI basic health
    if not wait_for_openwebui_basic():
        log("[ERROR] OpenWebUI never became healthy", "ERROR")
        return False
    
    # Step 2: Wait for OpenWebUI setup completion
    if not wait_for_openwebui_setup():
        log("[WARNING] Proceeding despite setup timeout", "WARN")
    
    # Step 3: Try to get API credentials (extract-only mode)
    credentials = None
    
    # Method 1: Extract from database (primary method)
    credentials = extract_api_keys_from_db()
    
    # Method 2: Use environment variables if provided (fallback)
    if not credentials and os.getenv("OPENWEBUI_API_KEY"):
        credentials = {
            "api_key": os.getenv("OPENWEBUI_API_KEY"),
            "admin_email": os.getenv("OPENWEBUI_ADMIN_EMAIL", "admin@localhost.local"),
            "jwt_token": os.getenv("OPENWEBUI_JWT_TOKEN")
        }
        log("Using credentials from environment variables")
    
    if not credentials:
        log("[WARNING] No admin user with API key found yet", "WARN")
        log("[INFO] Manual setup required (system will auto-detect once complete):")
        log("1. Access OpenWebUI at http://localhost:8080")
        log("2. Create admin account and generate API key")
        log("3. Functions will install automatically within 1 minute")
        log("4. Container will validate for 5 minutes then shutdown")
        log("[INFO] Checking again in 60 seconds...")
        return False
    
    # Step 4: Update installer script
    if not update_installer_script(credentials):
        log("[ERROR] Failed to update installer script", "ERROR")
        return False
    
    log("[COMPLETE] API Key Auto-Discovery Complete!")
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        log("Auto-discovery interrupted", "WARN")
        exit(1)
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        exit(1)
