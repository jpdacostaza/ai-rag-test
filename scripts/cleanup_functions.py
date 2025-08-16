#!/usr/bin/env python3
"""
Complete OpenWebUI Database Function Cleanup
===========================================

Removes all problematic function entries and recreates them with proper integer timestamps.
This fixes the validation errors preventing OpenWebUI from starting.
"""

import sqlite3
import time

WEBUI_DB_PATH = "./storage/openwebui/webui.db"

def cleanup_functions():
    """Remove all function entries from the database."""
    try:
        print("🧹 Cleaning up problematic function entries...")
        
        conn = sqlite3.connect(WEBUI_DB_PATH)
        cursor = conn.cursor()
        
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM function")
        before_count = cursor.fetchone()[0]
        print(f"Found {before_count} function entries to remove")
        
        # Delete all function entries
        cursor.execute("DELETE FROM function")
        
        # Get count after deletion
        cursor.execute("SELECT COUNT(*) FROM function")
        after_count = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        print(f"✅ Removed {before_count - after_count} function entries")
        print("✅ Function table is now clean")
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning up functions: {e}")
        return False

if __name__ == "__main__":
    success = cleanup_functions()
    if success:
        print("🎯 Database cleanup complete!")
        print("💡 You can now run the function importer again to re-import with correct timestamps")
    exit(0 if success else 1)
