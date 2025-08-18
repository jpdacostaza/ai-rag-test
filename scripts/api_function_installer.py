#!/usr/bin/env python3
"""
OpenWebUI API-Based Function Installer with Admin Authentication
==============================================================

This installer uses the OpenWebUI API with proper admin authentication to:
1. Install functions through the official API endpoints
2. Provide true zero-configuration operation
3. Persist across container rebuilds
4. Support incremental updates and change detection

Uses admin credentials for proper authentication instead of direct database manipulation.
"""

import asyncio
import httpx
import json
import os
import time
import hashlib
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Configuration
OPENWEBUI_URL = "http://openwebui:8080"
ADMIN_EMAIL = "admin@theroot.za.net"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjNiY2E5ZGZkLTAxYTgtNDMwMi1iODU5LTlkNjFkMDU4ZTA2MCJ9.B11QggyALNEN9Amf2MYAinwYi6ciBfCTrwJxFb5xR9M"
API_KEY = "sk-9fa8c351765b4d6cbdabb332268238b0"

FUNCTION_DIRS = [
    "/app/backend/data/functions/filters",
    "/app/backend/data/functions/tools"
]
FINGERPRINT_FILE = "/app/backend/data/.function_fingerprints.json"

MAX_RETRIES = 30
RETRY_DELAY = 10
REQUEST_TIMEOUT = 30

def log(message: str, level: str = "INFO"):
    """Enhanced logging with API context."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [API-AUTH] [{level}] {message}")

def calculate_file_fingerprint(file_path: str) -> str:
    """Calculate SHA256 fingerprint of function file."""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return ""

def load_fingerprints() -> Dict[str, str]:
    """Load existing function fingerprints."""
    try:
        if os.path.exists(FINGERPRINT_FILE):
            with open(FINGERPRINT_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_fingerprints(fingerprints: Dict[str, str]):
    """Save function fingerprints for change detection."""
    try:
        os.makedirs(os.path.dirname(FINGERPRINT_FILE), exist_ok=True)
        with open(FINGERPRINT_FILE, 'w') as f:
            json.dump(fingerprints, f, indent=2)
    except Exception as e:
        log(f"Warning: Could not save fingerprints: {e}", "WARN")

def wait_for_openwebui():
    """Wait for OpenWebUI to be ready with API access."""
    log("Waiting for OpenWebUI API to be ready...")
    
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                # Test basic health endpoint
                response = client.get(f"{OPENWEBUI_URL}/health")
                if response.status_code == 200:
                    log("[SUCCESS] OpenWebUI health endpoint is ready!")
                    
                    # Test API access with admin API key
                    headers = {
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json"
                    }
                    
                    api_response = client.get(f"{OPENWEBUI_URL}/api/v1/functions/", headers=headers)
                    if api_response.status_code == 200:
                        log("[SUCCESS] OpenWebUI API access confirmed with admin auth!")
                        return True
                    else:
                        log(f"API not ready yet: {api_response.status_code}", "DEBUG")
                        
        except Exception as e:
            log(f"Attempt {attempt + 1}/{MAX_RETRIES} - OpenWebUI not ready: {e}", "DEBUG")
            
        time.sleep(RETRY_DELAY)
    
    log("OpenWebUI API failed to become ready within timeout", "ERROR")
    return False

def get_existing_functions() -> Dict[str, Dict]:
    """Get all existing functions from OpenWebUI API."""
    try:
        log("Fetching existing functions from API...")
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(f"{OPENWEBUI_URL}/api/v1/functions/", headers=headers)
            
            if response.status_code == 200:
                functions = response.json()
                log(f"Found {len(functions)} existing functions")
                
                # Create lookup by function name/id
                function_lookup = {}
                for func in functions:
                    function_lookup[func.get('name', '')] = func
                    if 'id' in func:
                        function_lookup[func['id']] = func
                        
                return function_lookup
            else:
                log(f"Failed to fetch functions: {response.status_code} - {response.text}", "ERROR")
                return {}
                
    except Exception as e:
        log(f"Error fetching existing functions: {e}", "ERROR")
        return {}

def discover_functions_with_fingerprints() -> List[Dict]:
    """Discover functions with fingerprint calculation."""
    functions = []
    
    for func_dir in FUNCTION_DIRS:
        if not os.path.exists(func_dir):
            log(f"Function directory not found: {func_dir}", "DEBUG")
            continue
            
        log(f"Scanning: {func_dir}")
        
        for file_path in Path(func_dir).glob("*.py"):
            filename = file_path.name
            
            # Skip system files
            if filename.startswith(("test_", "__", ".")):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Validate function content
                if not ("class Filter:" in content or "class Tools:" in content):
                    log(f"Skipping {filename} - no valid class found", "DEBUG")
                    continue
                
                function_type = "filter" if "class Filter:" in content else "function"
                function_name = filename.replace(".py", "")
                fingerprint = calculate_file_fingerprint(file_path)
                
                # Extract title and description from content
                title = function_name.replace("_", " ").title()
                description = f"Auto-imported {function_type}: {filename}"
                
                # Look for docstring for better description
                lines = content.split('\n')
                for line in lines[:20]:
                    if '"""' in line or "'''" in line:
                        # Extract docstring content
                        break
                
                functions.append({
                    "name": function_name,
                    "type": function_type,
                    "content": content,
                    "fingerprint": fingerprint,
                    "filename": filename,
                    "path": str(file_path),
                    "manifest": {
                        "title": title,
                        "version": "1.0.0",
                        "author": "API Auto-Installer",
                        "description": description
                    }
                })
                
                log(f"Discovered: {filename} ({function_type}) [fingerprint: {fingerprint[:8]}...]")
                
            except Exception as e:
                log(f"Error processing {file_path}: {e}", "ERROR")
                
    log(f"Found {len(functions)} functions for API installation")
    return functions

