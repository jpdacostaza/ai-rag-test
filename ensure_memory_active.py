#!/usr/bin/env python3
"""
Persistent Memory Function Configuration
Makes the memory function always active and assigns it to all models automatically
"""

import sqlite3
import json
import time

def ensure_memory_function_active():
    """Ensure memory function is always active and assigned to models"""
    
    conn = sqlite3.connect('storage/openwebui/webui.db')
    cursor = conn.cursor()
    
    print("🔧 Ensuring Memory Function is Always Active...")
    
    # Update memory function to be always active and global
    cursor.execute("""
        UPDATE function 
        SET is_active = 1, 
            is_global = 1,
            type = 'filter'
        WHERE id = 'memory_function'
    """)
    
    # Check if we have any models in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='model'")
    model_table_exists = cursor.fetchone()
    
    if model_table_exists:
        cursor.execute("PRAGMA table_info(model)")
        model_columns = cursor.fetchall()
        print("Model table columns:", [col[1] for col in model_columns])
        
        # Get all models
        cursor.execute("SELECT id, name FROM model")
        models = cursor.fetchall()
        
        for model_id, model_name in models:
            print(f"📝 Configuring memory for model: {model_name}")
            
            # Update model to include memory function in filters
            cursor.execute("SELECT meta FROM model WHERE id = ?", (model_id,))
            model_meta = cursor.fetchone()
            
            if model_meta and model_meta[0]:
                meta = json.loads(model_meta[0])
            else:
                meta = {}
            
            # Ensure filters array exists and includes memory function
            if 'filters' not in meta:
                meta['filters'] = []
            
            if 'memory_function' not in meta['filters']:
                meta['filters'].append('memory_function')
                
                # Update the model
                cursor.execute("UPDATE model SET meta = ? WHERE id = ?", 
                             (json.dumps(meta), model_id))
                print(f"✅ Added memory function to {model_name}")
    
    conn.commit()
    conn.close()
    
    print("✅ Memory function configured to be always active!")

if __name__ == "__main__":
    ensure_memory_function_active()
