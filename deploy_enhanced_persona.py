#!/usr/bin/env python3
"""
Deploy Enhanced Persona Memory Function
=====================================
"""

import sqlite3
import time
import sys
import os

def deploy_enhanced_function():
    """Deploy the enhanced persona memory function"""
    db_path = "storage/openwebui/webui.db"
    function_file = "storage/openwebui/memory_function_working.py"
    
    try:
        with open(function_file, 'r', encoding='utf-8') as f:
            function_code = f.read()
        
        print(f"📖 Read {len(function_code)} characters")
        
        # Test syntax
        try:
            compile(function_code, function_file, 'exec')
            print("✅ Syntax valid")
        except SyntaxError as e:
            print(f"❌ Syntax error: {e}")
            return False
        
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
            print("✅ Enhanced persona memory function deployed!")
            print("🎭 New persona features:")
            print("   - Multiple persona styles (helpful, casual, professional, creative)")
            print("   - Configurable memory injection methods")
            print("   - Enhanced memory formatting")
            print("   - Relevance threshold filtering")
            print("   - Debug and visibility options")
            return True
        else:
            print("❌ No function found to update")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🎭 Deploying Enhanced Persona Memory Function...")
    if deploy_enhanced_function():
        print("🎉 Success! Enhanced persona features are now available.")
    else:
        print("💥 Deployment failed!")
        sys.exit(1)