def create_function_via_api(func_data: Dict) -> bool:
    """Create a new function via OpenWebUI API."""
    try:
        log(f"Creating function: {func_data['filename']}")
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Prepare function data for API
        api_data = {
            "id": func_data["name"],
            "name": func_data["name"],
            "type": func_data["type"],
            "content": func_data["content"],
            "meta": {
                "manifest": func_data["manifest"]
            }
        }
        
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.post(
                f"{OPENWEBUI_URL}/api/v1/functions/create",
                headers=headers,
                json=api_data
            )
            
            if response.status_code in [200, 201]:
                log(f"[SUCCESS] Successfully created: {func_data['filename']}")
                return True
            else:
                log(f"[ERROR] Failed to create {func_data['filename']}: {response.status_code} - {response.text}", "ERROR")
                return False
                
    except Exception as e:
        log(f"[ERROR] Error creating {func_data['filename']}: {e}", "ERROR")
        return False

def update_function_via_api(func_data: Dict, existing_func_id: str) -> bool:
    """Update an existing function via OpenWebUI API."""
    try:
        log(f"Updating function: {func_data['filename']}")
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Prepare function data for API
        api_data = {
            "id": existing_func_id,
            "name": func_data["name"],
            "type": func_data["type"],
            "content": func_data["content"],
            "meta": {
                "manifest": func_data["manifest"]
            }
        }
        
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.post(
                f"{OPENWEBUI_URL}/api/v1/functions/id/{existing_func_id}/update",
                headers=headers,
                json=api_data
            )
            
            if response.status_code in [200, 201]:
                log(f"[SUCCESS] Successfully updated: {func_data['filename']}")
                return True
            else:
                log(f"[ERROR] Failed to update {func_data['filename']}: {response.status_code} - {response.text}", "ERROR")
                return False
                
    except Exception as e:
        log(f"[ERROR] Error updating {func_data['filename']}: {e}", "ERROR")
        return False

def toggle_function_active(func_id: str) -> bool:
    """Toggle function active status using the toggle endpoint."""
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.post(
                f"{OPENWEBUI_URL}/api/v1/functions/id/{func_id}/toggle",
                headers=headers,
                json={}
            )
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                is_active = response_data.get("is_active", False)
                log(f"[SUCCESS] Toggled function {func_id}: is_active={is_active}")
                return True
            else:
                log(f"[ERROR] Failed to toggle {func_id}: {response.status_code} - {response.text}", "ERROR")
                return False
                
    except Exception as e:
        log(f"[ERROR] Error toggling {func_id}: {e}", "ERROR")
        return False


def toggle_function_global(func_id: str) -> bool:
    """Toggle function global status using the global toggle endpoint."""
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.post(
                f"{OPENWEBUI_URL}/api/v1/functions/id/{func_id}/toggle/global",
                headers=headers,
                json={}
            )
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                is_global = response_data.get("is_global", False)
                log(f"[SUCCESS] Toggled function {func_id}: is_global={is_global}")
                return True
            else:
                log(f"[ERROR] Failed to toggle global {func_id}: {response.status_code} - {response.text}", "ERROR")
                return False
                
    except Exception as e:
        log(f"[ERROR] Error toggling global {func_id}: {e}", "ERROR")
        return False

def delete_function_via_api(func_id: str, func_name: str) -> bool:
    """Delete a function via OpenWebUI API."""
    try:
        log(f"Deleting orphaned function: {func_name}")
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.delete(
                f"{OPENWEBUI_URL}/api/v1/functions/id/{func_id}/delete",
                headers=headers
            )
            
            if response.status_code in [200, 204]:
                log(f"[SUCCESS] Successfully deleted: {func_name}")
                return True
            else:
                log(f"[ERROR] Failed to delete {func_name}: {response.status_code} - {response.text}", "ERROR")
                return False
                
    except Exception as e:
        log(f"[ERROR] Error deleting {func_name}: {e}", "ERROR")
        return False

