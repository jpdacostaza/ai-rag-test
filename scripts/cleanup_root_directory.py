#!/usr/bin/env python3
"""
Root Directory Cleanup Script
Organizes files from root directory into appropriate subdirectories
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Tuple

class RootDirectoryCleanup:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.moved_files = []
        self.duplicates_found = []
        self.errors = []
        
    def analyze_files(self) -> Dict[str, List[str]]:
        """Analyze files in root directory and categorize them"""
        categories = {
            'test_files': [],
            'debug_files': [],
            'memory_files': [],
            'config_files': [],
            'docs': [],
            'scripts': [],
            'verification_files': [],
            'temp_files': []
        }
        
        # Get all files in root (excluding directories)
        root_files = [f for f in self.root_path.iterdir() if f.is_file()]
        
        for file_path in root_files:
            filename = file_path.name
            
            # Skip essential files
            if filename in ['.gitignore', '.env', '.env.example', 'docker-compose.yml', 
                          'requirements.txt', 'README.md', 'Dockerfile', 'pyproject.toml']:
                continue
                
            # Categorize by name patterns
            if filename.startswith('test_'):
                categories['test_files'].append(filename)
            elif filename.startswith('debug_'):
                categories['debug_files'].append(filename)
            elif 'memory' in filename.lower():
                categories['memory_files'].append(filename)
            elif filename.startswith('verify_') or filename.startswith('validate_'):
                categories['verification_files'].append(filename)
            elif filename.endswith('.md') and filename.isupper():
                categories['docs'].append(filename)
            elif filename.endswith('.py') and any(word in filename.lower() for word in ['config', 'setup']):
                categories['config_files'].append(filename)
            elif filename.endswith('.py'):
                categories['scripts'].append(filename)
            elif filename.endswith('.json') and 'test' in filename:
                categories['test_files'].append(filename)
            else:
                categories['temp_files'].append(filename)
                
        return categories
    
    def check_duplicates(self, file_path: Path, target_dir: Path) -> bool:
        """Check if file already exists in target directory"""
        target_file = target_dir / file_path.name
        if target_file.exists():
            # Compare file sizes and modification times
            if (file_path.stat().st_size == target_file.stat().st_size and
                abs(file_path.stat().st_mtime - target_file.stat().st_mtime) < 1):
                return True
            else:
                self.duplicates_found.append(f"Different content: {file_path.name}")
                return False
        return False
    
    def move_file_safely(self, source: Path, target_dir: Path) -> bool:
        """Move file to target directory with safety checks"""
        try:
            # Ensure target directory exists
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Check for duplicates
            if self.check_duplicates(source, target_dir):
                print(f"Duplicate found, removing from root: {source.name}")
                source.unlink()
                return True
            
            # Move the file
            target_file = target_dir / source.name
            shutil.move(str(source), str(target_file))
            self.moved_files.append(f"{source.name} -> {target_dir.relative_to(self.root_path)}")
            print(f"Moved: {source.name} -> {target_dir.relative_to(self.root_path)}")
            return True
            
        except Exception as e:
            self.errors.append(f"Failed to move {source.name}: {str(e)}")
            print(f"Error moving {source.name}: {str(e)}")
            return False
    
    def execute_cleanup(self) -> Dict[str, any]:
        """Execute the cleanup process"""
        print("Starting root directory cleanup...")
        
        categories = self.analyze_files()
        
        # Define target directories for each category
        moves = [
            # Test files go to tests/
            (categories['test_files'], self.root_path / 'tests'),
            # Debug files go to tests/debug/
            (categories['debug_files'], self.root_path / 'tests' / 'debug'),
            # Memory files go to memory/functions/ or tests/memory/
            (categories['memory_files'], self.root_path / 'tests' / 'memory'),
            # Config verification files go to tests/config/
            (categories['verification_files'], self.root_path / 'tests' / 'verification'),
            # Documentation goes to docs/
            (categories['docs'], self.root_path / 'docs'),
            # Scripts go to scripts/
            (categories['scripts'], self.root_path / 'scripts'),
            # Config files go to config/
            (categories['config_files'], self.root_path / 'config'),
        ]
        
        for file_list, target_dir in moves:
            for filename in file_list:
                source_file = self.root_path / filename
                if source_file.exists():
                    self.move_file_safely(source_file, target_dir)
        
        # Handle temp files separately - analyze each one
        for filename in categories['temp_files']:
            source_file = self.root_path / filename
            if source_file.exists():
                print(f"Temp file found: {filename} - Manual review needed")
        
        return {
            'moved_files': self.moved_files,
            'duplicates_found': self.duplicates_found,
            'errors': self.errors,
            'categories': categories
        }
    
    def generate_report(self, results: Dict[str, any]) -> str:
        """Generate cleanup report"""
        report = []
        report.append("# Root Directory Cleanup Report")
        report.append(f"Generated: {os.path.basename(__file__)}")
        report.append("")
        
        report.append("## Summary")
        report.append(f"- Files moved: {len(results['moved_files'])}")
        report.append(f"- Duplicates handled: {len(results['duplicates_found'])}")
        report.append(f"- Errors encountered: {len(results['errors'])}")
        report.append("")
        
        if results['moved_files']:
            report.append("## Files Moved")
            for move in results['moved_files']:
                report.append(f"- {move}")
            report.append("")
        
        if results['duplicates_found']:
            report.append("## Duplicates Found")
            for duplicate in results['duplicates_found']:
                report.append(f"- {duplicate}")
            report.append("")
        
        if results['errors']:
            report.append("## Errors")
            for error in results['errors']:
                report.append(f"- {error}")
            report.append("")
        
        report.append("## Categories Analyzed")
        for category, files in results['categories'].items():
            if files:
                report.append(f"### {category.replace('_', ' ').title()}")
                for file in files:
                    report.append(f"- {file}")
                report.append("")
        
        return "\n".join(report)

def main():
    """Main execution function"""
    cleaner = RootDirectoryCleanup()
    
    # Execute cleanup
    results = cleaner.execute_cleanup()
    
    # Generate and save report
    report = cleaner.generate_report(results)
    
    with open("CLEANUP_REPORT.md", "w") as f:
        f.write(report)
    
    print("\nCleanup completed!")
    print(f"Report saved to: CLEANUP_REPORT.md")
    print(f"Files moved: {len(results['moved_files'])}")
    print(f"Duplicates handled: {len(results['duplicates_found'])}")
    print(f"Errors: {len(results['errors'])}")

if __name__ == "__main__":
    main()
