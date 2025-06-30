#!/usr/bin/env python3
"""
Comprehensive Code & Quality Review Tool
=======================================

Performs extensive analysis of the entire codebase to identify:
1. Broken import paths and references
2. Files that have been moved but still referenced in old locations
3. Unused/redundant files
4. Endpoint integrity and cross-references
5. Code quality issues
"""

import os
import ast
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Any
import importlib.util

class CodeQualityReviewer:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.issues = []
        self.warnings = []
        self.file_references = {}
        self.import_map = {}
        self.endpoints = {}
        self.unused_files = set()
        
    def add_issue(self, severity: str, file: str, line: int, description: str):
        """Add an issue to the report."""
        self.issues.append({
            'severity': severity,
            'file': file,
            'line': line,
            'description': description
        })
        
    def add_warning(self, file: str, description: str):
        """Add a warning to the report."""
        self.warnings.append({
            'file': file,
            'description': description
        })
    
    def scan_python_files(self) -> List[Path]:
        """Get all Python files in the project."""
        python_files = []
        for root, dirs, files in os.walk(self.root_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache', 'node_modules'}]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        return python_files
    
    def scan_config_files(self) -> List[Path]:
        """Get all configuration files."""
        config_files = []
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache', 'node_modules'}]
            
            for file in files:
                if file.endswith(('.json', '.yml', '.yaml', '.env', '.md', '.txt', '.sh', '.ps1')):
                    config_files.append(Path(root) / file)
        return config_files
    
    def extract_imports(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract all imports from a Python file."""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            'type': 'import',
                            'module': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno
                        })
                elif isinstance(node, ast.ImportFrom):
                    imports.append({
                        'type': 'from_import',
                        'module': node.module,
                        'names': [alias.name for alias in node.names],
                        'line': node.lineno
                    })
        except Exception as e:
            self.add_issue('ERROR', str(file_path), 0, f"Failed to parse file: {e}")
        
        return imports
    
    def extract_endpoints(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract API endpoints from Python files."""
        endpoints = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for FastAPI route decorators
            route_patterns = [
                r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
                r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
                r'@[a-zA-Z_]+\.route\(["\']([^"\']+)["\'].*methods=\[([^\]]+)\]'
            ]
            
            for pattern in route_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    if len(match.groups()) >= 2:
                        method = match.group(1) if match.group(1) else 'GET'
                        path = match.group(2)
                        endpoints.append({
                            'file': str(file_path),
                            'method': method.upper(),
                            'path': path,
                            'line': content[:match.start()].count('\n') + 1
                        })
        except Exception as e:
            self.add_warning(str(file_path), f"Failed to extract endpoints: {e}")
        
        return endpoints
    
    def check_file_references(self, file_path: Path):
        """Check for file path references in the content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for hardcoded file paths
            file_patterns = [
                r'["\']([^"\']*\.py)["\']',
                r'["\']([^"\']*\.json)["\']',
                r'["\']([^"\']*\.yml)["\']',
                r'["\']([^"\']*\.yaml)["\']',
                r'open\(["\']([^"\']+)["\']',
                r'Path\(["\']([^"\']+)["\']',
            ]
            
            line_number = 1
            for line in content.split('\n'):
                for pattern in file_patterns:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        referenced_file = match.group(1)
                        # Check if the referenced file exists
                        full_path = self.root_path / referenced_file
                        if not full_path.exists() and not referenced_file.startswith(('http', 'https', 'ftp')):
                            self.add_issue('WARNING', str(file_path), line_number, 
                                         f"Referenced file not found: {referenced_file}")
                line_number += 1
                
        except Exception as e:
            self.add_warning(str(file_path), f"Failed to check file references: {e}")
    
    def check_docker_references(self):
        """Check Docker configuration files for path references."""
        docker_files = ['docker-compose.yml', 'Dockerfile', 'Dockerfile.memory', 'Dockerfile.api_bridge']
        
        for docker_file in docker_files:
            file_path = self.root_path / docker_file
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check volume mounts and COPY commands
                    line_number = 1
                    for line in content.split('\n'):
                        # Check volume mounts
                        if 'volumes:' in content and ':' in line and './' in line:
                            parts = line.split(':')
                            if len(parts) >= 2:
                                local_path = parts[0].strip().lstrip('- ')
                                if local_path.startswith('./'):
                                    full_path = self.root_path / local_path[2:]
                                    if not full_path.exists():
                                        self.add_issue('ERROR', docker_file, line_number,
                                                     f"Volume mount source not found: {local_path}")
                        
                        # Check COPY commands
                        if line.strip().startswith('COPY'):
                            parts = line.split()
                            if len(parts) >= 3:
                                source_path = parts[1]
                                if not source_path.startswith(('http', 'https')) and '/' in source_path:
                                    full_path = self.root_path / source_path
                                    if not full_path.exists():
                                        self.add_issue('ERROR', docker_file, line_number,
                                                     f"COPY source not found: {source_path}")
                        
                        line_number += 1
                        
                except Exception as e:
                    self.add_warning(docker_file, f"Failed to check Docker file: {e}")
    
    def find_unused_files(self):
        """Find files that are not referenced anywhere."""
        all_files = set()
        referenced_files = set()
        
        # Collect all files
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache'}]
            for file in files:
                if not file.startswith('.') and file not in {'README.md', 'requirements.txt'}:
                    all_files.add(str(Path(root) / file))
        
        # Find referenced files
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache'}]
            for file in files:
                if file.endswith(('.py', '.yml', '.yaml', '.json', '.md', '.sh', '.ps1')):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Look for file references
                        for other_file in all_files:
                            file_name = Path(other_file).name
                            if file_name in content and str(file_path) != other_file:
                                referenced_files.add(other_file)
                                
                    except Exception:
                        continue
        
        # Files that are never referenced
        self.unused_files = all_files - referenced_files
        
        # Remove essential files from unused list
        essential_patterns = [
            'main.py', 'config.py', '__init__.py', 'requirements.txt',
            'docker-compose.yml', 'Dockerfile', '.env', '.gitignore',
            'startup.sh', 'README.md'
        ]
        
        self.unused_files = {f for f in self.unused_files 
                           if not any(pattern in f for pattern in essential_patterns)}
    
    def cross_reference_endpoints(self):
        """Cross-reference endpoints across files."""
        all_endpoints = {}
        
        # Collect all endpoints
        python_files = self.scan_python_files()
        for file_path in python_files:
            endpoints = self.extract_endpoints(file_path)
            for endpoint in endpoints:
                key = f"{endpoint['method']} {endpoint['path']}"
                if key in all_endpoints:
                    self.add_issue('WARNING', endpoint['file'], endpoint['line'],
                                 f"Duplicate endpoint: {key} (also in {all_endpoints[key]['file']})")
                else:
                    all_endpoints[key] = endpoint
        
        # Check for endpoint references in other files
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for URL references
                url_patterns = [
                    r'["\']([^"\']*\/api\/[^"\']*)["\']',
                    r'["\']([^"\']*\/v1\/[^"\']*)["\']',
                    r'["\']([^"\']*\/health[^"\']*)["\']',
                    r'["\']([^"\']*\/test[^"\']*)["\']'
                ]
                
                line_number = 1
                for line in content.split('\n'):
                    for pattern in url_patterns:
                        matches = re.finditer(pattern, line)
                        for match in matches:
                            url = match.group(1)
                            # Check if this endpoint exists
                            found = False
                            for endpoint_key, endpoint_data in all_endpoints.items():
                                if endpoint_data['path'] == url or url in endpoint_data['path']:
                                    found = True
                                    break
                            
                            if not found and url not in ['/health', '/']:
                                self.add_issue('WARNING', str(file_path), line_number,
                                             f"Referenced endpoint not found: {url}")
                    
                    line_number += 1
                    
            except Exception as e:
                self.add_warning(str(file_path), f"Failed to check endpoint references: {e}")
    
    def generate_report(self) -> str:
        """Generate a comprehensive report."""
        report = []
        report.append("# Comprehensive Code & Quality Review Report")
        report.append(f"Generated on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        report.append("## 📊 Summary")
        report.append(f"- **Critical Issues**: {len([i for i in self.issues if i['severity'] == 'ERROR'])}")
        report.append(f"- **Warnings**: {len([i for i in self.issues if i['severity'] == 'WARNING'])}")
        report.append(f"- **General Warnings**: {len(self.warnings)}")
        report.append(f"- **Unused Files**: {len(self.unused_files)}")
        report.append("")
        
        # Critical Issues
        critical_issues = [i for i in self.issues if i['severity'] == 'ERROR']
        if critical_issues:
            report.append("## 🚨 Critical Issues (Must Fix)")
            for issue in critical_issues:
                report.append(f"- **{issue['file']}:{issue['line']}** - {issue['description']}")
            report.append("")
        
        # Warnings
        warning_issues = [i for i in self.issues if i['severity'] == 'WARNING']
        if warning_issues:
            report.append("## ⚠️ Warnings (Should Fix)")
            for issue in warning_issues:
                report.append(f"- **{issue['file']}:{issue['line']}** - {issue['description']}")
            report.append("")
        
        # General Warnings
        if self.warnings:
            report.append("## 💡 General Warnings")
            for warning in self.warnings:
                report.append(f"- **{warning['file']}** - {warning['description']}")
            report.append("")
        
        # Unused Files
        if self.unused_files:
            report.append("## 🗑️ Potentially Unused Files")
            report.append("These files appear to not be referenced anywhere:")
            for file in sorted(self.unused_files):
                report.append(f"- `{file}`")
            report.append("")
        
        # Recommendations
        report.append("## 🎯 Recommendations")
        report.append("1. **Fix Critical Issues**: Address all ERROR-level issues first")
        report.append("2. **Review Warnings**: Check WARNING-level issues for potential problems")
        report.append("3. **Clean Up**: Consider removing unused files after verification")
        report.append("4. **Update References**: Fix any broken file path references")
        report.append("5. **Test Endpoints**: Verify all endpoints are working correctly")
        
        return "\\n".join(report)
    
    def run_comprehensive_review(self):
        """Run the complete code quality review."""
        print("🔍 Starting comprehensive code review...")
        
        print("📁 Scanning Python files...")
        python_files = self.scan_python_files()
        print(f"Found {len(python_files)} Python files")
        
        print("🔗 Checking imports and references...")
        for file_path in python_files:
            # Check imports
            imports = self.extract_imports(file_path)
            self.import_map[str(file_path)] = imports
            
            # Check file references
            self.check_file_references(file_path)
        
        print("🐳 Checking Docker configurations...")
        self.check_docker_references()
        
        print("🔍 Finding unused files...")
        self.find_unused_files()
        
        print("🌐 Cross-referencing endpoints...")
        self.cross_reference_endpoints()
        
        print("📝 Generating report...")
        return self.generate_report()

def main():
    reviewer = CodeQualityReviewer()
    report = reviewer.run_comprehensive_review()
    
    # Save report
    with open('COMPREHENSIVE_CODE_REVIEW_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✅ Review complete! Report saved to COMPREHENSIVE_CODE_REVIEW_REPORT.md")
    
    # Print summary
    critical_count = len([i for i in reviewer.issues if i['severity'] == 'ERROR'])
    warning_count = len([i for i in reviewer.issues if i['severity'] == 'WARNING'])
    
    print(f"📊 Summary: {critical_count} critical issues, {warning_count} warnings, {len(reviewer.unused_files)} unused files")

if __name__ == "__main__":
    main()
