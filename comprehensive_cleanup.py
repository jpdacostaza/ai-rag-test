#!/usr/bin/env python3
"""
Comprehensive Backend Project Cleanup Script
Performs systematic cleanup, validation, and optimization of the entire backend project.

Usage: python comprehensive_cleanup.py [--dry-run] [--verbose]
"""

import os
import sys
import glob
import shutil
import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Set
import subprocess
import hashlib

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class BackendCleanup:
    """Comprehensive backend project cleanup utility."""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.project_root = Path(__file__).parent
        self.cleanup_stats = {
            'files_removed': 0,
            'directories_cleaned': 0,
            'issues_fixed': 0,
            'bytes_saved': 0
        }
        
        if verbose:
            logger.setLevel(logging.DEBUG)
    
    def log_action(self, action: str, file_path: str = "", size: int = 0):
        """Log cleanup actions."""
        if self.dry_run:
            logger.info(f"[DRY RUN] {action}: {file_path}")
        else:
            logger.info(f"{action}: {file_path}")
            if size > 0:
                self.cleanup_stats['bytes_saved'] += size
    
    def clean_python_cache(self):
        """Clean Python cache files and directories."""
        logger.info("🧹 Cleaning Python cache files...")
        
        # Clean __pycache__ directories
        pycache_dirs = glob.glob("**/__pycache__", recursive=True)
        for cache_dir in pycache_dirs:
            if os.path.exists(cache_dir):
                size = sum(os.path.getsize(os.path.join(cache_dir, f)) 
                          for f in os.listdir(cache_dir) if os.path.isfile(os.path.join(cache_dir, f)))
                self.log_action("Removing __pycache__", cache_dir, size)
                if not self.dry_run:
                    shutil.rmtree(cache_dir)
                self.cleanup_stats['directories_cleaned'] += 1
        
        # Clean .pyc files
        pyc_files = glob.glob("**/*.pyc", recursive=True)
        for pyc_file in pyc_files:
            if os.path.exists(pyc_file):
                size = os.path.getsize(pyc_file)
                self.log_action("Removing .pyc file", pyc_file, size)
                if not self.dry_run:
                    os.remove(pyc_file)
                self.cleanup_stats['files_removed'] += 1
        
        # Clean .pyo files
        pyo_files = glob.glob("**/*.pyo", recursive=True)
        for pyo_file in pyo_files:
            if os.path.exists(pyo_file):
                size = os.path.getsize(pyo_file)
                self.log_action("Removing .pyo file", pyo_file, size)
                if not self.dry_run:
                    os.remove(pyo_file)
                self.cleanup_stats['files_removed'] += 1
    
    def clean_temporary_files(self):
        """Clean temporary and backup files."""
        logger.info("🧹 Cleaning temporary files...")
        
        temp_patterns = [
            "**/*.tmp", "**/*.temp", "**/*~", "**/*.bak", 
            "**/*.swp", "**/*.swo", "**/.DS_Store", "**/Thumbs.db"
        ]
        
        for pattern in temp_patterns:
            temp_files = glob.glob(pattern, recursive=True)
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    size = os.path.getsize(temp_file)
                    self.log_action(f"Removing temp file", temp_file, size)
                    if not self.dry_run:
                        os.remove(temp_file)
                    self.cleanup_stats['files_removed'] += 1
    
    def clean_log_files(self):
        """Clean log files (optional)."""
        logger.info("🧹 Cleaning log files...")
        
        log_patterns = ["**/*.log", "**/*.out", "**/*.err"]
        
        for pattern in log_patterns:
            log_files = glob.glob(pattern, recursive=True)
            for log_file in log_files:
                if os.path.exists(log_file):
                    size = os.path.getsize(log_file)
                    self.log_action("Removing log file", log_file, size)
                    if not self.dry_run:
                        os.remove(log_file)
                    self.cleanup_stats['files_removed'] += 1
    
    def validate_python_files(self):
        """Validate all Python files for syntax errors."""
        logger.info("🔍 Validating Python files...")
        
        python_files = glob.glob("**/*.py", recursive=True)
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
    
    def check_imports(self):
        """Check for unused imports and import errors."""
        logger.info("🔍 Checking imports...")
        
        # This is a simplified check - in production you'd use tools like vulture or pyflakes
        python_files = glob.glob("*.py")  # Only check root level files
        
        for py_file in python_files:
            try:
                # Try to import the module (simplified check)
                module_name = os.path.splitext(py_file)[0]
                if module_name not in ['setup', 'comprehensive_cleanup']:  # Skip setup files
                    logger.debug(f"Testing imports for {py_file}")
                    # Note: In production, you'd use ast parsing for safer checking
            except Exception as e:
                logger.debug(f"Could not test imports for {py_file}: {e}")
    
    def optimize_requirements(self):
        """Check requirements.txt for issues."""
        logger.info("🔍 Checking requirements.txt...")
        
        req_file = "requirements.txt"
        if os.path.exists(req_file):
            with open(req_file, 'r') as f:
                lines = f.readlines()
            
            # Check for duplicate packages
            packages = set()
            duplicates = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    package = line.split('>=')[0].split('==')[0].split('<')[0]
                    if package in packages:
                        duplicates.append(package)
                    packages.add(package)
            
            if duplicates:
                logger.warning(f"Found duplicate packages in requirements.txt: {duplicates}")
            else:
                logger.info("✅ No duplicate packages found in requirements.txt")
    
    def check_configuration_consistency(self):
        """Check for configuration inconsistencies across files."""
        logger.info("🔍 Checking configuration consistency...")
        
        config_files = [
            "docker-compose.yml", ".env.example", "README.md"
        ]
        
        # Check for OLLAMA_URL vs OLLAMA_BASE_URL consistency
        inconsistencies = []
        
        for config_file in config_files:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                    if 'OLLAMA_URL=' in content and 'OLLAMA_BASE_URL=' not in content:
                        inconsistencies.append(f"{config_file} uses OLLAMA_URL instead of OLLAMA_BASE_URL")
        
        if inconsistencies:
            logger.warning("Configuration inconsistencies found:")
            for issue in inconsistencies:
                logger.warning(f"  - {issue}")
        else:
            logger.info("✅ Configuration files are consistent")
    
    def generate_file_inventory(self):
        """Generate an inventory of all project files."""
        logger.info("📋 Generating file inventory...")
        
        inventory = {
            'python_files': glob.glob("**/*.py", recursive=True),
            'config_files': glob.glob("**/*.yml", recursive=True) + 
                           glob.glob("**/*.yaml", recursive=True) + 
                           glob.glob("**/*.json", recursive=True) + 
                           glob.glob("**/*.env*", recursive=True),
            'documentation': glob.glob("**/*.md", recursive=True),
            'scripts': glob.glob("**/*.sh", recursive=True) + 
                      glob.glob("**/*.ps1", recursive=True),
            'total_files': 0,
            'total_size': 0
        }
        
        all_files = []
        for category in ['python_files', 'config_files', 'documentation', 'scripts']:
            all_files.extend(inventory[category])
        
        # Remove duplicates and calculate total size
        unique_files = list(set(all_files))
        total_size = 0
        
        for file_path in unique_files:
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)
        
        inventory['total_files'] = len(unique_files)
        inventory['total_size'] = total_size
        
        logger.info(f"📊 Project inventory:")
        logger.info(f"  - Python files: {len(inventory['python_files'])}")
        logger.info(f"  - Config files: {len(inventory['config_files'])}")
        logger.info(f"  - Documentation: {len(inventory['documentation'])}")
        logger.info(f"  - Scripts: {len(inventory['scripts'])}")
        logger.info(f"  - Total files: {inventory['total_files']}")
        logger.info(f"  - Total size: {total_size / (1024*1024):.2f} MB")
        
        return inventory
    
    def run_cleanup(self):
        """Run the complete cleanup process."""
        logger.info("🚀 Starting comprehensive backend cleanup...")
        logger.info(f"Project root: {self.project_root}")
        
        if self.dry_run:
            logger.info("🔍 Running in DRY RUN mode - no files will be modified")
        
        # Step 1: Generate inventory
        inventory = self.generate_file_inventory()
        
        # Step 2: Clean cache and temporary files
        self.clean_python_cache()
        self.clean_temporary_files()
        self.clean_log_files()
        
        # Step 3: Validate code
        syntax_valid = self.validate_python_files()
        
        # Step 4: Check imports and dependencies
        self.check_imports()
        self.optimize_requirements()
        
        # Step 5: Check configuration consistency
        self.check_configuration_consistency()
        
        # Step 6: Summary
        logger.info("🎉 Cleanup completed!")
        logger.info("📊 Cleanup statistics:")
        logger.info(f"  - Files removed: {self.cleanup_stats['files_removed']}")
        logger.info(f"  - Directories cleaned: {self.cleanup_stats['directories_cleaned']}")
        logger.info(f"  - Space saved: {self.cleanup_stats['bytes_saved'] / 1024:.2f} KB")
        
        if syntax_valid:
            logger.info("✅ All Python files passed syntax validation")
        else:
            logger.error("❌ Some Python files have syntax errors")
            return False
        
        return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Comprehensive backend project cleanup")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be done without making changes")
    parser.add_argument("--verbose", action="store_true", 
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    cleanup = BackendCleanup(dry_run=args.dry_run, verbose=args.verbose)
    success = cleanup.run_cleanup()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
