#!/usr/bin/env python3
"""
Auto-dependency installer for OpenWebUI Pipelines (Zero-Config Setup)
===================================================================

This script automatically installs missing dependencies required by custom pipelines.
It runs as part of the pipeline initialization to ensure zero-config deployment.

NOTE: This is NOT a pipeline module - it's a utility script.
Underscore prefix prevents pipeline auto-loading.
"""

import subprocess
import sys
import os
from pathlib import Path

def auto_install_dependencies():
    """Install dependencies from requirements.txt if it exists"""
    try:
        # Check for requirements.txt in the pipelines directory
        requirements_file = Path("/opt/backend/pipelines/requirements.txt")
        
        if requirements_file.exists():
            print("[PIPELINE INSTALLER] Found requirements.txt, installing dependencies...")
            
            # Install dependencies
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "-r", str(requirements_file), 
                "--quiet", "--no-warn-script-location"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("[PIPELINE INSTALLER] Dependencies installed successfully")
            else:
                print(f"[PIPELINE INSTALLER] Warning: Some dependencies failed to install: {result.stderr}")
        else:
            print("[PIPELINE INSTALLER] No requirements.txt found, skipping dependency installation")
            
    except Exception as e:
        print(f"[PIPELINE INSTALLER] Error during dependency installation: {e}")

def install_single_package(package_name):
    """Install a single package"""
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            package_name, "--quiet", "--no-warn-script-location"
        ])
        print(f"[PIPELINE INSTALLER] Installed: {package_name}")
        return True
    except Exception as e:
        print(f"[PIPELINE INSTALLER] Failed to install {package_name}: {e}")
        return False

def fix_pydantic_compatibility():
    """Fix pydantic version compatibility issues"""
    try:
        # Check current pydantic version and downgrade if needed
        import subprocess
        import sys
        
        # Install compatible version of pydantic first
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "pydantic>=2.7.0,<2.10.0", "--quiet", "--no-warn-script-location"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("[PIPELINE INSTALLER] Fixed pydantic compatibility")
            return True
        else:
            print(f"[PIPELINE INSTALLER] Could not fix pydantic compatibility: {result.stderr}")
            return False
    except Exception as e:
        print(f"[PIPELINE INSTALLER] Could not fix pydantic compatibility: {e}")
        return False

if __name__ == "__main__":
    print("[PIPELINE INSTALLER] Starting auto-dependency installation...")
    fix_pydantic_compatibility()
    auto_install_dependencies()
    print("[PIPELINE INSTALLER] Auto-dependency installation complete")
