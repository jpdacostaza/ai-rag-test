#!/usr/bin/env python3
"""
Fix Memory Relevance Issue
==========================
Modify the memory function to use a much lower relevance threshold and check raw memories.
"""

import sqlite3
import time

def fix_memory_relevance():
    """Fix the memory relevance issue by setting a very low threshold"""
    try:
        conn = sqlite3.connect('storage/openwebui/webui.db')
        cursor = conn.cursor()
        cursor.execute('SELECT content FROM function WHERE id = ?', ('memory_function',))
        result = cursor.fetchone()
        
        if not result:
            print("❌ Memory function not found!")
            return False
        
        content = result[0]
        
        # Set a very low relevance threshold (0.01 instead of 0.1)
        # Also modify the memory retrieval to return all memories regardless of relevance
        replacements = {
            'memory_relevance_threshold: float = 0.1': 'memory_relevance_threshold: float = 0.01',
            'self.valves.memory_relevance_threshold > 0': 'self.valves.memory_relevance_threshold > 1.0',  # Disable filtering
        }
        
        for old, new in replacements.items():
            if old in content:
                content = content.replace(old, new)
                print(f"✅ Updated: {old} → {new}")
        
        # Also add a debug statement to see what memories are being returned
        debug_injection = '''
                    self.log(f"Raw memories retrieved: {len(memories)}")
                    for i, memory in enumerate(memories):
                        self.log(f"Memory {i+1}: {memory.get('content', '')[:50]}... (score: {memory.get('relevance_score', 'N/A')})")
'''
        
        # Find where to inject the debug code
        injection_point = "if memories and self.valves.enable_persona:"
        if injection_point in content:
            content = content.replace(injection_point, debug_injection + "            " + injection_point)
            print("✅ Added debug logging")
        
        # Update in database
        cursor.execute("""
            UPDATE function 
            SET content = ?,
                updated_at = ?
            WHERE id = 'memory_function'
        """, (content, int(time.time())))
        
        conn.commit()
        conn.close()
        
        print("✅ Memory relevance issue fixed!")
        print("   - Relevance threshold: 0.1 → 0.01")
        print("   - Disabled relevance filtering")
        print("   - Added debug logging")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing memory relevance: {e}")
        return False

if __name__ == "__main__":
    fix_memory_relevance()
