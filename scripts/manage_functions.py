#!/usr/bin/env python3
"""
Function Management Utility
===========================

Utility script for managing OpenWebUI functions in the centralized functions/ directory.

Usage:
    python manage_functions.py list                    # List all functions
    python manage_functions.py validate               # Validate all functions
    python manage_functions.py install [function]     # Install function(s)
    python manage_functions.py backup                 # Backup functions
    python manage_functions.py restore               # Restore from backup
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import argparse

FUNCTIONS_DIR = Path("functions")
BACKUP_DIR = Path("backups/functions")

def list_functions() -> Dict[str, List[str]]:
    """List all functions by type."""
    functions = {"filters": [], "tools": []}
    
    for func_type in ["filters", "tools"]:
        func_dir = FUNCTIONS_DIR / func_type
        if func_dir.exists():
            for file_path in func_dir.glob("*.py"):
                if not file_path.name.startswith("__"):
                    functions[func_type].append(file_path.name)
    
    return functions

def validate_function(file_path: Path) -> Dict[str, any]:
    """Validate a single function file."""
    result = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "metadata": {}
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required class
        if "class Filter:" in content:
            result["metadata"]["type"] = "filter"
        elif "class Tools:" in content:
            result["metadata"]["type"] = "tool"
        else:
            result["errors"].append("No Filter or Tools class found")
            return result
        
        # Check for basic structure
        if "def __init__(" not in content:
            result["warnings"].append("No __init__ method found")
        
        # Extract metadata if available
        lines = content.split('\n')
        for line in lines[:20]:  # Check first 20 lines for metadata
            if 'title:' in line.lower():
                result["metadata"]["title"] = line.split(':', 1)[1].strip()
            elif 'description:' in line.lower():
                result["metadata"]["description"] = line.split(':', 1)[1].strip()
            elif 'version:' in line.lower():
                result["metadata"]["version"] = line.split(':', 1)[1].strip()
        
        result["valid"] = len(result["errors"]) == 0
        
    except Exception as e:
        result["errors"].append(f"Error reading file: {e}")
    
    return result

def validate_all_functions():
    """Validate all functions and print results."""
    functions = list_functions()
    total_valid = 0
    total_invalid = 0
    
    print("🔍 Function Validation Report")
    print("=" * 50)
    
    for func_type, func_list in functions.items():
        if not func_list:
            continue
            
        print(f"\n📂 {func_type.title()}:")
        
        for func_name in func_list:
            func_path = FUNCTIONS_DIR / func_type / func_name
            result = validate_function(func_path)
            
            if result["valid"]:
                print(f"  ✅ {func_name}")
                total_valid += 1
                
                # Show metadata if available
                if result["metadata"]:
                    for key, value in result["metadata"].items():
                        if value:
                            print(f"     {key}: {value}")
            else:
                print(f"  ❌ {func_name}")
                total_invalid += 1
                
                for error in result["errors"]:
                    print(f"     ERROR: {error}")
                    
            if result["warnings"]:
                for warning in result["warnings"]:
                    print(f"     WARNING: {warning}")
    
    print(f"\n📊 Summary: {total_valid} valid, {total_invalid} invalid")
    return total_invalid == 0

def backup_functions():
    """Create a backup of all functions."""
    if not FUNCTIONS_DIR.exists():
        print("❌ Functions directory not found")
        return False
    
    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped backup
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"functions_backup_{timestamp}"
    
    try:
        shutil.copytree(FUNCTIONS_DIR, backup_path)
        print(f"✅ Functions backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def install_functions(function_names: Optional[List[str]] = None):
    """Trigger function installation via auto-installer."""
    print("🚀 Triggering function installation...")
    
    # Run the auto-installer
    try:
        import subprocess
        result = subprocess.run([
            "docker-compose", "up", "function-auto-installer"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Function installation completed")
            print(result.stdout)
        else:
            print("❌ Function installation failed")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error running installer: {e}")
        print("💡 Try running manually: docker-compose up function-auto-installer")

def main():
    parser = argparse.ArgumentParser(description="Function Management Utility")
    parser.add_argument("command", choices=["list", "validate", "install", "backup", "restore"],
                        help="Command to execute")
    parser.add_argument("functions", nargs="*", help="Specific functions to operate on")
    
    args = parser.parse_args()
    
    if args.command == "list":
        functions = list_functions()
        print("📋 Available Functions:")
        print("=" * 30)
        
        for func_type, func_list in functions.items():
            if func_list:
                print(f"\n{func_type.title()}:")
                for func in func_list:
                    print(f"  • {func}")
            else:
                print(f"\n{func_type.title()}: (none)")
                
        total = sum(len(func_list) for func_list in functions.values())
        print(f"\nTotal: {total} functions")
    
    elif args.command == "validate":
        if not validate_all_functions():
            sys.exit(1)
    
    elif args.command == "install":
        install_functions(args.functions if args.functions else None)
    
    elif args.command == "backup":
        if not backup_functions():
            sys.exit(1)
    
    elif args.command == "restore":
        print("❌ Restore functionality not yet implemented")
        print("💡 Manually copy from backups/functions/ to functions/")
        sys.exit(1)

if __name__ == "__main__":
    main()
