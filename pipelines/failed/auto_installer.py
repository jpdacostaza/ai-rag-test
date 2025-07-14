#!/usr/bin/env python3
"""
Auto-dependency installer for OpenWebUI Pipelines (Zero-Config Setup)
===================================================================

This script automatically installs missing dependencies required by custom pipelines.
It runs as part of the pipeline initialization to ensure zero-config deployment.

NOTE: This is NOT a pipeline module - it's a utility script.
"""

import subprocess
import sys
import os
from pathlib import Path

# Mark this as NOT a pipeline to prevent auto-loading
__SKIP_PIPELINE_LOADING__ = True

def auto_install_dependencies():
    """Install dependencies from requirements.txt if it exists"""
    try:
        # Check for requirements.txt in the pipelines directory
        requirements_file = Path("/app/pipelines/requirements.txt")
        
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

if __name__ == "__main__":
    print("[PIPELINE INSTALLER] Starting auto-dependency installation...")
    auto_install_dependencies()
    print("[PIPELINE INSTALLER] Auto-dependency installation complete")
