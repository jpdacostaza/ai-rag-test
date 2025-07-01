#!/usr/bin/env python3
"""
Deploy Bulletproof Memory Function
=================================
This script replaces the current memory function with an ultra-robust version.
"""

import sqlite3
import time
import sys
import os

def deploy_bulletproof_function():
    """Deploy the bulletproof memory function"""
    db_path = "storage/openwebui/webui.db"
    function_file = "storage/openwebui/memory_function_bulletproof.py"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
        
    if not os.path.exists(function_file):
        print(f"❌ Bulletproof function file not found: {function_file}")
        return False
    
    try:
        # Read the bulletproof function code
        with open(function_file, 'r', encoding='utf-8') as f:
            function_code = f.read()
        
        print(f"📖 Read {len(function_code)} characters of bulletproof function code")
        
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
        
        if rows_affected == 0:
            print("⚠️  Function not found, creating new one...")
            cursor.execute("""
                INSERT INTO function (id, name, content, is_active, created_at, updated_at)
                VALUES ('memory_function', 'Memory Function', ?, 1, ?, ?)
            """, (function_code, int(time.time()), int(time.time())))
            rows_affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if rows_affected > 0:
            print("✅ Bulletproof memory function deployed successfully!")
            print(f"   - Function is now ultra-robust and won't auto-disable")
            print(f"   - Comprehensive error handling implemented")
            print(f"   - Rows affected: {rows_affected}")
            return True
        else:
            print("❌ Failed to deploy function")
            return False
            
    except Exception as e:
        print(f"❌ Error deploying function: {e}")
        return False

if __name__ == "__main__":
    print("🛡️  Deploying Bulletproof Memory Function...")
    if deploy_bulletproof_function():
        print("🎉 Deployment complete!")
        print("💡 The function should now remain active even if errors occur.")
    else:
        print("💥 Deployment failed!")
        sys.exit(1)
