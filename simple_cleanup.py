#!/usr/bin/env python3
"""
Simple Backend Project Cleanup and Validation Script
Performs focused cleanup and validation of the backend project.
"""

import os
import sys
import glob
import shutil
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def clean_python_cache():
    """Clean Python cache files safely."""
    logger.info("🧹 Cleaning Python cache files...")
    
    # Clean .pyc files only (safer than removing __pycache__ directories)
    pyc_files = glob.glob("**/*.pyc", recursive=True)
    removed_count = 0
    
    for pyc_file in pyc_files:
        try:
            if os.path.exists(pyc_file):
                os.remove(pyc_file)
                removed_count += 1
                logger.debug(f"Removed: {pyc_file}")
        except Exception as e:
            logger.warning(f"Could not remove {pyc_file}: {e}")
    
    logger.info(f"Removed {removed_count} .pyc files")
    return removed_count

def validate_python_syntax():
    """Validate Python files for syntax errors."""
    logger.info("🔍 Validating Python syntax...")
    
    python_files = glob.glob("*.py")  # Only root level files
    invalid_files = []
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                compile(content, py_file, 'exec')
            logger.debug(f"✅ {py_file}")
        except SyntaxError as e:
            logger.error(f"❌ Syntax error in {py_file}: {e}")
            invalid_files.append(py_file)
        except Exception as e:
            logger.warning(f"⚠️ Could not validate {py_file}: {e}")
    
    if invalid_files:
        logger.error(f"Found {len(invalid_files)} files with syntax errors!")
        return False
    else:
        logger.info(f"✅ All {len(python_files)} Python files are valid")
        return True

def check_configuration_consistency():
    """Check for OLLAMA_URL vs OLLAMA_BASE_URL consistency."""
    logger.info("🔍 Checking configuration consistency...")
    
    issues_found = []
    
    # Check specific known files
    files_to_check = {
        "docker-compose.yml": "Docker Compose configuration",
        ".env.example": "Environment variables example",
        "README.md": "Documentation"
    }
    
    for file_path, description in files_to_check.items():
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Check for old OLLAMA_URL usage
                if 'OLLAMA_URL=' in content and 'OLLAMA_BASE_URL=' not in content:
                    issues_found.append(f"{file_path} ({description}) uses OLLAMA_URL instead of OLLAMA_BASE_URL")
                    
            except Exception as e:
                logger.warning(f"Could not check {file_path}: {e}")
    
    if issues_found:
        logger.warning("Configuration inconsistencies found:")
        for issue in issues_found:
            logger.warning(f"  - {issue}")
        return False
    else:
        logger.info("✅ Configuration files are consistent")
        return True

def generate_project_summary():
    """Generate a summary of the project structure."""
    logger.info("📋 Generating project summary...")
    
    summary = {
        'python_files': len(glob.glob("*.py")),
        'shell_scripts': len(glob.glob("*.sh")),
        'config_files': len(glob.glob("*.yml")) + len(glob.glob("*.yaml")) + 
                       len(glob.glob("*.json")) + len(glob.glob("*.env*")),
        'documentation': len(glob.glob("*.md")) + len(glob.glob("readme/*.md")),
        'total_size_mb': 0
    }
    
    # Calculate total size of main files
    main_files = glob.glob("*.py") + glob.glob("*.sh") + glob.glob("*.yml") + glob.glob("*.md")
    total_size = sum(os.path.getsize(f) for f in main_files if os.path.exists(f))
    summary['total_size_mb'] = total_size / (1024 * 1024)
    
    logger.info(f"📊 Project summary:")
    logger.info(f"  - Python files: {summary['python_files']}")
    logger.info(f"  - Shell scripts: {summary['shell_scripts']}")
    logger.info(f"  - Config files: {summary['config_files']}")
    logger.info(f"  - Documentation files: {summary['documentation']}")
    logger.info(f"  - Main files size: {summary['total_size_mb']:.2f} MB")
    
    return summary

def check_requirements():
    """Basic check of requirements.txt."""
    logger.info("🔍 Checking requirements.txt...")
    
    if not os.path.exists("requirements.txt"):
        logger.warning("No requirements.txt found")
        return False
    
    try:
        with open("requirements.txt", 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        packages = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                package = line.split('>=')[0].split('==')[0].split('<')[0]
                packages.append(package)
        
        # Check for duplicates
        duplicates = []
        seen = set()
        for package in packages:
            if package in seen:
                duplicates.append(package)
            seen.add(package)
        
        if duplicates:
            logger.warning(f"Duplicate packages found: {duplicates}")
            return False
        else:
            logger.info(f"✅ requirements.txt looks good ({len(packages)} unique packages)")
            return True
            
    except Exception as e:
        logger.error(f"Error checking requirements.txt: {e}")
        return False

def main():
    """Main cleanup function."""
    logger.info("🚀 Starting Backend Project Cleanup and Validation")
    logger.info(f"Working directory: {os.getcwd()}")
    
    success = True
    
    # Step 1: Generate project summary
    summary = generate_project_summary()
    
    # Step 2: Clean Python cache
    clean_python_cache()
    
    # Step 3: Validate Python syntax
    if not validate_python_syntax():
        success = False
    
    # Step 4: Check configuration consistency
    if not check_configuration_consistency():
        success = False
    
    # Step 5: Check requirements
    if not check_requirements():
        success = False
    
    # Step 6: Final summary
    if success:
        logger.info("🎉 All checks passed! Project is clean and consistent.")
    else:
        logger.error("❌ Some issues were found that need attention.")
    
    logger.info("✅ Cleanup and validation completed")
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
