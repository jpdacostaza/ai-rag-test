#!/usr/bin/env python3
"""
Memory Function Startup Hook
Ensures memory function is always active on every OpenWebUI startup
"""

import sqlite3
import json
import os
import time
import sys

def update_function_in_database():
    """Update the memory function in the database with latest code and ensure it's active"""
    
    db_path = '/app/backend/data/webui.db'
    if not os.path.exists(db_path):
        print("Database not found, waiting...")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Read the latest function code
        function_code_path = '/app/backend/data/memory_function_code.py'
        if os.path.exists(function_code_path):
            with open(function_code_path, 'r') as f:
                latest_code = f.read()
            
            # Update function with latest code and ensure it's active
            cursor.execute("""
                UPDATE function 
                SET content = ?,
                    is_active = 1,
                    is_global = 1,
                    type = 'filter',
                    updated_at = ?
                WHERE id = 'memory_function'
            """, (latest_code, int(time.time())))
            
            if cursor.rowcount > 0:
                print("✅ Updated memory function with latest code")
            else:
                print("ℹ️  Memory function not found in database")
            
            conn.commit()
        
        # Ensure function is marked as active
        cursor.execute("""
            UPDATE function 
            SET is_active = 1, 
                is_global = 1,
                type = 'filter'
            WHERE id = 'memory_function'
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Memory function ensured to be active")
        return True
        
    except Exception as e:
        print(f"❌ Error updating function: {e}")
        return False

def main():
    """Main startup hook"""
    print("🚀 Memory Function Startup Hook")
    print("=" * 40)
    
    # Wait for database to be ready
    max_attempts = 30
    for attempt in range(max_attempts):
        if update_function_in_database():
            print("🎉 Memory function startup hook completed successfully!")
            break
        else:
            if attempt < max_attempts - 1:
                print(f"⏳ Attempt {attempt + 1}/{max_attempts}, waiting 2s...")
                time.sleep(2)
            else:
                print("❌ Failed to activate memory function after maximum attempts")
                sys.exit(1)

if __name__ == "__main__":
    main()
