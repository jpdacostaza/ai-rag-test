#!/usr/bin/env python3
"""
Comprehensive Code Quality Review and Test Suite
Performs extensive analysis of the entire backend codebase
"""

import os
import sys
import ast
import importlib.util
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import subprocess
import requests

# Add backend to path
sys.path.insert(0, "/opt/backend")
sys.path.insert(0, ".")


class CodeQualityReviewer:
    """TODO: Add proper docstring for CodeQualityReviewer class."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.backend_path = Path(".")
        self.issues = []
        self.file_analysis = {}
        self.endpoint_tests = {}
        self.import_graph = {}
        self.duplicate_code = []

    def log_issue(self, category: str, severity: str, file_path: str, line: int, message: str):
        """Log a code quality issue"""
        self.issues.append(
            {
                "category": category,
                "severity": severity,
                "file": str(file_path),
                "line": line,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        )
        print(f"🔍 {severity.upper()} [{category}] {file_path}:{line} - {message}")

    def analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python file for quality issues"""
        analysis = {
            "file": str(file_path),
            "lines": 0,
            "functions": 0,
            "classes": 0,
            "imports": [],
            "endpoints": [],
            "issues": [],
            "complexity": 0,
        }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\\n")
                analysis["lines"] = len(lines)

                # Parse AST
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            analysis["functions"] += 1
                            # Check for endpoint decorators
                            for decorator in node.decorator_list:
                                if isinstance(decorator, ast.Call) and hasattr(decorator.func, "attr"):
                                    if decorator.func.attr in ["get", "post", "put", "delete", "patch"]:
                                        if decorator.args and isinstance(decorator.args[0], ast.Str):
                                            endpoint = decorator.args[0].s
                                        elif decorator.args and isinstance(decorator.args[0], ast.Constant):
                                            endpoint = decorator.args[0].value
                                        else:
                                            endpoint = "unknown"
                                        analysis["endpoints"].append(
                                            {
                                                "method": decorator.func.attr.upper(),
                                                "path": endpoint,
                                                "function": node.name,
                                                "line": node.lineno,
                                            }
                                        )
                        elif isinstance(node, ast.ClassDef):
                            analysis["classes"] += 1
                        elif isinstance(node, (ast.Import, ast.ImportFrom)):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    analysis["imports"].append(
                                        {"type": "import", "module": alias.name, "line": node.lineno}
                                    )
                            else:
                                analysis["imports"].append(
                                    {
                                        "type": "from",
                                        "module": node.module,
                                        "names": [alias.name for alias in node.names],
                                        "line": node.lineno,
                                    }
                                )

                except SyntaxError as e:
                    self.log_issue("syntax", "error", file_path, e.lineno or 0, f"Syntax error: {e}")
                    analysis["issues"].append("syntax_error")

                # Check for common issues
                self.check_common_issues(file_path, lines, analysis)

        except Exception as e:
            self.log_issue("file_access", "error", file_path, 0, f"Cannot read file: {e}")

        return analysis

    def check_common_issues(self, file_path: Path, lines: List[str], analysis: Dict):
        """Check for common code quality issues"""
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Long lines
            if len(line) > 120:
                self.log_issue("style", "warning", file_path, i, f"Line too long ({len(line)} chars)")

            # TODO comments
            if "TODO" in line or "FIXME" in line:
                self.log_issue("maintenance", "info", file_path, i, "TODO/FIXME comment found")

            # Hardcoded paths
            if any(path in line for path in ["/tmp/", "/home/", "C:\\\\", "/Users/"]):
                self.log_issue("portability", "warning", file_path, i, "Hardcoded path detected")

            # Print statements (should use logging)
            if line_stripped.startswith("print(") and "debug" not in file_path.name.lower():
                self.log_issue("logging", "info", file_path, i, "Print statement found (consider using logging)")

            # Bare except clauses
            if line_stripped.startswith("except:"):
                self.log_issue("error_handling", "warning", file_path, i, "Bare except clause")

    def check_imports(self, file_path: Path, imports: List[Dict]) -> List[str]:
        """Check if imports are valid and accessible"""
        broken_imports = []

        for imp in imports:
            try:
                if imp["type"] == "import":
                    # Try to import the module
                    spec = importlib.util.find_spec(imp["module"])
                    if spec is None:
                        broken_imports.append(f"Line {imp['line']}: Cannot import '{imp['module']}'")
                        self.log_issue("imports", "error", file_path, imp["line"], f"Cannot import '{imp['module']}'")
                elif imp["type"] == "from":
                    if imp["module"]:
                        spec = importlib.util.find_spec(imp["module"])
                        if spec is None:
                            broken_imports.append(f"Line {imp['line']}: Cannot import from '{imp['module']}'")
                            self.log_issue(
                                "imports", "error", file_path, imp["line"], f"Cannot import from '{imp['module']}'"
                            )
            except Exception as e:
                broken_imports.append(f"Line {imp['line']}: Import check failed: {e}")
                self.log_issue("imports", "warning", file_path, imp["line"], f"Import check failed: {e}")

        return broken_imports

    def test_endpoints(self, base_url: str = "http://localhost:9099") -> Dict[str, Any]:
        """Test all discovered endpoints"""
        results = {"tested": 0, "passed": 0, "failed": 0, "endpoints": []}

        # Collect all endpoints from analysis
        all_endpoints = []
        for file_analysis in self.file_analysis.values():
            all_endpoints.extend(file_analysis.get("endpoints", []))

        print(f"\\n🔍 Testing {len(all_endpoints)} discovered endpoints...")

        for endpoint in all_endpoints:
            results["tested"] += 1
            method = endpoint["method"]
            path = endpoint["path"]

            # Skip parameterized paths for now
            if "{" in path:
                results["endpoints"].append(
                    {"method": method, "path": path, "status": "skipped", "reason": "parameterized path"}
                )
                continue

            try:
                if method == "GET":
                    response = requests.get(f"{base_url}{path}", timeout=5)
                elif method == "POST":
                    response = requests.post(f"{base_url}{path}", json={}, timeout=5)
                else:
                    results["endpoints"].append(
                        {"method": method, "path": path, "status": "skipped", "reason": f"method {method} not tested"}
                    )
                    continue

                if response.status_code < 500:
                    results["passed"] += 1
                    status = "passed"
                else:
                    results["failed"] += 1
                    status = "failed"

                results["endpoints"].append(
                    {
                        "method": method,
                        "path": path,
                        "status": status,
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds(),
                    }
                )

            except Exception as e:
                results["failed"] += 1
                results["endpoints"].append({"method": method, "path": path, "status": "error", "error": str(e)})

        return results

    def scan_all_files(self) -> Dict[str, Any]:
        """Scan all Python files in the project"""
        print("🔍 Starting comprehensive codebase scan...")

        python_files = list(self.backend_path.rglob("*.py"))
        print(f"📁 Found {len(python_files)} Python files")

        for file_path in python_files:
            if "__pycache__" in str(file_path):
                continue

            print(f"📄 Analyzing {file_path}")
            analysis = self.analyze_python_file(file_path)
            self.file_analysis[str(file_path)] = analysis

            # Check imports
            broken_imports = self.check_imports(file_path, analysis["imports"])
            if broken_imports:
                analysis["broken_imports"] = broken_imports

        return self.file_analysis

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        total_files = len(self.file_analysis)
        total_lines = sum(f.get("lines", 0) for f in self.file_analysis.values())
        total_functions = sum(f.get("functions", 0) for f in self.file_analysis.values())
        total_classes = sum(f.get("classes", 0) for f in self.file_analysis.values())
        total_endpoints = sum(len(f.get("endpoints", [])) for f in self.file_analysis.values())

        # Group issues by severity
        issues_by_severity = {}
        for issue in self.issues:
            severity = issue["severity"]
            if severity not in issues_by_severity:
                issues_by_severity[severity] = []
            issues_by_severity[severity].append(issue)

        report = {
            "summary": {
                "total_files": total_files,
                "total_lines": total_lines,
                "total_functions": total_functions,
                "total_classes": total_classes,
                "total_endpoints": total_endpoints,
                "total_issues": len(self.issues),
                "scan_timestamp": datetime.now().isoformat(),
            },
            "issues_by_severity": {
                "error": len(issues_by_severity.get("error", [])),
                "warning": len(issues_by_severity.get("warning", [])),
                "info": len(issues_by_severity.get("info", [])),
            },
            "detailed_issues": self.issues,
            "file_analysis": self.file_analysis,
            "endpoint_tests": self.endpoint_tests,
        }

        return report


