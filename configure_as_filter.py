#!/usr/bin/env python3
import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cursor = conn.cursor()

print("🔧 Updating Memory Function to be a proper Filter...")

# Read the current function
cursor.execute("SELECT content FROM function WHERE id = 'memory_function'")
func_content = cursor.fetchone()

if func_content:
    # Update the metadata to indicate this is a filter with inlet/outlet
    meta = {
        "description": "Persistent memory for conversations",
        "type": "filter",
        "has_inlet": True,
        "has_outlet": True,
        "manifest": {
            "type": "filter",
            "id": "memory_function",
            "name": "Memory Function",
            "description": "Provides persistent memory functionality for conversations",
            "version": "1.0.0",
            "required": False
        }
    }
    
    # Update the function with proper metadata
    cursor.execute("""
        UPDATE function 
        SET type = 'filter', 
            meta = ?, 
            is_active = 1, 
            is_global = 1 
        WHERE id = 'memory_function'
    """, (json.dumps(meta),))
    
    conn.commit()
    
    # Verify the update
    cursor.execute("SELECT id, name, type, is_active, is_global, meta FROM function WHERE id = 'memory_function'")
    func = cursor.fetchone()
    
    print("✅ Updated function:")
    print(f"   ID: {func[0]}")
    print(f"   Name: {func[1]}")
    print(f"   Type: {func[2]}")
    print(f"   Active: {func[3]}")
    print(f"   Global: {func[4]}")
    print(f"   Meta: {func[5]}")
    
else:
    print("❌ Function not found!")

conn.close()
print("🎉 Memory Function configured as Filter!")
