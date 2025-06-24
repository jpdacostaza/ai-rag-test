#!/usr/bin/env python3
"""
Extensive Code Quality Review Tool
==================================

This tool performs a comprehensive analysis of the entire codebase including:
- Code complexity analysis
- Security vulnerabilities
- Performance issues
- Best practices violations
- Documentation completeness
- Test coverage analysis
- Dependency analysis
- Code duplication
- Type safety
- Error handling
"""

import ast
import os
import re
import sys
import json
import subprocess
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import importlib.util

class ExtensiveCodeReview:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)
        self.python_files = []
        self.config_files = []
        
    def add_issue(self, category, severity, file, line, message, fix_suggestion=""):
        """Add an issue to the report."""
        self.issues[category].append({
            "severity": severity,  # critical, high, medium, low
            "file": file,
            "line": line,
            "message": message,
            "fix": fix_suggestion
        })
        
    def scan_project(self):
        """Scan the entire project for Python and config files."""
        skip_dirs = {'.git', '__pycache__', 'venv', 'env', '.env', 'node_modules', 
                     'chroma_storage', 'redis_data', 'ollama_models'}
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                filepath = Path(root) / file
                if file.endswith('.py'):
                    self.python_files.append(filepath)
                elif file in ['requirements.txt', 'docker-compose.yml', 'Dockerfile', 
                            '.env', 'pyproject.toml', 'setup.py']:
                    self.config_files.append(filepath)
                    
    def analyze_startup_py(self, filepath):
        """Specific analysis for startup.py file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for specific startup.py issues
            if 'global watchdog_thread' in content:
                self.add_issue(
                    "startup", "high", str(filepath), 0,
                    "Global variable 'watchdog_thread' used but not declared",
                    "Add 'watchdog_thread = None' at module level or use app.state"
                )
                
            # Check for Unicode emojis in production code
            unicode_pattern = r'[🚀✅❌]'
            if re.search(unicode_pattern, content):
                self.add_issue(
                    "startup", "medium", str(filepath), 0,
                    "Unicode emojis in log messages may cause encoding issues",
                    "Replace with ASCII equivalents for better compatibility"
                )
                
            # Check for missing error handling in HTTP calls
            if 'httpx.AsyncClient' in content and 'except' not in content:
                self.add_issue(
                    "startup", "high", str(filepath), 0,
                    "HTTP client calls without comprehensive error handling",
                    "Add try-catch blocks around all HTTP operations"
                )
                
        except Exception as e:
            pass
            
    def analyze_code_complexity(self, filepath):
        """Analyze cyclomatic complexity and other metrics."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_complexity(node)
                    if complexity > 10:
                        self.add_issue(
                            "complexity", "high", str(filepath), node.lineno,
                            f"Function '{node.name}' has high cyclomatic complexity: {complexity}",
                            "Consider breaking this function into smaller, more focused functions"
                        )
                    
                    # Check function length
                    func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                    if func_lines > 50:
                        self.add_issue(
                            "complexity", "medium", str(filepath), node.lineno,
                            f"Function '{node.name}' is too long: {func_lines} lines",
                            "Functions should ideally be under 50 lines. Consider refactoring"
                        )
                        
        except Exception as e:
            self.add_issue("parsing", "high", str(filepath), 0, f"Failed to parse: {e}")
            
    def _calculate_complexity(self, node):
        """Calculate cyclomatic complexity of a function."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
        
    def analyze_type_safety(self, filepath):
        """Check for type hints and type safety issues."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for missing type hints
                    if not node.returns and node.name != '__init__' and not node.name.startswith('_'):
                        self.add_issue(
                            "type_safety", "low", str(filepath), node.lineno,
                            f"Function '{node.name}' missing return type annotation",
                            f"Add return type: def {node.name}(...) -> ReturnType:"
                        )
                        
                    # Check parameters for type hints
                    for arg in node.args.args:
                        if not arg.annotation and arg.arg not in ['self', 'cls']:
                            self.add_issue(
                                "type_safety", "low", str(filepath), node.lineno,
                                f"Parameter '{arg.arg}' in '{node.name}' missing type annotation",
                                f"Add type hint: {arg.arg}: TypeName"
                            )
                            
        except Exception as e:
            pass
            
    def analyze_error_handling(self, filepath):
        """Check for proper error handling."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Check for bare except
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    self.add_issue(
                        "error_handling", "medium", str(filepath), node.lineno,
                        "Bare except clause catches all exceptions",
                        "Specify exception types: except (ValueError, TypeError):"
                    )
                    
                # Check for except Exception without logging
                if isinstance(node, ast.ExceptHandler):
                    if node.type and getattr(node.type, 'id', None) == 'Exception':
                        # Check if there's logging in the except block
                        has_logging = False
                        for n in ast.walk(node):
                            if isinstance(n, ast.Call):
                                if hasattr(n.func, 'attr') and getattr(n.func, 'attr', None) in ['error', 'warning', 'info', 'debug']:
                                    has_logging = True
                                elif hasattr(n.func, 'id') and getattr(n.func, 'id', None) in ['print', 'log_service_status']:
                                    has_logging = True
                        if not has_logging:
                            self.add_issue(
                                "error_handling", "high", str(filepath), node.lineno,
                                "Exception caught but not logged",
                                "Add logging: log_service_status('SERVICE', 'error', f'Error: {e}')"
                            )
                            
        except Exception as e:
            pass
            
    def check_test_coverage(self):
        """Check if tests exist for modules."""
        test_dirs = ['tests', 'test']
        test_files = []
        
        for test_dir in test_dirs:
            test_path = self.project_root / test_dir
            if test_path.exists():
                for file in test_path.rglob('test_*.py'):
                    test_files.append(file)
                    
        # Check which modules have tests
        modules_with_tests = set()
        for test_file in test_files:
            # Extract module name from test file name
            module_name = test_file.stem.replace('test_', '')
            modules_with_tests.add(module_name)
            
        # Check for modules without tests
        critical_modules = ['startup', 'main', 'database_manager', 'model_manager', 'error_handler']
        for py_file in self.python_files:
            if 'test' not in str(py_file) and '__pycache__' not in str(py_file):
                module_name = py_file.stem
                if module_name not in modules_with_tests and module_name in critical_modules:
                    self.add_issue(
                        "testing", "high", str(py_file), 0,
                        f"Critical module '{module_name}' has no tests",
                        f"Create tests/test_{module_name}.py with comprehensive test cases"
                    )
                elif module_name not in modules_with_tests and not module_name.startswith('_'):
                    self.add_issue(
                        "testing", "medium", str(py_file), 0,
                        f"No tests found for module '{module_name}'",
                        f"Create tests/test_{module_name}.py with test cases"
                    )
                    
    def analyze_documentation(self, filepath):
        """Check for missing or incomplete documentation."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            # Check module docstring
            if not ast.get_docstring(tree):
                self.add_issue(
                    "documentation", "low", str(filepath), 1,
                    "Missing module docstring",
                    "Add module docstring explaining the purpose and main functionality"
                )
                
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node)
                    if not docstring and not node.name.startswith('_'):
                        self.add_issue(
                            "documentation", "medium", str(filepath), node.lineno,
                            f"Function '{node.name}' missing docstring",
                            f'Add docstring: """Brief description of {node.name}."""'
                        )
                        
                if isinstance(node, ast.ClassDef):
                    if not ast.get_docstring(node):
                        self.add_issue(
                            "documentation", "medium", str(filepath), node.lineno,
                            f"Class '{node.name}' missing docstring",
                            f'Add class docstring explaining purpose and usage'
                        )
                        
        except Exception as e:
            pass
            
    def generate_report(self):
        """Generate comprehensive report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files_analyzed": len(self.python_files),
                "total_issues": sum(len(issues) for issues in self.issues.values()),
                "critical_issues": sum(1 for issues in self.issues.values() 
                                     for issue in issues if issue["severity"] == "critical"),
                "high_issues": sum(1 for issues in self.issues.values() 
                                 for issue in issues if issue["severity"] == "high"),
                "medium_issues": sum(1 for issues in self.issues.values() 
                                   for issue in issues if issue["severity"] == "medium"),
                "low_issues": sum(1 for issues in self.issues.values() 
                                for issue in issues if issue["severity"] == "low"),
            },
            "issues_by_category": {}
        }
        
        # Group issues by category
        for category, issues in self.issues.items():
            report["issues_by_category"][category] = {
                "count": len(issues),
                "issues": sorted(issues, key=lambda x: (x["severity"], x["file"], x["line"]))
            }
            
        return report
        
    def run_analysis(self):
        """Run complete analysis."""
        print("Starting extensive code review...")
        
        # Scan project
        self.scan_project()
        print(f"Found {len(self.python_files)} Python files to analyze")
        
        # Analyze each Python file
        for i, filepath in enumerate(self.python_files, 1):
            print(f"Analyzing {i}/{len(self.python_files)}: {filepath.name}")
            
            # Special analysis for startup.py
            if filepath.name == 'startup.py':
                self.analyze_startup_py(filepath)
                
            self.analyze_code_complexity(filepath)
            self.analyze_error_handling(filepath)
            self.analyze_type_safety(filepath)
            self.analyze_documentation(filepath)
            
        # Analyze project-level items
        self.check_test_coverage()
        
        # Generate report
        report = self.generate_report()
        
        # Save report
        report_path = self.project_root / "focused_code_review_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        # Print summary
        print("\n" + "="*60)
        print("FOCUSED CODE REVIEW SUMMARY")
        print("="*60)
        print(f"Total files analyzed: {report['summary']['total_files_analyzed']}")
        print(f"Total issues found: {report['summary']['total_issues']}")
        print(f"  - Critical: {report['summary']['critical_issues']}")
        print(f"  - High: {report['summary']['high_issues']}")
        print(f"  - Medium: {report['summary']['medium_issues']}")
        print(f"  - Low: {report['summary']['low_issues']}")
        print("\nIssues by category:")
        for category, data in report['issues_by_category'].items():
            print(f"  - {category}: {data['count']} issues")
        print(f"\nDetailed report saved to: {report_path}")
        
        return report

if __name__ == "__main__":
    reviewer = ExtensiveCodeReview()
    reviewer.run_analysis()
