#!/usr/bin/env python3
"""
Project Reorganization Script
This script moves files to appropriate directories and updates all imports/references.
"""

import os
import shutil
import re
from pathlib import Path
from typing import Dict, List, Tuple

class ProjectReorganizer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.moved_files = {}  # old_path -> new_path mapping
        
    def move_files_to_directories(self):
        """Move files to their appropriate directories"""
        
        # Files to move with their target directories
        file_moves = {
            # Config files
            'config/': [
                'config.py', 'config_minimal.py', 'config_unified.py', 
                'debug_config.py', 'migrate_config.py'
            ],
            
            # Core application files  
            'core/': [
                'startup.py', 'startup_original.py', 'startup_simplified.py',
                'main.py', 'error_handler.py', 'human_logging.py'
            ],
            
            # Services
            'services/': [
                'model_manager.py', 'storage_manager.py', 'database_manager.py',
                'adaptive_learning.py', 'user_profiles.py', 'feedback_router.py'
            ],
            
            # Utilities
            'utilities/': [
                'watchdog.py', 'web_search_tool.py', 'rag.py'
            ],
            
            # Scripts
            'scripts/': [
                'configure_memory.py', 'flush_databases.py', 'install_global_pipeline.py',
                'manage_pipelines.py', 'integrated_memory_startup.py',
                'enhanced_integration.py', 'enhanced_web_search_trigger.py',
                'fix_rag.py', 'fix_error_patterns.py', 'improved_installer.py',
                'startup_order_validator.py'
            ],
            
            # Tests
            'tests/': [
                'comprehensive_test.py', 'enhanced_comprehensive_test.py',
                'test_connection_factory_migration.py', 'test_error_handler_migration.py',
                'test_small_model_persona.py', 'test_watchdog_migration.py'
            ],
            
            # Setup/Deployment
            'setup/': [
                'deploy.ps1', 'deploy.sh', 'secure_deployment.sh', 'linux_setup.sh'
            ],
            
            # Models
            'models/': [
                'models.py'
            ]
        }
        
        for target_dir, files in file_moves.items():
            target_path = self.root_dir / target_dir
            target_path.mkdir(exist_ok=True)
            
            for file_name in files:
                source_path = self.root_dir / file_name
                dest_path = target_path / file_name
                
                if source_path.exists() and source_path.is_file():
                    try:
                        shutil.move(str(source_path), str(dest_path))
                        self.moved_files[file_name] = f"{target_dir}{file_name}"
                        print(f"✅ Moved {file_name} → {target_dir}")
                    except Exception as e:
                        print(f"❌ Failed to move {file_name}: {e}")
                else:
                    print(f"⚠️  File not found: {file_name}")
    
    def update_imports_in_file(self, file_path: Path):
        """Update imports in a single file based on moved files"""
        try:
            if not file_path.exists() or not file_path.is_file():
                return
        except OSError:
            # Skip files with path length issues on Windows
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Update imports based on moved files
            for old_name, new_path in self.moved_files.items():
                module_name = old_name.replace('.py', '')
                new_module = new_path.replace('.py', '').replace('/', '.')
                
                # Pattern for various import styles
                patterns = [
                    f"from {module_name} import",
                    f"import {module_name}",
                    f"from .{module_name} import",
                    f"import .{module_name}",
                ]
                
                replacements = [
                    f"from {new_module} import",
                    f"import {new_module}",
                    f"from {new_module} import",
                    f"import {new_module}",
                ]
                
                for pattern, replacement in zip(patterns, replacements):
                    content = re.sub(
                        re.escape(pattern),
                        replacement,
                        content
                    )
            
            # Additional specific import fixes
            content = self.fix_specific_imports(content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Updated imports in {file_path.relative_to(self.root_dir)}")
                
        except Exception as e:
            print(f"❌ Failed to update {file_path}: {e}")
    
    def fix_specific_imports(self, content: str) -> str:
        """Fix specific import patterns that need special handling"""
        
        # Common import fixes
        fixes = {
            'from core.error_handler import': 'from core.error_handler import',
            'from core.human_logging import': 'from core.human_logging import',
            'from services.database_manager import': 'from services.database_manager import',
            'from services.model_manager import': 'from services.model_manager import',
            'from services.storage_manager import': 'from services.storage_manager import',
            'from utilities.watchdog import': 'from utilities.watchdog import',
            'from utilities.web_search_tool import': 'from utilities.web_search_tool import',
            'from utilities.rag import': 'from utilities.rag import',
            'from config.config import': 'from config.config import',
            'from config.config_unified import': 'from config.config_unified import',
            'from core.startup import': 'from core.startup import',
            'from core.main import': 'from core.main import',
            'from models.models import': 'from models.models import',
        }
        
        for old_import, new_import in fixes.items():
            content = content.replace(old_import, new_import)
        
        return content
    
    def update_all_imports(self):
        """Update imports in all Python files"""
        python_files = list(self.root_dir.rglob("*.py"))
        
        for file_path in python_files:
            # Skip __pycache__, .git directories, and problematic paths
            if any(skip in str(file_path) for skip in ['__pycache__', '.git', 'openwebui', 'storage\\openwebui']):
                continue
                
            self.update_imports_in_file(file_path)
    
    def update_dockerfile_references(self):
        """Update Dockerfile references to moved files"""
        dockerfiles = [
            'Dockerfile', 'Dockerfile.backend', 'Dockerfile.gateway',
            'Dockerfile.memory', 'Dockerfile.function-installer',
            'Dockerfile.unified-installer'
        ]
        
        for dockerfile in dockerfiles:
            dockerfile_path = self.root_dir / dockerfile
            if dockerfile_path.exists():
                self.update_imports_in_file(dockerfile_path)
    
    def update_docker_compose_references(self):
        """Update docker-compose files"""
        compose_files = list(self.root_dir.glob("docker-compose*.yml"))
        
        for compose_file in compose_files:
            self.update_imports_in_file(compose_file)
    
    def clean_root_directory(self):
        """Clean up remaining files in root that should be moved"""
        # Move log files to logs directory
        logs_dir = self.root_dir / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        for log_file in self.root_dir.glob("*.log"):
            try:
                shutil.move(str(log_file), str(logs_dir / log_file.name))
                print(f"✅ Moved log file {log_file.name} → logs/")
            except Exception as e:
                print(f"❌ Failed to move log file {log_file.name}: {e}")
        
        # Move JSON test results to tests directory
        for json_file in self.root_dir.glob("*test*.json"):
            try:
                shutil.move(str(json_file), str(self.root_dir / 'tests' / json_file.name))
                print(f"✅ Moved test file {json_file.name} → tests/")
            except Exception as e:
                print(f"❌ Failed to move test file {json_file.name}: {e}")
    
    def reorganize(self):
        """Run the complete reorganization process"""
        print("🚀 Starting project reorganization...")
        
        print("\n📁 Moving files to appropriate directories...")
        self.move_files_to_directories()
        
        print("\n🔄 Updating imports in all files...")
        self.update_all_imports()
        
        print("\n🐳 Updating Docker references...")
        self.update_dockerfile_references()
        self.update_docker_compose_references()
        
        print("\n🧹 Cleaning up root directory...")
        self.clean_root_directory()
        
        print("\n✅ Project reorganization complete!")
        print(f"📊 Moved {len(self.moved_files)} files")
        
        # Display summary
        print("\n📋 Summary of moved files:")
        for old_name, new_path in self.moved_files.items():
            print(f"  {old_name} → {new_path}")

if __name__ == "__main__":
    import sys
    
    root_directory = sys.argv[1] if len(sys.argv) > 1 else "."
    
    reorganizer = ProjectReorganizer(root_directory)
    reorganizer.reorganize()
