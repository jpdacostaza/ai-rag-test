#!/usr/bin/env python3
"""
Deploy Filter-based Memory Function
=================================
"""

import sqlite3
import time
import sys
import os

def deploy_filter_function():
    """Deploy a filter-based memory function"""
    db_path = "storage/openwebui/webui.db"
    function_file = "storage/openwebui/memory_function_filter.py"
    
    try:
        with open(function_file, 'r', encoding='utf-8') as f:
            function_code = f.read()
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Update the function code and ensure it's active
        cursor.execute("""
            UPDATE function 
            SET content = ?,
                is_active = 1,
                updated_at = ?
            WHERE id = 'memory_function'
        """, (function_code, int(time.time())))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        if rows_affected > 0:
            print("✅ Filter-based memory function deployed!")
            return True
        else:
            print("❌ No function found to update")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    deploy_filter_function()
