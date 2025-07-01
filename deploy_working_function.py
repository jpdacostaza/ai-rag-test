#!/usr/bin/env python3
"""
Deploy Working Memory Function
=============================
"""

import sqlite3
import time
import sys
import os

def deploy_working_function():
    """Deploy the working memory function"""
    db_path = "storage/openwebui/webui.db"
    function_file = "storage/openwebui/memory_function_working.py"
    
    try:
        with open(function_file, 'r', encoding='utf-8') as f:
            function_code = f.read()
        
        print(f"📖 Read {len(function_code)} characters")
        
        # Test syntax
        compile(function_code, function_file, 'exec')
        print("✅ Syntax valid")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Update the function
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
            print("✅ Working memory function deployed!")
            return True
        else:
            print("❌ No function found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Deploying Working Memory Function...")
    if deploy_working_function():
        print("🎉 Success!")
    else:
        sys.exit(1)
