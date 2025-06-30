#!/usr/bin/env python3
"""
Fix Memory Threshold
==================
Set the memory relevance threshold to a very low value so memories are returned.
"""

import sqlite3
import time

def fix_threshold():
    """Fix the memory relevance threshold"""
    try:
        conn = sqlite3.connect('storage/openwebui/webui.db')
        cursor = conn.cursor()
        cursor.execute('SELECT content FROM function WHERE id = ?', ('memory_function',))
        result = cursor.fetchone()
        
        if not result:
            print("❌ Memory function not found!")
            return False
        
        content = result[0]
        
        # Set the threshold to 0.05 (5%) instead of 0.3 (30%)
        content = content.replace('memory_relevance_threshold: float = 0.3', 'memory_relevance_threshold: float = 0.05')
        content = content.replace('memory_relevance_threshold: float = 0.1', 'memory_relevance_threshold: float = 0.05')
        content = content.replace('memory_relevance_threshold: float = 0.01', 'memory_relevance_threshold: float = 0.05')
        
        # Also ensure debug is enabled
        content = content.replace('debug: bool = False', 'debug: bool = True')
        
        # Update in database
        cursor.execute("""
            UPDATE function 
            SET content = ?,
                updated_at = ?
            WHERE id = 'memory_function'
        """, (content, int(time.time())))
        
        conn.commit()
        conn.close()
        
        print("✅ Memory threshold fixed!")
        print("   - Relevance threshold: → 0.05 (5%)")
        print("   - Debug mode: → True")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing threshold: {e}")
        return False

if __name__ == "__main__":
    fix_threshold()