def install_or_update_functions(functions: List[Dict], existing_functions: Dict[str, Dict], stored_fingerprints: Dict[str, str], force_update: bool = False) -> tuple:
    """Install or update functions based on changes."""
    success_count = 0
    failed_count = 0
    updated_count = 0
    created_count = 0
    
    for func_data in functions:
        func_name = func_data["name"]
        current_fingerprint = func_data["fingerprint"]
        stored_fingerprint = stored_fingerprints.get(func_data["filename"], "")
        
        # Check if function exists in OpenWebUI
        existing_func = existing_functions.get(func_name)
        
        # Determine if update is needed
        needs_update = current_fingerprint != stored_fingerprint or force_update
        
        if existing_func and not needs_update:
            log(f"[SKIP] {func_data['filename']} - up to date", "DEBUG")
            success_count += 1
            continue
        
        # Perform create or update
        if existing_func:
            if update_function_via_api(func_data, existing_func['id']):
                # After successful update, ensure the function is active
                current_active = existing_func.get("is_active", False)
                if not current_active:
                    log(f"Enabling function: {func_data['filename']}")
                    toggle_function_active(existing_func['id'])
                    log(f"Setting global: {func_data['filename']}")
                    toggle_function_global(existing_func['id'])
                success_count += 1
                updated_count += 1
            else:
                failed_count += 1
        else:
            if create_function_via_api(func_data):
                # After successful creation, enable the function
                log(f"Enabling function: {func_data['filename']}")
                toggle_function_active(func_data["name"])
                log(f"Setting global: {func_data['filename']}")
                toggle_function_global(func_data["name"])
                success_count += 1
                created_count += 1
            else:
                failed_count += 1
    
    return success_count, failed_count, created_count, updated_count

def cleanup_orphaned_functions(current_functions: List[Dict], existing_functions: Dict[str, Dict]) -> int:
    """Remove functions that no longer exist in filesystem."""
    current_names = {f["name"] for f in current_functions}
    removed_count = 0
    
    for func_name, func_data in existing_functions.items():
        # Only remove functions that were auto-installed (have our metadata pattern)
        if func_name not in current_names:
            meta = func_data.get('meta', {})
            manifest = meta.get('manifest', {})
            author = manifest.get('author', '')
            
            if 'Auto-Installer' in author:
                if delete_function_via_api(func_data['id'], func_name):
                    removed_count += 1
    
    return removed_count

def main(force_update: bool = False):
    """Main API-based installation function."""
    log("[STARTUP] Starting API-Based Function Auto-Installer")
    log("=" * 65)
    log(f"Admin: {ADMIN_EMAIL}")
    log(f"API: {OPENWEBUI_URL}")
    log(f"[CONFIG] Force update mode: {force_update}")
    
    # Wait for OpenWebUI API to be ready
    if not wait_for_openwebui():
        log("[ERROR] OpenWebUI API not ready, exiting", "ERROR")
        return False
    
    # Get existing functions
    existing_functions = get_existing_functions()
    
    # Load stored fingerprints
    stored_fingerprints = load_fingerprints()
    if force_update:
        # Clear stored fingerprints to force all functions to be treated as changed
        log("[INFO] Clearing stored fingerprints for force update")
        stored_fingerprints = {}
    
    # Discover all functions
    functions = discover_functions_with_fingerprints()
    
    if not functions:
        log("[WARNING] No functions found to install")
        return True
    
    # Install/update functions
    success_count, failed_count, created_count, updated_count = install_or_update_functions(
        functions, existing_functions, stored_fingerprints, force_update
    )
    
    # Cleanup orphaned functions
    removed_count = cleanup_orphaned_functions(functions, existing_functions)
    
    # Save fingerprints for next run
    new_fingerprints = {f["filename"]: f["fingerprint"] for f in functions}
    save_fingerprints(new_fingerprints)
    
    # Summary
    log("=" * 65)
    log("[SUMMARY] API-Based Installation Summary:")
    log(f"   - Functions processed: {len(functions)}")
    log(f"   - Successfully processed: {success_count}")
    log(f"   - Failed: {failed_count}")
    log(f"   - Created: {created_count}")
    log(f"   - Updated: {updated_count}")
    log(f"   - Removed (orphaned): {removed_count}")
    
    if failed_count == 0:
        log("[COMPLETE] API-based installation completed successfully!")
        log("[INFO] Functions are now available in OpenWebUI")
        log("[INFO] No manual intervention required")
        return True
    else:
        log(f"[WARNING] {failed_count} functions failed - but system is resilient", "WARN")
        return success_count > 0  # Partial success is OK

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="OpenWebUI API-Based Function Installer")
    parser.add_argument("--force-update", action="store_true", 
                       help="Force update all functions regardless of fingerprint changes")
    args = parser.parse_args()
    
    try:
        success = main(force_update=args.force_update)
        exit(0 if success else 1)
    except KeyboardInterrupt:
        log("Installation interrupted", "WARN")
        exit(1)
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        exit(1)
