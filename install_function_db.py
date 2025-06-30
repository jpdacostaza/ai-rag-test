#!/usr/bin/env python3
import sqlite3
import json
import hashlib
import time

# Read the function code
with open('/app/backend/data/memory_function_code.py', 'r') as f:
    function_code = f.read()

# Connect to database
conn = sqlite3.connect('/app/backend/data/webui.db')
cursor = conn.cursor()

# Check table structure
cursor.execute("PRAGMA table_info(function)")
columns = cursor.fetchall()
print("Function table columns:", columns)

# Create function entry
function_id = "memory_function"
function_name = "Memory Function"
created_at = int(time.time())

try:
    # Insert the function - using a default/system user ID
    cursor.execute("""
        INSERT OR REPLACE INTO function 
        (id, user_id, name, type, content, meta, valves, is_active, is_global, updated_at, created_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        function_id,
        "system",  # Using system as user_id
        function_name,
        "function",
        function_code,
        json.dumps({"description": "Persistent memory for conversations"}),
        json.dumps({}),
        True,
        True,
        created_at,
        created_at
    ))
    
    conn.commit()
    print("✅ Function inserted successfully!")
    
except Exception as e:
    print(f"❌ Error inserting function: {e}")
    
    # Try to find existing functions to see the required format
    cursor.execute("SELECT * FROM function LIMIT 1")
    row = cursor.fetchone()
    if row:
        print("Example function row:", row)
    else:
        print("No existing functions found")

finally:
    conn.close()
