#!/usr/bin/env python3
"""
Check Persona Configuration
==========================
Verify the current persona settings in the memory function.
"""

import sqlite3
import re

def check_persona_config():
    """Check current persona configuration"""
    try:
        conn = sqlite3.connect('storage/openwebui/webui.db')
        cursor = conn.cursor()
        cursor.execute('SELECT content FROM function WHERE id = ?', ('memory_function',))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            print("❌ Memory function not found!")
            return
        
        content = result[0]
        
        # Extract persona settings
        settings = {}
        patterns = {
            'persona_style': r'persona_style: str = "([^"]+)"',
            'inject_memories_as': r'inject_memories_as: str = "([^"]+)"',
            'enable_persona': r'enable_persona: bool = (True|False)',
            'memory_relevance_threshold': r'memory_relevance_threshold: float = ([0-9.]+)',
            'debug': r'debug: bool = (True|False)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                settings[key] = match.group(1)
        
        print("🎭 Current Persona Configuration:")
        print("=" * 40)
        for key, value in settings.items():
            print(f"   {key}: {value}")
        
        # Check if persona template exists
        if 'persona_template: str = """' in content:
            start = content.find('persona_template: str = """') + len('persona_template: str = """')
            end = content.find('"""', start)
            if end > start:
                template = content[start:end].strip()
                print(f"\n📝 Persona Template (first 100 chars):")
                print(f"   {template[:100]}...")
        
        return settings
        
    except Exception as e:
        print(f"❌ Error checking config: {e}")
        return None

if __name__ == "__main__":
    check_persona_config()
