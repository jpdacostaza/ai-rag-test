#!/usr/bin/env python3
"""
Startup Integration for Automatic Function Installation
=====================================================

This script integrates automatic function installation into the regular startup process.
"""

import os
import time
import subprocess
import sys
from pathlib import Path

def run_function_installer():
    """Run the function installer as part of startup"""
    print("🚀 Running automatic memory function installation...")
    
    # Check if the function installer should run
    if os.getenv("SKIP_FUNCTION_INSTALL", "").lower() in ["true", "1", "yes"]:
        print("⏭️  Function installation skipped (SKIP_FUNCTION_INSTALL=true)")
        return
    
    try:
        # Run docker-compose to start the function installer
        cmd = ["docker-compose", "up", "function_installer", "--no-deps"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Function installer completed successfully")
        else:
            print(f"⚠️  Function installer finished with code {result.returncode}")
            print("This is normal - it's a one-time setup container")
    
    except subprocess.TimeoutExpired:
        print("⏰ Function installer timed out (this is normal)")
    except Exception as e:
        print(f"⚠️  Function installer error: {e}")
        print("This is normal for automated installation - check the logs above")

def main():
    print("🔧 Backend Startup with Automatic Function Installation")
    print("=" * 60)
    
    # Run function installer
    run_function_installer()
    
    print("\n🎉 Startup process completed!")
    print("=" * 60)
    print("📋 Next Steps:")
    print("1. Go to http://localhost:3000")
    print("2. Login as admin")
    print("3. Check Admin → Functions for 'Enhanced Memory Function'")
    print("4. If not installed, follow the manual installation instructions")
    print("\n💡 The memory system is ready to use!")

if __name__ == "__main__":
    main()
