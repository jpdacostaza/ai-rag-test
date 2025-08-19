#!/usr/bin/env python3
"""
Copy unified_prompt.json to functions directory for filter access
"""
import json
import shutil
import os

def copy_unified_prompt():
    # Source path (config directory)
    source_path = "../../config/unified_prompt.json"
    
    # Destination path (accessible by OpenWebUI filters)
    dest_path = "../../functions/unified_prompt_cache.json"
    
    try:
        # Copy the file
        shutil.copy2(source_path, dest_path)
        print(f"✅ Successfully copied unified_prompt.json to {dest_path}")
        
        # Verify the copy
        with open(dest_path, 'r') as f:
            config = json.load(f)
            system_prompt = config.get("system_prompt", "")
            print(f"✅ Verified: {len(system_prompt)} characters in system_prompt")
            
    except Exception as e:
        print(f"❌ Error copying file: {e}")
        return False
    
    return True

if __name__ == "__main__":
    copy_unified_prompt()
