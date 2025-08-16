#!/usr/bin/env python3
"""
OpenWebUI Function Database Importer
====================================

Imports function files into OpenWebUI's database using the proper import API.
This script creates a user session and uses the import functionality to properly
register functions in the OpenWebUI database.

Requirements:
- OpenWebUI must be running and accessible
- Admin user must exist (first user created is automatically admin)
- Function files must be in the correct directories
"""

import asyncio
import httpx
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

OPENWEBUI_URL = "http://openwebui:8080"
MAX_RETRIES = 30
RETRY_DELAY = 10
REQUEST_TIMEOUT = 30

# Function directories to scan
FUNCTION_DIRS = [
    "/app/backend/data/functions/filters",
    "/app/backend/data/functions/tools"
]

def log(message: str, level: str = "INFO"):
    """Simple logging function."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def wait_for_openwebui():
    """Wait for OpenWebUI to be ready."""
    log("Waiting for OpenWebUI to be ready...")
    
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                response = client.get(f"{OPENWEBUI_URL}/health")
                if response.status_code == 200:
                    log("OpenWebUI is ready!")
                    return True
        except Exception as e:
            log(f"Attempt {attempt + 1}/{MAX_RETRIES} - OpenWebUI not ready: {e}", "WARN")
            
        time.sleep(RETRY_DELAY)
    
    log("OpenWebUI failed to become ready within timeout", "ERROR")
    return False

def create_admin_user():
    """Create the first admin user if none exists."""
    try:
        log("Checking if admin user needs to be created...")
        
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            # Check if we need to create an admin user
            response = client.get(f"{OPENWEBUI_URL}/api/config")
            
            if response.status_code == 200:
                config = response.json()
                if config.get("features", {}).get("auth", True):
                    # Try to create admin user
                    admin_data = {
                        "name": "Admin",
                        "email": "admin@localhost",
                        "password": "admin123",
                        "role": "admin"
                    }
                    
                    signup_response = client.post(
                        f"{OPENWEBUI_URL}/api/v1/auths/signup",
                        json=admin_data
                    )
                    
                    if signup_response.status_code in [200, 201]:
                        log("✅ Admin user created successfully")
                        return admin_data
                    elif signup_response.status_code == 400:
                        log("Admin user already exists, will attempt login")
                        return admin_data
                    else:
                        log(f"Failed to create admin user: {signup_response.status_code} - {signup_response.text}", "ERROR")
                        
    except Exception as e:
        log(f"Error creating admin user: {e}", "ERROR")
        
    return None

def login_admin():
    """Login as admin and get session cookies."""
    try:
        log("Attempting admin login...")
        
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            login_data = {
                "email": "admin@localhost",
                "password": "admin123"
            }
            
            response = client.post(
                f"{OPENWEBUI_URL}/api/v1/auths/signin",
                json=login_data
            )
            
            if response.status_code == 200:
                log("✅ Admin login successful")
                return client.cookies
            else:
                log(f"Admin login failed: {response.status_code} - {response.text}", "ERROR")
                
    except Exception as e:
        log(f"Error during admin login: {e}", "ERROR")
        
    return None

def discover_functions() -> List[Dict]:
    """Discover all function files."""
    functions = []
    
    for func_dir in FUNCTION_DIRS:
        if not os.path.exists(func_dir):
            log(f"Function directory not found: {func_dir}", "WARN")
            continue
            
        log(f"Scanning for functions in: {func_dir}")
        
        for file_path in Path(func_dir).glob("*.py"):
            filename = file_path.name
            
            # Skip test files and non-function files
            if filename.startswith("test_") or filename.startswith("__"):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Basic validation - must have Filter or Tools class
                if "class Filter:" in content or "class Tools:" in content:
                    function_type = "filter" if "class Filter:" in content else "tool"
                    
                    functions.append({
                        "name": filename.replace(".py", ""),
                        "type": function_type,
                        "content": content,
                        "filename": filename,
                        "path": str(file_path)
                    })
                    
                    log(f"Discovered function: {filename} ({function_type})")
                else:
                    log(f"Skipping {filename} - no Filter or Tools class found", "WARN")
                    
            except Exception as e:
                log(f"Error reading {file_path}: {e}", "ERROR")
                
    log(f"Found {len(functions)} functions to import")
    return functions

def import_function(func_data: Dict, cookies) -> bool:
    """Import a single function using the Import Functions API."""
    try:
        log(f"Importing function: {func_data['filename']}")
        
        with httpx.Client(cookies=cookies, timeout=REQUEST_TIMEOUT) as client:
            # Import the function content
            import_data = {
                "content": func_data["content"]
            }
            
            response = client.post(
                f"{OPENWEBUI_URL}/api/v1/functions/import",
                json=import_data
            )
            
            if response.status_code in [200, 201]:
                log(f"✅ Successfully imported: {func_data['filename']}")
                return True
            else:
                log(f"❌ Failed to import {func_data['filename']}: {response.status_code} - {response.text}", "ERROR")
                return False
                
    except Exception as e:
        log(f"❌ Error importing {func_data['filename']}: {e}", "ERROR")
        return False

def main():
    """Main import function."""
    log("🚀 Starting OpenWebUI Function Database Importer")
    log("============================================================")
    
    # Wait for OpenWebUI to be ready
    if not wait_for_openwebui():
        log("❌ OpenWebUI not ready, exiting", "ERROR")
        return False
    
    # Create admin user if needed
    admin_data = create_admin_user()
    if not admin_data:
        log("❌ Failed to create/verify admin user", "ERROR")
        return False
    
    # Login and get session
    cookies = login_admin()
    if not cookies:
        log("❌ Failed to login as admin", "ERROR")
        return False
    
    # Discover all functions
    functions = discover_functions()
    
    if not functions:
        log("⚠️ No functions found to import")
        return True
    
    # Import each function
    success_count = 0
    failed_count = 0
    
    for func_data in functions:
        if import_function(func_data, cookies):
            success_count += 1
        else:
            failed_count += 1
            
        # Small delay between imports
        time.sleep(2)
    
    # Summary
    log("============================================================")
    log("🎯 Import Summary:")
    log(f"   • Total functions: {len(functions)}")
    log(f"   • Successfully imported: {success_count}")
    log(f"   • Failed: {failed_count}")
    
    if failed_count == 0:
        log("🎉 All functions imported successfully!")
        log("📋 Functions are now available in OpenWebUI Admin Panel > Functions")
        return True
    else:
        log(f"⚠️ {failed_count} functions failed to import", "WARN")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        log("Import interrupted by user", "WARN")
        exit(1)
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        exit(1)
