#!/usr/bin/env python3
"""
Automated Cleanup Script
Removes obsolete files and organizes the project structure
"""
import os
import shutil
from pathlib import Path
import time

class ProjectCleaner:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.backup_dir = self.base_dir / f"CLEANUP_BACKUP_{time.strftime('%Y%m%d_%H%M%S')}"
        self.removed_files = []
        self.moved_files = []
        
    def log(self, message: str):
        print(f"[{time.strftime('%H:%M:%S')}] {message}")
    
    def safe_remove(self, file_path: Path, reason: str = ""):
        """Safely remove a file after backing it up"""
        if not file_path.exists():
            return
        
        try:
            # Create backup directory if it doesn't exist
            self.backup_dir.mkdir(exist_ok=True)
            
            # Create backup
            backup_path = self.backup_dir / file_path.name
            if backup_path.exists():
                backup_path = self.backup_dir / f"{file_path.stem}_{int(time.time())}{file_path.suffix}"
            
            shutil.copy2(file_path, backup_path)
            
            # Remove original
            file_path.unlink()
            
            self.removed_files.append({"file": str(file_path), "reason": reason, "backup": str(backup_path)})
            self.log(f"✅ Removed: {file_path.name} ({reason})")
            
        except Exception as e:
            self.log(f"❌ Failed to remove {file_path.name}: {e}")
    
    def clean_obsolete_files(self):
        """Remove clearly obsolete files"""
        self.log("🧹 Cleaning obsolete files...")
        
        obsolete_files = [
            # Old memory implementations
            ("memory_function.py", "Replaced by memory_function_working.py"),
            ("memory_api_main_fixed.py", "Replaced by enhanced_memory_api.py"),
            ("adaptive_learning.py", "Feature not in use"),
            
            # Old configuration files
            ("memory_filter_function.py", "Old filter implementation"),
            ("memory_function_guardian.py", "Old guardian implementation"),
            ("memory_function_robust.py", "Old robust implementation"),
            
            # Development/debug scripts that are no longer needed
            ("check_function_config.py", "Development script"),
            ("check_function_syntax.py", "Development script"),
            ("check_persona_config.py", "Development script"),
            ("configure_as_filter.py", "Development script"),
            ("configure_persona.py", "Development script"),
            ("debug_memory_system.py", "Debug script"),
            ("fix_function_config.py", "Development script"),
            ("fix_memory_relevance.py", "Development script"),
            ("fix_threshold.py", "Development script"),
            ("quick_debug_config.py", "Development script"),
            
            # Deployment scripts that are replaced
            ("deploy_bulletproof_function.py", "Old deployment script"),
            ("deploy_enhanced_persona.py", "Old deployment script"),
            ("deploy_filter_function.py", "Old deployment script"),
            ("deploy_minimal_function.py", "Old deployment script"),
            ("deploy_working_function.py", "Old deployment script"),
            
            # Unused utility scripts
            ("ensure_memory_active.py", "Utility script"),
            ("import_memory_function.py", "Utility script"),
            ("install_function_db.py", "Utility script"),
            ("memory_startup_hook.py", "Old startup script"),
            ("update_function_url.py", "Utility script"),
            
            # Test files that are obsolete
            ("test_complete_memory_system.py", "Replaced by comprehensive tests"),
            ("test_name_correction.py", "Feature-specific test"),
            
            # Other obsolete files
            ("clean_memory_system.py", "Old cleanup script"),
            ("final_verification.py", "Old verification script"),
            ("human_logging.py", "Unused feature"),
            ("web_search_tool.py", "Unused feature"),
            ("watchdog.py", "Unused feature"),
        ]
        
        for filename, reason in obsolete_files:
            file_path = self.base_dir / filename
            self.safe_remove(file_path, reason)
    
    def organize_directories(self):
        """Organize files into better directory structure"""
        self.log("📁 Organizing directory structure...")
        
        # Create organized directories
        dirs_to_create = [
            "archive/old_implementations",
            "archive/development_scripts", 
            "documentation/reports",
            "documentation/status",
        ]
        
        for dir_path in dirs_to_create:
            (self.base_dir / dir_path).mkdir(parents=True, exist_ok=True)
        
        # Move documentation files
        doc_patterns = [
            ("*_REPORT.md", "documentation/reports"),
            ("*_STATUS.md", "documentation/status"),
            ("*_COMPLETION_*.md", "documentation/reports"),
            ("EXPLICIT_MEMORY_*.md", "documentation/status"),
            ("PROJECT_STATE_*.md", "documentation/status"),
            ("SESSION_*.md", "documentation/reports"),
        ]
        
        for pattern, target_dir in doc_patterns:
            target_path = self.base_dir / target_dir
            for file_path in self.base_dir.glob(pattern):
                if file_path.is_file() and file_path.parent == self.base_dir:
                    try:
                        new_path = target_path / file_path.name
                        if not new_path.exists():
                            shutil.move(str(file_path), str(new_path))
                            self.moved_files.append({"from": str(file_path), "to": str(new_path)})
                            self.log(f"📦 Moved: {file_path.name} → {target_dir}/")
                    except Exception as e:
                        self.log(f"❌ Failed to move {file_path.name}: {e}")
    
    def clean_pycache(self):
        """Remove __pycache__ directories"""
        self.log("🗑️ Cleaning __pycache__ directories...")
        
        for pycache_dir in self.base_dir.rglob("__pycache__"):
            if pycache_dir.is_dir():
                try:
                    shutil.rmtree(pycache_dir)
                    self.log(f"✅ Removed: {pycache_dir}")
                except Exception as e:
                    self.log(f"❌ Failed to remove {pycache_dir}: {e}")
    
    def generate_cleanup_report(self):
        """Generate a report of all cleanup actions"""
        report_path = self.base_dir / "CLEANUP_REPORT.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Project Cleanup Report\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Summary\n")
            f.write(f"- **Files removed**: {len(self.removed_files)}\n")
            f.write(f"- **Files moved**: {len(self.moved_files)}\n")
            f.write(f"- **Backup location**: {self.backup_dir.name}\n\n")
            
            if self.removed_files:
                f.write("## Removed Files\n")
                for item in self.removed_files:
                    f.write(f"- **{Path(item['file']).name}**: {item['reason']}\n")
                    f.write(f"  - Backup: `{item['backup']}`\n")
                f.write("\n")
            
            if self.moved_files:
                f.write("## Moved Files\n")
                for item in self.moved_files:
                    f.write(f"- **{Path(item['from']).name}**: {item['from']} → {item['to']}\n")
                f.write("\n")
            
            f.write("## Next Steps\n")
            f.write("1. Review the removed files list\n")
            f.write("2. Test the system to ensure nothing is broken\n")
            f.write("3. If satisfied, you can delete the backup directory\n")
            f.write("4. Commit the cleaned up project structure\n")
        
        self.log(f"📄 Cleanup report saved to: {report_path.name}")
    
    def run_cleanup(self):
        """Run the complete cleanup process"""
        self.log("🚀 Starting Project Cleanup")
        self.log("=" * 50)
        
        self.clean_obsolete_files()
        self.organize_directories() 
        self.clean_pycache()
        self.generate_cleanup_report()
        
        self.log("=" * 50)
        self.log(f"✅ Cleanup completed!")
        self.log(f"📦 Backup created at: {self.backup_dir.name}")
        self.log(f"📊 Files removed: {len(self.removed_files)}")
        self.log(f"📊 Files moved: {len(self.moved_files)}")

def main():
    cleaner = ProjectCleaner()
    
    # Ask for confirmation
    print("🚨 This will remove obsolete files and reorganize the project structure.")
    print("📦 All removed files will be backed up first.")
    
    response = input("\nProceed with cleanup? (y/N): ").strip().lower()
    if response == 'y':
        cleaner.run_cleanup()
    else:
        print("❌ Cleanup cancelled.")

if __name__ == "__main__":
    main()
