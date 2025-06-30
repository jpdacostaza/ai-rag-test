#!/usr/bin/env python3
"""
Update Memory Function URL in Database
====================================
This script updates the memory function code in the database to use the correct API URL.
"""

import sqlite3
import sys
import os

def update_function_url():
    """Update the memory function URL in the database"""
    db_path = "storage/openwebui/webui.db"
    function_file = "storage/openwebui/memory_function_code.py"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
        
    if not os.path.exists(function_file):
        print(f"❌ Function file not found: {function_file}")
        return False
    
    try:
        # Read the updated function code
        with open(function_file, 'r', encoding='utf-8') as f:
            function_code = f.read()
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Update the function code
        cursor.execute("""
            UPDATE function 
            SET content = ?,
                updated_at = ?
            WHERE id = 'memory_function'
        """, (function_code, int(time.time())))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        if rows_affected > 0:
            print("✅ Memory function updated successfully!")
            print(f"   - Updated URL to: http://memory_api:8001")
            print(f"   - Rows affected: {rows_affected}")
            return True
        else:
            print("❌ No function found to update")
            return False
            
    except Exception as e:
        print(f"❌ Error updating function: {e}")
        return False

if __name__ == "__main__":
    import time
    print("🔧 Updating Memory Function URL...")
    if update_function_url():
        print("🎉 Function update complete!")
    else:
        print("💥 Function update failed!")
        sys.exit(1)
