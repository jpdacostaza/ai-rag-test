"""
Auto-installer for OpenWebUI Pipeline Dependencies
Optimized to prevent duplicate installations and reduce startup time
"""

import subprocess
import sys
from typing import List, Optional

# Global flag to prevent duplicate installations
_installer_executed = False

def check_package_installed(package_name: str) -> bool:
    """Check if a package is already installed"""
    try:
        import importlib
        # Handle special cases for package names
        if package_name.startswith('pydantic'):
            import_name = 'pydantic'
        elif 'langchain' in package_name:
            import_name = 'langchain'
        elif 'wikipedia' in package_name:
            import_name = 'wikipedia'
        elif 'requests' in package_name:
            import_name = 'requests'
        else:
            import_name = package_name.split('>=')[0].split('==')[0].split('<')[0]
        
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False

def fix_pydantic_compatibility():
    """Fix pydantic version conflicts for LangChain compatibility"""
    global _installer_executed
    
    if _installer_executed:
        print("[AUTO_INSTALLER] Pydantic compatibility already checked")
        return
        
    # Only update if pydantic is not compatible
    if check_package_installed('pydantic'):
        try:
            import pydantic
            # Check if version is compatible (2.7.0 <= version < 3.0.0)
            version = getattr(pydantic, '__version__', '0.0.0')
            major, minor = map(int, version.split('.')[:2])
            if major == 2 and minor >= 7:
                print("[AUTO_INSTALLER] Pydantic version is compatible, skipping update")
                return
        except Exception:
            pass  # Continue with update if version check fails
    
    try:
        print("[AUTO_INSTALLER] Updating pydantic for LangChain compatibility...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "pydantic>=2.7.0,<3.0.0", "--upgrade", "--quiet"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("[AUTO_INSTALLER] [OK] Pydantic compatibility updated")
        else:
            print(f"[AUTO_INSTALLER] [WARN]  Pydantic update failed: {result.stderr}")
    except Exception as e:
        print(f"[AUTO_INSTALLER] [FAIL] Error updating pydantic: {e}")

def auto_install_dependencies(requirements_file: Optional[str] = None):
    """Auto-install dependencies from requirements file (optimized to skip if already installed)"""
    global _installer_executed
    
    if _installer_executed:
        print("[AUTO_INSTALLER] Dependencies already processed, skipping duplicate installation")
        return
        
    try:
        if not requirements_file:
            requirements_file = "/op./storage/openwebui/pipelines/requirements.txt"
        
        # Check if requirements file exists
        import os
        if not os.path.exists(requirements_file):
            print(f"[AUTO_INSTALLER] Requirements file not found: {requirements_file}")
            _installer_executed = True
            return
        
        print("[AUTO_INSTALLER] Checking dependencies from requirements file...")
        
        # Read requirements and check what's actually missing
        with open(requirements_file, 'r') as f:
            lines = f.readlines()
        
        missing_packages = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                package_name = line.split('>=')[0].split('==')[0].split('<')[0]
                if not check_package_installed(package_name):
                    missing_packages.append(line)
        
        if not missing_packages:
            print("[AUTO_INSTALLER] [OK] All requirements already satisfied")
            _installer_executed = True
            return
        
        print(f"[AUTO_INSTALLER] Installing {len(missing_packages)} missing packages...")
        
        # Install only missing packages
        for package in missing_packages:
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", 
                    package, "--quiet", "--no-warn-script-location"
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"[AUTO_INSTALLER] [OK] Installed: {package}")
                else:
                    print(f"[AUTO_INSTALLER] [FAIL] Failed: {package}")
            except Exception as e:
                print(f"[AUTO_INSTALLER] [FAIL] Error installing {package}: {e}")
                
        _installer_executed = True
        print("[AUTO_INSTALLER] Dependency installation completed")
            
    except Exception as e:
        print(f"[AUTO_INSTALLER] [FAIL] Error processing dependencies: {e}")
        _installer_executed = True

def install_package(package: str) -> bool:
    """Install a single package with error handling (checks if already installed first)"""
    
    # Check if already installed
    if check_package_installed(package):
        print(f"[AUTO_INSTALLER] [OK] Already installed: {package}")
        return True
        
    try:
        print(f"[AUTO_INSTALLER] Installing: {package}")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package, "--quiet"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"[AUTO_INSTALLER] [OK] Successfully installed: {package}")
            return True
        else:
            print(f"[AUTO_INSTALLER] [FAIL] Failed to install {package}: {result.stderr}")
            return False
    except Exception as e:
        print(f"[AUTO_INSTALLER] [FAIL] Error installing {package}: {e}")
        return False