def main():
    """Main function to run comprehensive review"""
    print("🚀 Starting Comprehensive Code Quality Review")
    print("=" * 60)

    reviewer = CodeQualityReviewer()

    # Scan all files
    reviewer.scan_all_files()

    # Test endpoints if backend is running
    try:
        reviewer.endpoint_tests = reviewer.test_endpoints()
    except Exception as e:
        print(f"⚠️  Endpoint testing failed: {e}")
        reviewer.endpoint_tests = {"error": str(e)}

    # Generate report
    report = reviewer.generate_report()

    # Print summary
    print("\\n" + "=" * 60)
    print("📊 COMPREHENSIVE REVIEW SUMMARY")
    print("=" * 60)
    print(f"📁 Files analyzed: {report['summary']['total_files']}")
    print(f"📄 Lines of code: {report['summary']['total_lines']}")
    print(f"🔧 Functions: {report['summary']['total_functions']}")
    print(f"🏗️  Classes: {report['summary']['total_classes']}")
    print(f"🌐 Endpoints: {report['summary']['total_endpoints']}")
    print(f"❌ Total issues: {report['summary']['total_issues']}")
    print(f"   - Errors: {report['issues_by_severity']['error']}")
    print(f"   - Warnings: {report['issues_by_severity']['warning']}")
    print(f"   - Info: {report['issues_by_severity']['info']}")

    if "tested" in reviewer.endpoint_tests:
        print(f"🔍 Endpoints tested: {reviewer.endpoint_tests['tested']}")
        print(f"✅ Passed: {reviewer.endpoint_tests['passed']}")
        print(f"❌ Failed: {reviewer.endpoint_tests['failed']}")

    # Save detailed report
    with open("comprehensive_review_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\\n💾 Detailed report saved to: comprehensive_review_report.json")
    print("🎉 Review completed!")

    return report


if __name__ == "__main__":
    main()
