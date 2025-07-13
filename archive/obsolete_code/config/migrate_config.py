#!/usr/bin/env python3
"""
Configuration Migration Script
=============================

This script helps migrate from the old fragmented configuration system
to the new unified configuration system.

Usage:
    python migrate_config.py [--dry-run] [--backup]
    
    --dry-run: Show what would be changed without making changes
    --backup: Create backups of original files before modification
"""

import os
import re
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Tuple

class ConfigMigrator:
    """Handles migration from old config system to unified config."""
    
    def __init__(self, dry_run: bool = False, backup: bool = False):
        self.dry_run = dry_run
        self.backup = backup
        self.backend_root = Path(__file__).parent
        
        # Files that import from config modules
        self.files_to_migrate = [
            "main.py",
            "startup.py",
            "security.py",
            "database_manager.py",
            "routes/health.py",
            "routes/chat.py",
            "routes/models.py",
            "routes/debug.py",
            "services/llm_service.py"
        ]
        
        # Old config files to deprecate
        self.old_config_files = [
            "config_minimal.py",
            "core/config.py",
            "pipelines/config.py",
            "pipelines/pipeline_config.py"
        ]
    
    def migrate(self):
        """Execute the complete migration."""
        print("🔄 Starting configuration migration...")
        
        if self.backup:
            self._create_backups()
        
        self._migrate_import_statements()
        self._create_deprecation_notices()
        self._validate_migration()
        
        if self.dry_run:
            print("\\n✅ Dry run completed. No files were modified.")
        else:
            print("\\n✅ Configuration migration completed successfully!")
            print("\\n📋 Next steps:")
            print("1. Test application startup: python -c 'import main'")
            print("2. Review and remove old config files when confident")
            print("3. Update documentation to reference config_unified.py")
    
    def _create_backups(self):
        """Create backups of files before modification."""
        print("\\n📁 Creating backups...")
        backup_dir = self.backend_root / "config_migration_backup"
        backup_dir.mkdir(exist_ok=True)
        
        all_files = self.files_to_migrate + ["config.py"] + self.old_config_files
        
        for file_path in all_files:
            source = self.backend_root / file_path
            if source.exists():
                backup_path = backup_dir / file_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, backup_path)
                print(f"  📋 Backed up: {file_path}")
    
    def _migrate_import_statements(self):
        """Update import statements in Python files."""
        print("\\n🔄 Migrating import statements...")
        
        for file_path in self.files_to_migrate:
            full_path = self.backend_root / file_path
            if not full_path.exists():
                continue
            
            self._migrate_file_imports(full_path)
    
    def _migrate_file_imports(self, file_path: Path):
        """Migrate imports in a specific file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Migration patterns
            migrations = [
                # Simple config imports
                (r'from config.config import', 'from config.config_unified import'),
                (r'import config\\b', 'import config_unified as config'),
                
                # Specific imports that need to be updated
                (r'from config.config import (DEFAULT_MODEL|OLLAMA_BASE_URL|DEFAULT_SYSTEM_PROMPT)', 
                 r'from config.config_unified import \\1'),
                
                # Core config imports
                (r'from core\\.config import', 'from config.config_unified import'),
                
                # Pipeline config imports
                (r'from pipelines\\.config import', 'from config.config_unified import'),
                (r'from \\.\\./config import', 'from config.config_unified import'),
            ]
            
            # Apply migrations
            for pattern, replacement in migrations:
                content = re.sub(pattern, replacement, content)
            
            # Handle special cases for config object access
            content = re.sub(r'\\bconfig\\.(\\w+)', r'config_unified._config.\\1', content)
            
            if content != original_content:
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✅ Migrated: {file_path}")
                else:
                    print(f"  🔍 Would migrate: {file_path}")
            
        except Exception as e:
            print(f"  ❌ Error migrating {file_path}: {e}")
    
    def _create_deprecation_notices(self):
        """Add deprecation notices to old config files."""
        print("\\n📝 Adding deprecation notices...")
        
        deprecation_notice = '''"""
⚠️  DEPRECATED: This configuration file has been replaced by config_unified.py
==============================================================================

This file is kept for backward compatibility but should not be modified.
All new configuration should be done through config_unified.py.

Migration date: {migration_date}
Replacement: config_unified.py

To complete the migration:
1. Verify all imports have been updated to use config_unified
2. Test the application thoroughly
3. Remove this file when confident the migration is complete
"""

# Original configuration content follows:
# (kept for reference during migration period)

'''
        
        for config_file in self.old_config_files:
            file_path = self.backend_root / config_file
            if not file_path.exists():
                continue
            
            try:
                # Read original content
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                # Create deprecated version
                deprecated_content = deprecation_notice.format(
                    migration_date=__import__('datetime').datetime.now().isoformat()
                ) + original_content
                
                if not self.dry_run:
                    # Write deprecated version
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(deprecated_content)
                    print(f"  📝 Added deprecation notice: {config_file}")
                else:
                    print(f"  🔍 Would add deprecation notice: {config_file}")
                    
            except Exception as e:
                print(f"  ❌ Error updating {config_file}: {e}")
    
    def _validate_migration(self):
        """Validate that the migration was successful."""
        print("\\n🔍 Validating migration...")
        
        try:
            # Try importing the unified config
            import sys
            sys.path.insert(0, str(self.backend_root))
            
            if not self.dry_run:
                import config_unified
                config = config_unified.Config.get_instance()
                print("  ✅ config_unified.py imports successfully")
                print(f"  ✅ Configuration loaded: {len(config.to_dict())} sections")
            else:
                print("  🔍 Would validate config_unified.py import")
                
        except Exception as e:
            print(f"  ❌ Validation error: {e}")
    
    def _show_summary(self):
        """Show migration summary."""
        print("\\n📊 Migration Summary:")
        print(f"  Files to migrate: {len(self.files_to_migrate)}")
        print(f"  Old config files: {len(self.old_config_files)}")
        print(f"  Dry run mode: {self.dry_run}")
        print(f"  Backup enabled: {self.backup}")

def main():
    """Main migration script."""
    parser = argparse.ArgumentParser(description='Migrate to unified configuration system')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be changed without making changes')
    parser.add_argument('--backup', action='store_true',
                       help='Create backups of original files before modification')
    
    args = parser.parse_args()
    
    migrator = ConfigMigrator(dry_run=args.dry_run, backup=args.backup)
    migrator._show_summary()
    migrator.migrate()

if __name__ == "__main__":
    main()
