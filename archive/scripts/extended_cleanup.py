#!/usr/bin/env python3
"""
Extended Legacy Cleanup Script
This script performs additional cleanup of obsolete files and directories.
"""

import os
import shutil
from pathlib import Path
from typing import List

class ExtendedCleanup:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.archive_dir = self.root_dir / 'archive'
        self.archive_dir.mkdir(exist_ok=True)

    def archive_failed_pipelines(self):
        """Archive the failed pipelines directory"""
        failed_dir = self.root_dir / 'pipelines' / 'failed'
        if failed_dir.exists():
            archive_path = self.archive_dir / 'failed_pipelines'
            archive_path.mkdir(exist_ok=True)
            
            print("📦 Archiving failed pipeline attempts...")
            
            for item in failed_dir.iterdir():
                if item.name != '__pycache__':
                    dest_path = archive_path / item.name
                    if item.is_file():
                        shutil.copy2(item, dest_path)
                    else:
                        shutil.copytree(item, dest_path, dirs_exist_ok=True)
                    print(f"✅ Archived: {item.name}")
            
            # Remove the failed directory
            shutil.rmtree(failed_dir)
            print("🗑️  Removed pipelines/failed directory")

    def archive_duplicate_docker_files(self):
        """Archive duplicate/alternative docker files"""
        docker_files_to_archive = [
            'docker-compose-fixed.yml',
            'docker-compose-ordered.yml', 
            'docker-compose.dev.yml',
            'docker-compose.simplified.yml',
            'docker-compose.yml.tmp'
        ]
        
        archive_path = self.archive_dir / 'docker_alternatives'
        archive_path.mkdir(exist_ok=True)
        
        print("📦 Archiving alternative Docker files...")
        
        for file_name in docker_files_to_archive:
            file_path = self.root_dir / file_name
            if file_path.exists():
                dest_path = archive_path / file_name
                shutil.move(str(file_path), str(dest_path))
                print(f"✅ Archived: {file_name}")

    def archive_test_result_files(self):
        """Archive test result files and logs"""
        patterns = [
            '*.log',
            '*test*.json', 
            '*report*.json',
            '*validation*.json',
            '*baseline*.json'
        ]
        
        archive_path = self.archive_dir / 'test_results'
        archive_path.mkdir(exist_ok=True)
        
        print("📦 Archiving test result files...")
        
        for pattern in patterns:
            for file_path in self.root_dir.glob(pattern):
                if file_path.is_file() and not file_path.name.startswith('requirements'):
                    dest_path = archive_path / file_path.name
                    try:
                        shutil.move(str(file_path), str(dest_path))
                        print(f"✅ Archived: {file_path.name}")
                    except Exception as e:
                        print(f"⚠️  Could not move {file_path.name}: {e}")

    def archive_security_file(self):
        """Archive the standalone security.py file (moved to core)"""
        security_file = self.root_dir / 'security.py'
        if security_file.exists():
            archive_path = self.archive_dir / 'obsolete_code'
            archive_path.mkdir(exist_ok=True)
            
            dest_path = archive_path / 'security.py'
            shutil.move(str(security_file), str(dest_path))
            print("✅ Archived standalone security.py (now in core/)")

    def clean_pycache_directories(self):
        """Remove all __pycache__ directories"""
        print("🧹 Cleaning __pycache__ directories...")
        
        count = 0
        for pycache_dir in self.root_dir.rglob('__pycache__'):
            try:
                shutil.rmtree(pycache_dir)
                count += 1
            except Exception as e:
                print(f"⚠️  Could not remove {pycache_dir}: {e}")
        
        print(f"✅ Removed {count} __pycache__ directories")

    def archive_handover_directory(self):
        """Archive handover directory - it's documentation that can be preserved"""
        handover_dir = self.root_dir / 'handover'
        if handover_dir.exists():
            archive_path = self.archive_dir / 'handover_docs'
            
            print("📦 Archiving handover documentation...")
            shutil.copytree(handover_dir, archive_path, dirs_exist_ok=True)
            shutil.rmtree(handover_dir)
            print("✅ Archived handover directory")

    def identify_large_unused_files(self):
        """Identify large files that might be unused"""
        print("🔍 Checking for large files...")
        
        large_files = []
        for file_path in self.root_dir.rglob('*'):
            try:
                if file_path.is_file() and not self._should_skip_file(file_path):
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    if size_mb > 10:  # Files larger than 10MB
                        large_files.append((file_path, size_mb))
            except (OSError, PermissionError):
                # Skip files with access issues
                continue
        
        if large_files:
            print("📊 Large files found:")
            for file_path, size_mb in sorted(large_files, key=lambda x: x[1], reverse=True):
                rel_path = file_path.relative_to(self.root_dir)
                print(f"  📄 {rel_path} ({size_mb:.1f} MB)")
        else:
            print("✅ No unusually large files found")

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            '__pycache__', '.git', 'node_modules', 'venv', '.venv',
            'openwebui_data', 'storage', 'data', 'logs', 'archive'
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)

    def create_cleanup_summary(self):
        """Create a summary of cleanup operations"""
        summary_path = self.archive_dir / 'EXTENDED_CLEANUP_SUMMARY.md'
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("# Extended Cleanup Summary\n\n")
            f.write("## Operations Performed\n\n")
            f.write("### 1. Failed Pipelines\n")
            f.write("- Archived `pipelines/failed/` directory containing experimental pipeline code\n")
            f.write("- Removed failed attempts to avoid confusion\n\n")
            
            f.write("### 2. Docker Alternatives\n")
            f.write("- Archived alternative docker-compose files\n")
            f.write("- Kept main `docker-compose.yml` for production\n\n")
            
            f.write("### 3. Test Results\n")
            f.write("- Archived old test result files and logs\n")
            f.write("- Preserved test reports for historical reference\n\n")
            
            f.write("### 4. Obsolete Files\n")
            f.write("- Archived standalone files that were moved to appropriate directories\n\n")
            
            f.write("### 5. Cache Cleanup\n")
            f.write("- Removed all `__pycache__` directories\n\n")
            
            f.write("### 6. Documentation Archive\n")
            f.write("- Archived handover documentation for reference\n\n")
            
            f.write("## Result\n")
            f.write("- Cleaner project structure\n")
            f.write("- Reduced confusion from obsolete files\n")
            f.write("- All important files preserved in archive\n")
        
        print(f"📋 Extended cleanup summary created: {summary_path}")

    def run_extended_cleanup(self):
        """Run all extended cleanup operations"""
        print("🚀 Starting extended cleanup...")
        
        self.archive_failed_pipelines()
        self.archive_duplicate_docker_files() 
        self.archive_test_result_files()
        self.archive_security_file()
        self.clean_pycache_directories()
        self.archive_handover_directory()
        self.identify_large_unused_files()
        self.create_cleanup_summary()
        
        print("\n✅ Extended cleanup complete!")
        print(f"📂 All archived content is in: {self.archive_dir}")

if __name__ == "__main__":
    import sys
    
    root_directory = sys.argv[1] if len(sys.argv) > 1 else "."
    
    cleanup = ExtendedCleanup(root_directory)
    cleanup.run_extended_cleanup()
