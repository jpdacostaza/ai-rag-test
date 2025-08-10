#!/usr/bin/env python3
"""
Post-Cleanup Verification Script
Checks for duplicates, verifies code integrity, and validates file locations
"""

import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Set

class PostCleanupVerification:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.duplicates = {}
        self.broken_imports = []
        self.endpoint_files = []
        self.verified_files = []
        self.errors = []
        
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.errors.append(f"Failed to hash {file_path}: {str(e)}")
            return ""
    
    def find_duplicates(self) -> Dict[str, List[Path]]:
        """Find duplicate files across the entire project"""
        print("Scanning for duplicate files...")
        file_hashes = {}
        
        # Scan all Python files
        for py_file in self.root_path.rglob("*.py"):
            if '.git' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            file_hash = self.calculate_file_hash(py_file)
            if file_hash:
                if file_hash not in file_hashes:
                    file_hashes[file_hash] = []
                file_hashes[file_hash].append(py_file)
        
        # Find actual duplicates
        duplicates = {h: files for h, files in file_hashes.items() if len(files) > 1}
        
        for file_hash, files in duplicates.items():
            print(f"Duplicate files found (hash: {file_hash[:8]}):")
            for file in files:
                print(f"  - {file.relative_to(self.root_path)}")
        
        return duplicates
    
    def check_import_integrity(self) -> List[str]:
        """Check for broken imports in moved files"""
        print("Checking import integrity...")
        broken_imports = []
        
        # Check files in tests directory
        test_dirs = ['tests', 'tests/debug', 'tests/memory', 'tests/verification']
        
        for test_dir in test_dirs:
            test_path = self.root_path / test_dir
            if test_path.exists():
                for py_file in test_path.glob("*.py"):
                    broken = self.analyze_imports(py_file)
                    if broken:
                        broken_imports.extend(broken)
        
        return broken_imports
    
    def analyze_imports(self, file_path: Path) -> List[str]:
        """Analyze imports in a specific file"""
        broken = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line.startswith(('import ', 'from ')) and not line.startswith('#'):
                    # Check for relative imports that might be broken
                    if ('core.' in line or 'services.' in line or 'config.' in line or 
                        'memory.' in line or 'utilities.' in line):
                        # These might need adjustment since files moved
                        broken.append(f"{file_path.relative_to(self.root_path)}:{i} - {line}")
                        
        except Exception as e:
            self.errors.append(f"Failed to analyze imports in {file_path}: {str(e)}")
            
        return broken
    
    def find_endpoints(self) -> List[Tuple[Path, List[str]]]:
        """Find API endpoints in moved files"""
        print("Scanning for API endpoints...")
        endpoint_files = []
        
        endpoint_patterns = [
            '@app.route',
            '@router.get',
            '@router.post', 
            '@router.put',
            '@router.delete',
            'FastAPI(',
            'APIRouter(',
            'app.get(',
            'app.post(',
            'app.put(',
            'app.delete('
        ]
        
        for py_file in self.root_path.rglob("*.py"):
            if '.git' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                found_endpoints = []
                for pattern in endpoint_patterns:
                    if pattern in content:
                        found_endpoints.append(pattern)
                
                if found_endpoints:
                    endpoint_files.append((py_file, found_endpoints))
                    
            except Exception as e:
                self.errors.append(f"Failed to scan endpoints in {py_file}: {str(e)}")
        
        return endpoint_files
    
    def verify_critical_files(self) -> List[str]:
        """Verify critical files are in correct locations"""
        print("Verifying critical file locations...")
        issues = []
        
        critical_files = {
            'memory/functions/enhanced_memory_function_filter_v5_1_final.py': 'Main memory function',
            'core/main.py': 'Main application entry point',
            'docker-compose.yml': 'Docker orchestration',
            'requirements.txt': 'Python dependencies',
            'README.md': 'Project documentation'
        }
        
        for file_path, description in critical_files.items():
            full_path = self.root_path / file_path
            if not full_path.exists():
                issues.append(f"Missing critical file: {file_path} ({description})")
            else:
                print(f"✓ Found: {file_path}")
        
        return issues
    
    def generate_verification_report(self) -> str:
        """Generate comprehensive verification report"""
        print("Generating verification report...")
        
        # Run all checks
        duplicates = self.find_duplicates()
        broken_imports = self.check_import_integrity()
        endpoints = self.find_endpoints()
        critical_issues = self.verify_critical_files()
        
        # Generate report
        report = []
        report.append("# Post-Cleanup Verification Report")
        report.append(f"Generated: {os.path.basename(__file__)}")
        report.append("")
        
        # Summary
        report.append("## Summary")
        report.append(f"- Duplicate file groups found: {len(duplicates)}")
        report.append(f"- Potential import issues: {len(broken_imports)}")
        report.append(f"- Files with API endpoints: {len(endpoints)}")
        report.append(f"- Critical file issues: {len(critical_issues)}")
        report.append(f"- Errors encountered: {len(self.errors)}")
        report.append("")
        
        # Duplicates
        if duplicates:
            report.append("## 🔍 Duplicate Files Found")
            for file_hash, files in duplicates.items():
                report.append(f"### Hash: {file_hash[:12]}")
                for file in files:
                    report.append(f"- `{file.relative_to(self.root_path)}`")
                report.append("")
        else:
            report.append("## ✅ No Duplicate Files Found")
            report.append("")
        
        # Import issues
        if broken_imports:
            report.append("## ⚠️ Potential Import Issues")
            for issue in broken_imports:
                report.append(f"- {issue}")
            report.append("")
        else:
            report.append("## ✅ No Import Issues Detected")
            report.append("")
        
        # API endpoints
        if endpoints:
            report.append("## 🌐 API Endpoints Found")
            for file_path, patterns in endpoints:
                report.append(f"### {file_path.relative_to(self.root_path)}")
                for pattern in patterns:
                    report.append(f"- {pattern}")
                report.append("")
        
        # Critical files
        if critical_issues:
            report.append("## ❌ Critical File Issues")
            for issue in critical_issues:
                report.append(f"- {issue}")
            report.append("")
        else:
            report.append("## ✅ All Critical Files Present")
            report.append("")
        
        # Errors
        if self.errors:
            report.append("## ❌ Errors Encountered")
            for error in self.errors:
                report.append(f"- {error}")
            report.append("")
        
        # Directory structure
        report.append("## 📁 Current Directory Structure")
        report.append("```")
        for item in sorted(self.root_path.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                report.append(f"{item.name}/")
                # Show first level of subdirectories
                try:
                    for subitem in sorted(item.iterdir())[:5]:  # Limit to first 5
                        if subitem.is_dir():
                            report.append(f"  {subitem.name}/")
                        else:
                            report.append(f"  {subitem.name}")
                    sub_count = len(list(item.iterdir()))
                    if sub_count > 5:
                        report.append(f"  ... and {sub_count - 5} more items")
                except PermissionError:
                    report.append(f"  [Permission denied]")
                report.append("")
        report.append("```")
        
        return "\n".join(report)

def main():
    """Main execution"""
    verifier = PostCleanupVerification()
    
    print("🔍 Starting post-cleanup verification...")
    print("=" * 50)
    
    # Generate comprehensive report
    report = verifier.generate_verification_report()
    
    # Save report
    report_file = "POST_CLEANUP_VERIFICATION_REPORT.md"
    with open(report_file, "w", encoding='utf-8') as f:
        f.write(report)
    
    print("=" * 50)
    print(f"✅ Verification completed!")
    print(f"📄 Report saved to: {report_file}")
    
    # Show summary
    if verifier.errors:
        print(f"⚠️  {len(verifier.errors)} errors encountered")
    else:
        print("✅ No errors encountered")

if __name__ == "__main__":
    main()
