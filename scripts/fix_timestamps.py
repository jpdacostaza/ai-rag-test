#!/usr/bin/env python3
"""
Fix OpenWebUI Database Timestamps
=================================

Fixes the timestamp format in the OpenWebUI database.
OpenWebUI expects integer timestamps but our importer created float timestamps.
"""

import sqlite3
import time

WEBUI_DB_PATH = "./storage/openwebui/webui.db"

def fix_timestamps():
    """Fix timestamp format in the function table."""
    try:
        print("🔧 Fixing function table timestamps...")
        
        conn = sqlite3.connect(WEBUI_DB_PATH)
        cursor = conn.cursor()
        
        # Get all functions with their current timestamps
        cursor.execute("SELECT id, created_at, updated_at FROM function")
        functions = cursor.fetchall()
        
        print(f"Found {len(functions)} functions to fix")
        
        # Update each function with integer timestamps
        for func_id, created_at, updated_at in functions:
            # Convert to integer (truncate the decimal part)
            int_created = int(float(created_at))
            int_updated = int(float(updated_at))
            
            cursor.execute("""
                UPDATE function 
                SET created_at = ?, updated_at = ?
                WHERE id = ?
            """, (int_created, int_updated, func_id))
            
            print(f"Fixed {func_id}: {created_at} -> {int_created}, {updated_at} -> {int_updated}")
        
        conn.commit()
        conn.close()
        
        print("✅ Successfully fixed all timestamps!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing timestamps: {e}")
        return False

if __name__ == "__main__":
    success = fix_timestamps()
    exit(0 if success else 1)
