#!/usr/bin/env python3
"""
Quick Debug Configuration
========================
Enable debug mode and lower relevance threshold to see what's happening.
"""

import sqlite3
import time

def update_debug_config():
    """Update configuration for debugging"""
    try:
        conn = sqlite3.connect('storage/openwebui/webui.db')
        cursor = conn.cursor()
        cursor.execute('SELECT content FROM function WHERE id = ?', ('memory_function',))
        result = cursor.fetchone()
        
        if not result:
            print("❌ Memory function not found!")
            return False
        
        content = result[0]
        
        # Update configuration values for debugging
        replacements = {
            'memory_relevance_threshold: float = 0.3': 'memory_relevance_threshold: float = 0.1',
            'debug: bool = False': 'debug: bool = True',
            'show_memory_in_response: bool = False': 'show_memory_in_response: bool = True'
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        # Update in database
        cursor.execute("""
            UPDATE function 
            SET content = ?,
                updated_at = ?
            WHERE id = 'memory_function'
        """, (content, int(time.time())))
        
        conn.commit()
        conn.close()
        
        print("✅ Debug configuration updated!")
        print("   - Relevance threshold: 0.3 → 0.1")
        print("   - Debug mode: False → True")
        print("   - Show memory in response: False → True")
        return True
        
    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return False

if __name__ == "__main__":
    update_debug_config()
