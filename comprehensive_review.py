#!/usr/bin/env python3
"""
Comprehensive Code & Quality Review Tool
"""

import os
import ast
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Any

class CodeQualityReviewer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.endpoints = []
        self.files_analyzed = 0
        self.import_issues = []
        self.missing_files = []
        self.unused_files = []
        
    def find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        files = []
        skip_dirs = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', 'archive', 'CLEANUP_BACKUP_20250630_152654'}
        
        for root, dirs, filenames in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for filename in filenames:
                if filename.endswith('.py'):
                    files.append(Path(root) / filename)
        return files
    
    def analyze_imports(self, file_path: Path) -> List[str]:
        """Analyze imports in a Python file."""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                issues.append(f"SYNTAX ERROR: {e}")
                return issues
                
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        # Check for problematic imports
                        if any(x in module_name for x in ['memory.', 'scripts.', 'tests.', 'readme.']):
                            issues.append(f"BROKEN IMPORT: import {module_name}")
                            
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module
                        # Check for relative imports or problematic modules
                        if module_name in ['memory', 'scripts', 'tests', 'readme']:
                            issues.append(f"POTENTIAL BROKEN IMPORT: from {module_name} import ...")
                        elif module_name.startswith('.') and node.level > 1:
                            issues.append(f"COMPLEX RELATIVE IMPORT: from {module_name} import ...")
                            
        except Exception as e:
            issues.append(f"ERROR ANALYZING: {str(e)}")
        
        return issues
    
    def find_endpoints(self, file_path: Path) -> List[Dict[str, Any]]:
        """Find API endpoints in Python files."""
        endpoints = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Look for FastAPI route decorators
            route_patterns = [
                r'@\w+\.get\([\'"]([^\'"]+)[\'"]',
                r'@\w+\.post\([\'"]([^\'"]+)[\'"]',
                r'@\w+\.put\([\'"]([^\'"]+)[\'"]',
                r'@\w+\.delete\([\'"]([^\'"]+)[\'"]',
                r'@\w+\.patch\([\'"]([^\'"]+)[\'"]',
            ]
            
            for pattern in route_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    endpoints.append({
                        'file': str(file_path),
                        'endpoint': match,
                        'method': pattern.split('.')[1].split('(')[0].upper()
                    })
                    
        except Exception as e:
            pass
        
        return endpoints
    
    def check_file_references(self, file_path: Path) -> List[str]:
        """Check for references to missing files."""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Look for common file reference patterns
            patterns = [
                r'open\([\'"]([^\'"]+)[\'"]',
                r'Path\([\'"]([^\'"]+)[\'"]',
                r'[\'"]\.\/[^\'"]+\.py[\'"]',
                r'[\'"]config\/[^\'"]+[\'"]',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if match and not match.startswith(('http', 'https', '/dev/', '/proc/')):
                        # Check if file exists
                        ref_path = Path(match)
                        if not ref_path.is_absolute():
                            ref_path = file_path.parent / match
                            if not ref_path.exists():
                                ref_path = self.project_root / match
                        
                        if not ref_path.exists():
                            issues.append(f"MISSING FILE REFERENCE: {match}")
                            
        except Exception as e:
            pass
        
        return issues
    
    def run_comprehensive_review(self):
        """Run the complete code quality review."""
        print("🔍 Starting Comprehensive Code Quality Review...")
        
        python_files = self.find_python_files()
        print(f"📁 Found {len(python_files)} Python files to analyze")
        
        all_import_issues = []
        all_file_issues = []
        all_endpoints = []
        
        for file_path in python_files:
            self.files_analyzed += 1
            
            # Analyze imports
            import_issues = self.analyze_imports(file_path)
            if import_issues:
                all_import_issues.extend([(str(file_path), issue) for issue in import_issues])
            
            # Find endpoints
            endpoints = self.find_endpoints(file_path)
            all_endpoints.extend(endpoints)
            
            # Check file references
            file_issues = self.check_file_references(file_path)
            if file_issues:
                all_file_issues.extend([(str(file_path), issue) for issue in file_issues])
        
        # Generate report
        self.generate_report(all_import_issues, all_file_issues, all_endpoints)
    
    def generate_report(self, import_issues, file_issues, endpoints):
        """Generate comprehensive report."""
        report = []
        report.append("# Comprehensive Code Quality Review Report")
        report.append(f"**Date:** {os.popen('date').read().strip()}")
        report.append(f"**Files Analyzed:** {self.files_analyzed}")
        report.append("")
        
        # Import Issues
        report.append("## 🔴 Import Issues")
        if import_issues:
            report.append(f"**Total Issues:** {len(import_issues)}")
            report.append("")
            for file_path, issue in import_issues[:20]:  # Show first 20
                report.append(f"- **{os.path.basename(file_path)}**: {issue}")
        else:
            report.append("✅ No import issues found")
        report.append("")
        
        # File Reference Issues
        report.append("## 📁 Missing File References")
        if file_issues:
            report.append(f"**Total Issues:** {len(file_issues)}")
            report.append("")
            for file_path, issue in file_issues[:20]:  # Show first 20
                report.append(f"- **{os.path.basename(file_path)}**: {issue}")
        else:
            report.append("✅ No missing file references found")
        report.append("")
        
        # Endpoints Found
        report.append("## 🌐 API Endpoints Discovered")
        if endpoints:
            report.append(f"**Total Endpoints:** {len(endpoints)}")
            endpoint_summary = {}
            for ep in endpoints:
                method = ep['method']
                endpoint_summary[method] = endpoint_summary.get(method, 0) + 1
            
            report.append("")
            report.append("### By Method:")
            for method, count in sorted(endpoint_summary.items()):
                report.append(f"- **{method}**: {count} endpoints")
                
            report.append("")
            report.append("### Endpoint List:")
            for ep in endpoints:
                report.append(f"- **{ep['method']}** `{ep['endpoint']}` ({os.path.basename(ep['file'])})")
        else:
            report.append("⚠️ No API endpoints found")
        report.append("")
        
        # Summary
        total_issues = len(import_issues) + len(file_issues)
        report.append("## 📊 Summary")
        report.append(f"- **Total Issues Found:** {total_issues}")
        report.append(f"- **Import Issues:** {len(import_issues)}")
        report.append(f"- **File Reference Issues:** {len(file_issues)}")
        report.append(f"- **API Endpoints:** {len(endpoints)}")
        report.append(f"- **Files Analyzed:** {self.files_analyzed}")
        
        if total_issues == 0:
            report.append("\n✅ **No critical issues found! Code quality looks good.**")
        else:
            report.append(f"\n⚠️ **{total_issues} issues need attention.**")
        
        # Write report
        report_content = '\n'.join(report)
        with open('comprehensive_code_review_report.md', 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print("\n" + "="*60)
        print("📋 COMPREHENSIVE CODE REVIEW COMPLETE")
        print("="*60)
        print(report_content)
        print("\n📄 Full report saved to: comprehensive_code_review_report.md")

if __name__ == "__main__":
    reviewer = CodeQualityReviewer(".")
    reviewer.run_comprehensive_review()
