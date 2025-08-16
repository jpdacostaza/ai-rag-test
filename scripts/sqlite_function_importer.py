#!/usr/bin/env python3
"""
OpenWebUI SQLite Function Importer
==================================

Directly imports function files into OpenWebUI's SQLite database.
This bypasses the web API authentication issues and directly inserts
function records into the SQLite database.

Requirements:
- Access to OpenWebUI's webui.db file
- Function files already copied to the functions directory
"""

import sqlite3
import json
import os
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional

WEBUI_DB_PATH = "/app/backend/data/webui.db"
FUNCTION_DIRS = [
    "/app/backend/data/functions/filters",
    "/app/backend/data/functions/tools"
]

def log(message: str, level: str = "INFO"):
    """Simple logging function."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def wait_for_database():
    """Wait for the database to be available."""
    log("Waiting for OpenWebUI database to be ready...")
    
    for attempt in range(30):
        if os.path.exists(WEBUI_DB_PATH):
            try:
                # Test database connection
                conn = sqlite3.connect(WEBUI_DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='function';")
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    log("✅ OpenWebUI database is ready!")
                    return True
                else:
                    log("Database exists but function table not found, creating...", "WARN")
                    return create_function_table()
            except Exception as e:
                log(f"Database not ready yet: {e}", "WARN")
        
        log(f"Attempt {attempt + 1}/30 - Database not ready...")
        time.sleep(10)
    
    log("❌ Database failed to become ready within timeout", "ERROR")
    return False

def create_function_table():
    """Create the function table if it doesn't exist."""
    try:
        conn = sqlite3.connect(WEBUI_DB_PATH)
        cursor = conn.cursor()
        
        # Create function table (based on OpenWebUI schema)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS function (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                meta TEXT,
                valves TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_global BOOLEAN DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        log("✅ Function table created successfully")
        return True
        
    except Exception as e:
        log(f"❌ Error creating function table: {e}", "ERROR")
        return False

def get_or_create_admin_user():
    """Get the admin user ID or create one."""
    try:
        conn = sqlite3.connect(WEBUI_DB_PATH)
        cursor = conn.cursor()
        
        # Check if user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user';")
        if not cursor.fetchone():
            log("User table doesn't exist, will use default admin user", "WARN")
            conn.close()
            return "admin"
        
        # Look for admin user
        cursor.execute("SELECT id FROM user WHERE role = 'admin' LIMIT 1;")
        result = cursor.fetchone()
        
        if result:
            admin_id = result[0]
            log(f"Found admin user: {admin_id}")
            conn.close()
            return admin_id
        
        # Look for any user
        cursor.execute("SELECT id FROM user LIMIT 1;")
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
            log(f"Using first available user: {user_id}")
            conn.close()
            return user_id
        
        log("No users found, using default admin", "WARN")
        conn.close()
        return "admin"
        
    except Exception as e:
        log(f"Error getting admin user: {e}", "WARN")
        return "admin"

def generate_function_id(content: str) -> str:
    """Generate a unique function ID based on content hash."""
    return hashlib.md5(content.encode()).hexdigest()[:16]

def extract_function_metadata(content: str, filename: str) -> Dict:
    """Extract function metadata from content."""
    lines = content.split('\n')
    
    # Extract basic info
    meta = {
        "manifest": {
            "title": filename.replace(".py", "").replace("_", " ").title(),
            "version": "1.0.0",
            "author": "Auto-imported",
            "description": f"Auto-imported function from {filename}"
        }
    }
    
    # Look for docstrings or comments for better metadata
    for i, line in enumerate(lines[:20]):  # Check first 20 lines
        if '"""' in line or "'''" in line:
            # Found docstring, extract it
            docstring_lines = []
            in_docstring = False
            quote_type = '"""' if '"""' in line else "'''"
            
            for j in range(i, min(i + 10, len(lines))):
                if quote_type in lines[j]:
                    if in_docstring:
                        break
                    in_docstring = True
                    continue
                if in_docstring:
                    docstring_lines.append(lines[j].strip())
            
            if docstring_lines:
                meta["manifest"]["description"] = " ".join(docstring_lines)[:200]
            break
    
    return meta

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
                    function_type = "filter" if "class Filter:" in content else "function"
                    function_name = filename.replace(".py", "")
                    
                    functions.append({
                        "id": generate_function_id(content),
                        "name": function_name,
                        "type": function_type,
                        "content": content,
                        "meta": extract_function_metadata(content, filename),
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

def function_exists(cursor, function_id: str) -> bool:
    """Check if function already exists in database."""
    cursor.execute("SELECT id FROM function WHERE id = ?", (function_id,))
    return cursor.fetchone() is not None

def import_function_to_db(func_data: Dict, admin_id: str) -> bool:
    """Import a single function directly into the SQLite database."""
    try:
        conn = sqlite3.connect(WEBUI_DB_PATH)
        cursor = conn.cursor()
        
        # Use integer timestamp as required by OpenWebUI
        current_time = int(time.time())
        
        # Check if function already exists
        if function_exists(cursor, func_data["id"]):
            log(f"Function {func_data['filename']} already exists, updating...")
            # Update existing function
            cursor.execute("""
                UPDATE function 
                SET content = ?, meta = ?, updated_at = ?
                WHERE id = ?
            """, (
                func_data["content"],
                json.dumps(func_data["meta"]),
                current_time,
                func_data["id"]
            ))
        else:
            log(f"Importing new function: {func_data['filename']}")
            # Insert new function
            cursor.execute("""
                INSERT INTO function 
                (id, user_id, name, type, content, meta, valves, is_active, is_global, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                func_data["id"],
                admin_id,
                func_data["name"],
                func_data["type"],
                func_data["content"],
                json.dumps(func_data["meta"]),
                "{}",  # Empty valves
                1,     # is_active
                1,     # is_global
                current_time,  # created_at (integer)
                current_time   # updated_at (integer)
            ))
        
        conn.commit()
        conn.close()
        log(f"✅ Successfully imported: {func_data['filename']}")
        return True
        
    except Exception as e:
        log(f"❌ Error importing {func_data['filename']}: {e}", "ERROR")
        return False

def main():
    """Main import function."""
    log("🚀 Starting OpenWebUI SQLite Function Importer")
    log("============================================================")
    
    # Wait for database to be ready
    if not wait_for_database():
        log("❌ Database not ready, exiting", "ERROR")
        return False
    
    # Get admin user
    admin_id = get_or_create_admin_user()
    log(f"Using user ID: {admin_id}")
    
    # Discover all functions
    functions = discover_functions()
    
    if not functions:
        log("⚠️ No functions found to import")
        return True
    
    # Import each function
    success_count = 0
    failed_count = 0
    
    for func_data in functions:
        if import_function_to_db(func_data, admin_id):
            success_count += 1
        else:
            failed_count += 1
    
    # Summary
    log("============================================================")
    log("🎯 Import Summary:")
    log(f"   • Total functions: {len(functions)}")
    log(f"   • Successfully imported: {success_count}")
    log(f"   • Failed: {failed_count}")
    
    if failed_count == 0:
        log("🎉 All functions imported successfully!")
        log("📋 Functions are now available in OpenWebUI")
        log("🔄 You may need to refresh the OpenWebUI page to see them")
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
