#!/usr/bin/env python3
"""
Deploy Memory Filter to OpenWebUI
================================
"""

import sqlite3
import time
import os
import json

def deploy_memory_filter():
    """Deploy the memory filter to OpenWebUI database"""
    
    # Read the filter code
    filter_file = "memory/functions/memory_filter.py"
    if not os.path.exists(filter_file):
        print(f"❌ Filter file not found: {filter_file}")
        return False
    
    try:
        with open(filter_file, 'r', encoding='utf-8') as f:
            filter_code = f.read()
        
        # Connect to database
        db_path = "storage/openwebui/webui.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if filter already exists
        cursor.execute("SELECT id FROM function WHERE id = ? AND type = 'filter'", ("memory_filter",))
        exists = cursor.fetchone()
        
        current_time = int(time.time())
        
        if exists:
            # Update existing filter
            cursor.execute("""
                UPDATE function 
                SET content = ?,
                    is_active = 1,
                    is_global = 1,
                    updated_at = ?
                WHERE id = 'memory_filter' AND type = 'filter'
            """, (filter_code, current_time))
            print("✅ Memory filter updated!")
        else:
            # Insert new filter
            cursor.execute("""
                INSERT INTO function (
                    id, user_id, name, type, content, meta, 
                    created_at, updated_at, valves, is_active, is_global
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "memory_filter",           # id
                "",                        # user_id (empty for global)
                "Enhanced Memory Filter",   # name
                "filter",                  # type
                filter_code,              # content
                json.dumps({
                    "description": "Memory filter that stores and retrieves conversation context",
                    "author": "Memory System",
                    "version": "1.0.0"
                }),                       # meta
                current_time,             # created_at
                current_time,             # updated_at
                json.dumps({
                    "memory_api_url": "http://memory_api:8000",
                    "enable_memory": True,
                    "max_memories": 3,
                    "memory_threshold": 0.7,
                    "debug": True
                }),                       # valves
                1,                        # is_active
                1                         # is_global
            ))
            print("✅ Memory filter deployed!")
        
        conn.commit()
        
        # Verify the filter was created/updated
        cursor.execute("SELECT id, name, type, is_active FROM function WHERE type = 'filter'")
        filters = cursor.fetchall()
        print(f"\n=== AVAILABLE FILTERS ===")
        for f in filters:
            print(f"ID: {f[0]}, Name: {f[1]}, Type: {f[2]}, Active: {f[3]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error deploying filter: {e}")
        return False

if __name__ == "__main__":
    success = deploy_memory_filter()
    if success:
        print("\n🎉 Memory filter deployment complete!")
        print("Please restart OpenWebUI container to see the filter in the model settings.")
    else:
        print("\n❌ Memory filter deployment failed!")
