#!/usr/bin/env python3
"""
Configure Memory Function Persona Settings
========================================
This script allows you to customize the persona behavior of the memory function.
"""

import sqlite3
import json
import sys

def get_current_config():
    """Get current function configuration"""
    try:
        conn = sqlite3.connect('storage/openwebui/webui.db')
        cursor = conn.cursor()
        cursor.execute('SELECT content FROM function WHERE id = ?', ('memory_function',))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            content = result[0]
            # Extract current valves configuration
            if 'class Valves(BaseModel):' in content:
                return True
        return False
    except Exception as e:
        print(f"Error reading config: {e}")
        return False

def update_persona_config(style="helpful", injection_method="system", enable_persona=True, 
                         template=None, relevance_threshold=0.3, debug=False):
    """Update persona configuration in the database"""
    try:
        conn = sqlite3.connect('storage/openwebui/webui.db')
        cursor = conn.cursor()
        cursor.execute('SELECT content FROM function WHERE id = ?', ('memory_function',))
        result = cursor.fetchone()
        
        if not result:
            print("❌ Memory function not found!")
            return False
        
        content = result[0]
        
        # Update configuration values in the code
        replacements = {
            'persona_style: str = "helpful"': f'persona_style: str = "{style}"',
            'inject_memories_as: str = "system"': f'inject_memories_as: str = "{injection_method}"',
            'enable_persona: bool = True': f'enable_persona: bool = {enable_persona}',
            'memory_relevance_threshold: float = 0.3': f'memory_relevance_threshold: float = {relevance_threshold}',
            'debug: bool = False': f'debug: bool = {debug}'
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        # Update custom template if provided
        if template:
            # Find and replace the persona_template
            start_marker = 'persona_template: str = """'
            end_marker = '"""'
            
            start_idx = content.find(start_marker)
            if start_idx != -1:
                start_idx += len(start_marker)
                end_idx = content.find(end_marker, start_idx)
                if end_idx != -1:
                    content = content[:start_idx] + template + content[end_idx:]
        
        # Update in database
        cursor.execute("""
            UPDATE function 
            SET content = ?,
                updated_at = ?
            WHERE id = 'memory_function'
        """, (content, int(time.time())))
        
        conn.commit()
        conn.close()
        
        print("✅ Persona configuration updated!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return False

def interactive_config():
    """Interactive configuration menu"""
    print("🎭 Memory Function Persona Configuration")
    print("=" * 50)
    
    if not get_current_config():
        print("❌ Memory function not found or not accessible")
        return
    
    print("\nPersona Style Options:")
    print("1. helpful (default) - Friendly and supportive")
    print("2. casual - Relaxed and conversational") 
    print("3. professional - Formal and business-like")
    print("4. creative - Artistic and imaginative")
    
    style_choice = input("\nChoose persona style (1-4, or press Enter for current): ").strip()
    styles = {"1": "helpful", "2": "casual", "3": "professional", "4": "creative"}
    style = styles.get(style_choice, "helpful")
    
    print("\nMemory Injection Methods:")
    print("1. system (default) - Inject as system message")
    print("2. user - Add as user message")
    print("3. context - Append to current user message")
    
    injection_choice = input("Choose injection method (1-3, or press Enter for current): ").strip()
    injections = {"1": "system", "2": "user", "3": "context"}
    injection = injections.get(injection_choice, "system")
    
    enable_persona = input("Enable persona features? (Y/n): ").strip().lower() != 'n'
    
    relevance_input = input("Memory relevance threshold (0.0-1.0, default 0.3): ").strip()
    try:
        relevance = float(relevance_input) if relevance_input else 0.3
    except ValueError:
        relevance = 0.3
    
    debug = input("Enable debug logging? (y/N): ").strip().lower() == 'y'
    
    # Custom template option
    custom_template = None
    if input("Use custom persona template? (y/N): ").strip().lower() == 'y':
        print("\nEnter custom template (use {memory_context} and {user_name} as placeholders):")
        custom_template = input("> ")
    
    print(f"\n📝 Configuration Summary:")
    print(f"   Persona Style: {style}")
    print(f"   Injection Method: {injection}")
    print(f"   Persona Enabled: {enable_persona}")
    print(f"   Relevance Threshold: {relevance}")
    print(f"   Debug Mode: {debug}")
    if custom_template:
        print(f"   Custom Template: {custom_template[:50]}...")
    
    confirm = input("\nApply this configuration? (Y/n): ").strip().lower() != 'n'
    
    if confirm:
        success = update_persona_config(
            style=style,
            injection_method=injection,
            enable_persona=enable_persona,
            template=custom_template,
            relevance_threshold=relevance,
            debug=debug
        )
        
        if success:
            print("\n🎉 Configuration applied successfully!")
            print("💡 Restart OpenWebUI to apply changes:")
            print("   docker compose restart openwebui")
        else:
            print("\n❌ Failed to apply configuration")
    else:
        print("⏹️  Configuration cancelled")

if __name__ == "__main__":
    import time
    
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "helpful":
            update_persona_config(style="helpful")
        elif sys.argv[1] == "casual":
            update_persona_config(style="casual")
        elif sys.argv[1] == "professional":
            update_persona_config(style="professional")
        elif sys.argv[1] == "creative":
            update_persona_config(style="creative")
        else:
            print("Usage: python configure_persona.py [helpful|casual|professional|creative]")
    else:
        # Interactive mode
        interactive_config()
