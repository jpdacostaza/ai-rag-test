"""
Auto-installer for OpenWebUI Pipeline Dependencies
Handles automatic dependency installation with version conflict resolution
"""

import subprocess
import sys
from typing import List, Optional

def fix_pydantic_compatibility():
    """Fix pydantic version conflicts for LangChain compatibility"""
    try:
        # Install compatible pydantic version
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "pydantic>=2.7.0,<3.0.0", "--upgrade"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("[AUTO_INSTALLER] Pydantic compatibility updated")
        else:
            print(f"[AUTO_INSTALLER] Warning: Pydantic update failed: {result.stderr}")
    except Exception as e:
        print(f"[AUTO_INSTALLER] Error updating pydantic: {e}")

def auto_install_dependencies(requirements_file: Optional[str] = None):
    """Auto-install dependencies from requirements file"""
    try:
        if not requirements_file:
            requirements_file = "/app/pipelines/requirements.txt"
        
        # Install from requirements file
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "-r", requirements_file, "--upgrade"
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("[AUTO_INSTALLER] Dependencies installed successfully")
        else:
            print(f"[AUTO_INSTALLER] Warning: Some dependencies failed: {result.stderr}")
            
    except Exception as e:
        print(f"[AUTO_INSTALLER] Error installing dependencies: {e}")

def install_package(package: str) -> bool:
    """Install a single package with error handling"""
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"[AUTO_INSTALLER] Successfully installed: {package}")
            return True
        else:
            print(f"[AUTO_INSTALLER] Failed to install {package}: {result.stderr}")
            return False
    except Exception as e:
        print(f"[AUTO_INSTALLER] Error installing {package}: {e}")
        return False
