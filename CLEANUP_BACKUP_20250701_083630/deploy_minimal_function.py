#!/usr/bin/env python3
"""
Deploy Minimal Memory Function for Testing
=========================================
"""

import sqlite3
import time
import sys
import os

def deploy_minimal_function():
    """Deploy a minimal memory function for testing"""
    db_path = "storage/openwebui/webui.db"
    function_file = "storage/openwebui/memory_function_minimal.py"
    
    if not os.path.exists(function_file):
        print(f"❌ Minimal function file not found: {function_file}")
        return False
    
    try:
        # Read the minimal function code
        with open(function_file, 'r', encoding='utf-8') as f:
            function_code = f.read()
        
        print(f"📖 Read {len(function_code)} characters of minimal function code")
        
        # Test syntax
        try:
            compile(function_code, function_file, 'exec')
            print("✅ Function syntax is valid")
        except SyntaxError as e:
            print(f"❌ Syntax error: {e}")
            return False
        
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
            print("✅ Minimal memory function deployed successfully!")
            print(f"   - Rows affected: {rows_affected}")
            return True
        else:
            print("❌ No function found to update")
            return False
            
    except Exception as e:
        print(f"❌ Error deploying function: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Deploying Minimal Memory Function for Testing...")
    if deploy_minimal_function():
        print("🎉 Deployment complete!")
    else:
        print("💥 Deployment failed!")
        sys.exit(1)
