#!/usr/bin/env python3
"""
Project Structure Reorganization Script
======================================

This script reorganizes the project structure to consolidate storage,
move test files, and update all references.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
import re

class ProjectReorganizer:
    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()
        self.changes_made = []
        
    def log_change(self, action: str, source: str, target: str = None):
        """Log changes made during reorganization."""
        if target:
            change = f"{action}: {source} -> {target}"
        else:
            change = f"{action}: {source}"
        self.changes_made.append(change)
        print(f"✅ {change}")

    def consolidate_storage(self):
        """Consolidate all storage to root/storage."""
        print("\n🔄 Phase 1: Consolidating Storage Directories")
        
        setup_storage = self.root / "setup" / "storage"
        root_storage = self.root / "storage"
        
        if setup_storage.exists():
            print(f"📁 Found duplicate storage in setup/: {setup_storage}")
            
            # Move contents from setup/storage to root/storage
            for item in setup_storage.iterdir():
                source = item
                target = root_storage / item.name
                
                if target.exists():
                    print(f"⚠️  Merging {item.name} (target exists)")
                    if item.is_dir():
                        # Merge directories
                        for subitem in item.rglob("*"):
                            if subitem.is_file():
                                rel_path = subitem.relative_to(item)
                                target_file = target / rel_path
                                target_file.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(subitem, target_file)
                    else:
                        # Replace file
                        shutil.copy2(source, target)
                else:
                    # Move entire directory/file
                    shutil.move(str(source), str(target))
                
                self.log_change("MOVE", str(source), str(target))
            
            # Remove setup/storage directory
            try:
                shutil.rmtree(setup_storage)
                self.log_change("REMOVE", str(setup_storage))
            except OSError as e:
                print(f"⚠️  Could not remove {setup_storage}: {e}")
                # Try to remove remaining files manually
                for item in setup_storage.rglob("*"):
                    if item.is_file():
                        try:
                            item.unlink()
                        except:
                            pass
                try:
                    setup_storage.rmdir()
                    self.log_change("REMOVE", str(setup_storage))
                except:
                    print(f"⚠️  Some files remain in {setup_storage}")

        # Remove backend/ folder if it's just storage
        backend_folder = self.root / "backend"
        if backend_folder.exists():
            backend_data = backend_folder / "data"
            if backend_data.exists() and len(list(backend_folder.iterdir())) == 1:
                # Move backend/data contents to storage/openwebui
                openwebui_storage = root_storage / "openwebui"
                openwebui_storage.mkdir(exist_ok=True)
                
                for item in backend_data.iterdir():
                    target = openwebui_storage / item.name
                    if item.is_dir():
                        shutil.copytree(item, target, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, target)
                    self.log_change("MOVE", str(item), str(target))
                
                # Remove backend folder
                shutil.rmtree(backend_folder)
                self.log_change("REMOVE", str(backend_folder))

    def move_test_files(self):
        """Move all test and debug files to tests/ directory."""
        print("\n🔄 Phase 2: Moving Test and Debug Files")
        
        tests_dir = self.root / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        # Find all tests/tests/test_*.py and tests/tests/debug_*.py files in root
        test_patterns = ["tests/tests/test_*.py", "tests/tests/debug_*.py", "tests/tests/validate_*.py", "tests/tests/fix_*.py"]
        
        for pattern in test_patterns:
            for file_path in self.root.glob(pattern):
                if file_path.parent == self.root:  # Only root level files
                    target = tests_dir / file_path.name
                    if not target.exists():
                        shutil.move(str(file_path), str(target))
                        self.log_change("MOVE", str(file_path), str(target))

    def organize_remaining_files(self):
        """Move remaining files to appropriate directories."""
        print("\n🔄 Phase 3: Organizing Remaining Files")
        
        # Define file organization rules
        moves = {
            # Documentation files
            "*.md": "docs/",
            # Configuration files
            "mypy.ini": "config/",
            "pyproject.toml": "config/",
            # Scripts
            "*.sh": "scripts/",
        }
        
        for pattern, target_dir in moves.items():
            target_path = self.root / target_dir
            target_path.mkdir(exist_ok=True)
            
            for file_path in self.root.glob(pattern):
                if file_path.parent == self.root:  # Only root level files
                    # Skip certain files that should stay in root
                    skip_files = ["README.md", "CHANGELOG.md", "docker-compose.yml"]
                    if file_path.name in skip_files:
                        continue
                        
                    target = target_path / file_path.name
                    if not target.exists():
                        shutil.move(str(file_path), str(target))
                        self.log_change("MOVE", str(file_path), str(target))

    def update_file_references(self):
        """Update all file references in code."""
        print("\n🔄 Phase 4: Updating File References")
        
        # Define replacement patterns
        replacements = [
            # Storage path updates
            (r'./storage/', './storage/'),
            (r'storage/', 'storage/'),
            # Backend folder references
            (r'/app/data/', '/app/data/'),
            (r'./storage/openwebui/', './storage/openwebui/'),
            # Test file references
            (r'test_[^/\s]+\.py', lambda m: f'tests/{m.group(0)}'),
            (r'debug_[^/\s]+\.py', lambda m: f'tests/{m.group(0)}'),
            (r'validate_[^/\s]+\.py', lambda m: f'tests/{m.group(0)}'),
            (r'fix_[^/\s]+\.py', lambda m: f'tests/{m.group(0)}'),
        ]
        
        # File types to update
        file_patterns = [
            "**/*.py", "**/*.yml", "**/*.yaml", "**/*.json", 
            "**/*.sh", "**/*.ps1", "**/*.md", "**/Dockerfile*"
        ]
        
        updated_files = []
        
        for pattern in file_patterns:
            for file_path in self.root.rglob(pattern):
                try:
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        # Skip storage directories and other non-code directories
                        skip_dirs = ['storage', '.git', '__pycache__', 'node_modules', '.cache']
                        if any(skip_dir in str(file_path) for skip_dir in skip_dirs):
                            continue
                            
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                        
                            original_content = content
                        
                            # Apply replacements
                            for pattern_regex, replacement in replacements:
                                if callable(replacement):
                                    content = re.sub(pattern_regex, replacement, content)
                                else:
                                    content = re.sub(pattern_regex, replacement, content)
                        
                            # Write back if changed
                            if content != original_content:
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(content)
                                updated_files.append(str(file_path))
                            
                        except (UnicodeDecodeError, PermissionError, OSError):
                            # Skip binary files or files we can't read
                            continue
                except (OSError, PermissionError):
                    # Skip files we can't access (long paths, permissions, etc.)
                    continue
        
        if updated_files:
            print(f"📝 Updated references in {len(updated_files)} files")
            for file_path in updated_files[:10]:  # Show first 10
                self.log_change("UPDATE", file_path)
            if len(updated_files) > 10:
                print(f"... and {len(updated_files) - 10} more files")

    def verify_memory_installer(self):
        """Verify memory installer functionality."""
        print("\n🔄 Phase 5: Verifying Memory Installer")
        
        # Check if memory installer is properly configured
        dockerfile_installer = self.root / "Dockerfile.function-installer"
        if dockerfile_installer.exists():
            with open(dockerfile_installer, 'r') as f:
                content = f.read()
            
            if 'auto_install_function.py' in content:
                print("✅ Memory installer dockerfile found")
                
                # Check if script exists
                installer_script = self.root / "scripts" / "auto_install_function.py"
                if installer_script.exists():
                    print("✅ Memory installer script found")
                else:
                    print("❌ Memory installer script not found")
            else:
                print("❌ Memory installer not configured in dockerfile")

    def run_reorganization(self):
        """Run the complete reorganization process."""
        print("🚀 Starting Project Reorganization")
        print(f"📂 Working directory: {self.root}")
        
        try:
            self.consolidate_storage()
            self.move_test_files()
            self.organize_remaining_files()
            self.update_file_references()
            self.verify_memory_installer()
            
            print(f"\n✅ Reorganization Complete!")
            print(f"📊 Total changes made: {len(self.changes_made)}")
            
            # Write summary
            summary_file = self.root / "REORGANIZATION_SUMMARY.md"
            with open(summary_file, 'w') as f:
                f.write("# Project Reorganization Summary\n\n")
                f.write(f"Date: {subprocess.check_output(['date'], shell=True, text=True).strip()}\n\n")
                f.write("## Changes Made:\n\n")
                for change in self.changes_made:
                    f.write(f"- {change}\n")
            
            print(f"📄 Summary written to: {summary_file}")
            
        except Exception as e:
            print(f"❌ Error during reorganization: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        root_path = sys.argv[1]
    else:
        root_path = os.getcwd()
    
    reorganizer = ProjectReorganizer(root_path)
    reorganizer.run_reorganization()
