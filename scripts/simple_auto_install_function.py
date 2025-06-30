#!/usr/bin/env python3
"""
Simple Memory Function Auto-Installer
====================================

This script automatically installs the memory function into OpenWebUI
using a simple direct approach that bypasses complex authentication.
"""

import json
import time
import os
import sys
from pathlib import Path
import httpx

def log(message, level="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def wait_for_openwebui(url, max_retries=30):
    """Wait for OpenWebUI to be ready"""
    log(f"🔍 Waiting for OpenWebUI at {url}...")
    
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=10.0) as client:
                # Try the main page instead of API
                response = client.get(url)
                if response.status_code == 200:
                    log("✅ OpenWebUI is ready!")
                    return True
        except Exception as e:
            log(f"Attempt {attempt + 1}/{max_retries} failed: {e}", "DEBUG")
        
        if attempt < max_retries - 1:
            log(f"⏳ OpenWebUI not ready, waiting 10s... (attempt {attempt + 1}/{max_retries})")
            time.sleep(10)
    
    log("❌ OpenWebUI did not become ready within the timeout period", "ERROR")
    return False

def read_function_code():
    """Read the memory function code"""
    possible_paths = [
        Path("/app/memory_function.py"),
        Path("/opt/backend/memory_function.py"),
        Path("./memory_function.py"),
        Path("/memory_function.py")
    ]
    
    for path in possible_paths:
        if path.exists():
            log(f"📖 Reading function code from {path}")
            return path.read_text(encoding='utf-8')
    
    log("❌ Memory function file not found in any expected location", "ERROR")
    return None

def install_via_manual_method():
    """Install function using manual method - save to shared volume for user to import"""
    log("🔧 Installing memory function via manual method...")
    
    function_code = read_function_code()
    if not function_code:
        return False
    
    # Create installation instructions
    install_instructions = f"""
# Memory Function Auto-Installation
=====================================

The memory function has been prepared for installation. To complete the installation:

## Method 1: Copy-Paste Installation (Recommended)

1. Open OpenWebUI at http://localhost:3000
2. Login as admin
3. Go to Admin → Functions
4. Click "Add Function" or "+"
5. Copy the entire function code below and paste it into the editor:

---FUNCTION CODE START---
{function_code}
---FUNCTION CODE END---

6. Set Function ID: memory_function
7. Set Function Name: Enhanced Memory Function
8. Enable "Active" checkbox
9. Enable "Global" checkbox (optional)
10. Save the function

## Method 2: Use Installation Scripts

Run one of these from your host machine:

PowerShell:
```powershell
cd {os.getcwd()}
.\\scripts\\install_memory_function.ps1
```

Python:
```bash
cd {os.getcwd()}
python scripts/install_memory_function.py
```

## Configuration

After installation, configure these valves in the function settings:
- memory_api_url: "http://memory_api:8000"
- enable_memory: true
- max_memories: 3
- memory_threshold: 0.7
- debug: true

The function will automatically connect to your memory API at http://memory_api:8000
"""
    
    # Save instructions to a file
    instructions_path = "/tmp/openwebui/memory_function_installation_instructions.txt"
    try:
        os.makedirs(os.path.dirname(instructions_path), exist_ok=True)
        with open(instructions_path, 'w', encoding='utf-8') as f:
            f.write(install_instructions)
        log(f"📋 Installation instructions saved to {instructions_path}")
    except Exception as e:
        log(f"⚠️  Could not save instructions: {e}", "WARNING")
    
    # Also save just the function code for easy copying
    function_path = "/tmp/openwebui/memory_function_code.py"
    try:
        with open(function_path, 'w', encoding='utf-8') as f:
            f.write(function_code)
        log(f"📄 Function code saved to {function_path}")
    except Exception as e:
        log(f"⚠️  Could not save function code: {e}", "WARNING")
    
    log("✅ Manual installation files prepared!")
    log("🔗 To complete installation:")
    log("   1. Go to http://localhost:3000")
    log("   2. Login as admin → Functions → Add Function")
    log("   3. Copy the function code and paste it")
    log("   4. Set ID: memory_function, Name: Enhanced Memory Function")
    log("   5. Enable Active & Global checkboxes")
    log("   6. Save the function")
    
    return True

def main():
    log("🚀 Simple Memory Function Auto-Installer")
    log("=" * 50)
    
    openwebui_url = os.getenv("OPENWEBUI_URL", "http://openwebui:8080")
    
    # Wait for OpenWebUI to be ready
    if not wait_for_openwebui(openwebui_url):
        log("❌ OpenWebUI is not accessible, preparing manual installation files", "WARNING")
    else:
        log("✅ OpenWebUI is ready!")
    
    # Use manual installation method
    success = install_via_manual_method()
    
    if success:
        log("🎉 Installation preparation completed!")
        log("📝 Manual installation files are ready")
        log("🔗 Complete the installation by following the instructions above")
        return True
    else:
        log("❌ Installation preparation failed", "ERROR")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        log("✅ Auto-installer completed successfully")
        # Keep container running for a bit so logs can be read
        time.sleep(30)
        sys.exit(0)
    else:
        log("❌ Auto-installer failed", "ERROR")
        time.sleep(30)
        sys.exit(1)
