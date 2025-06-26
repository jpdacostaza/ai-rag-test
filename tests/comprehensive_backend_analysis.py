#!/usr/bin/env python3
"""
Comprehensive Backend Code Review and Quality Analysis
Performs detailed analysis of all production code and creates a comprehensive report
"""

import os
import sys
import ast
import json
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import requests

# Add backend root to path
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))


class BackendCodeAnalyzer:
    def __init__(self):
        self.backend_path = Path(__file__).parent.parent
        self.issues = []
        self.file_analysis = {}
        self.endpoint_inventory = {}
        self.import_dependencies = {}

    def log_issue(self, category: str, severity: str, file_path: str, line: int, message: str, suggestion: str = ""):
        """Log a code quality issue with optional suggestion"""
        issue = {
            "category": category,
            "severity": severity,
            "file": str(file_path.relative_to(self.backend_path)),
            "line": line,
            "message": message,
            "suggestion": suggestion,
            "timestamp": datetime.now().isoformat(),
        }
        self.issues.append(issue)
        print(f"🔍 {severity.upper()} [{category}] {file_path.name}:{line} - {message}")
        if suggestion:
            print(f"    💡 Suggestion: {suggestion}")

    def analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Comprehensive analysis of a Python file"""
        analysis = {
            "file": str(file_path.relative_to(self.backend_path)),
            "lines": 0,
            "functions": [],
            "classes": [],
            "imports": [],
            "endpoints": [],
            "complexity_score": 0,
            "docstring_coverage": 0,
            "test_coverage": "unknown",
        }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\\n")
                analysis["lines"] = len(lines)

                # Parse AST for detailed analysis
                try:
                    tree = ast.parse(content)
                    self.analyze_ast(tree, file_path, analysis)
                except SyntaxError as e:
                    self.log_issue(
                        "syntax",
                        "error",
                        file_path,
                        e.lineno or 0,
                        f"Syntax error: {e}",
                        "Fix syntax error before proceeding",
                    )

                # Line-by-line analysis
                self.analyze_lines(lines, file_path, analysis)

        except Exception as e:
            self.log_issue(
                "file_access", "error", file_path, 0, f"Cannot read file: {e}", "Check file permissions and encoding"
            )

        return analysis

    def analyze_ast(self, tree: ast.AST, file_path: Path, analysis: Dict):
        """Analyze AST for functions, classes, imports, and endpoints"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "args": len(node.args.args),
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "has_docstring": ast.get_docstring(node) is not None,
                    "complexity": self.calculate_complexity(node),
                }
                analysis["functions"].append(func_info)

                # Check for API endpoints
                for decorator in node.decorator_list:
                    endpoint = self.extract_endpoint_info(decorator, node, file_path)
                    if endpoint:
                        analysis["endpoints"].append(endpoint)

            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "methods": len([n for n in node.body if isinstance(n, ast.FunctionDef)]),
                    "has_docstring": ast.get_docstring(node) is not None,
                }
                analysis["classes"].append(class_info)

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_info = self.extract_import_info(node)
                if import_info:
                    analysis["imports"].append(import_info)

    def extract_endpoint_info(self, decorator: ast.expr, func_node: ast.FunctionDef, file_path: Path) -> Dict:
        """Extract API endpoint information from decorators"""
        if not isinstance(decorator, ast.Call):
            return None

        if hasattr(decorator.func, "attr") and decorator.func.attr in [
            "get",
            "post",
            "put",
            "delete",
            "patch",
            "head",
            "options",
        ]:
            method = decorator.func.attr.upper()

            # Extract path
            path = "/"
            if decorator.args and isinstance(decorator.args[0], (ast.Str, ast.Constant)):
                path = decorator.args[0].s if hasattr(decorator.args[0], "s") else decorator.args[0].value

            return {
                "method": method,
                "path": path,
                "function": func_node.name,
                "line": func_node.lineno,
                "file": str(file_path.relative_to(self.backend_path)),
                "has_docstring": ast.get_docstring(func_node) is not None,
                "param_count": len(func_node.args.args),
            }
        return None

    def extract_import_info(self, node) -> Dict:
        """Extract import information"""
        if isinstance(node, ast.Import):
            return {"type": "import", "modules": [alias.name for alias in node.names], "line": node.lineno}
        elif isinstance(node, ast.ImportFrom):
            return {
                "type": "from",
                "module": node.module,
                "names": [alias.name for alias in node.names],
                "line": node.lineno,
                "level": node.level,
            }
        return None

    def calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(
                child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.AsyncWith)
            ):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def analyze_lines(self, lines: List[str], file_path: Path, analysis: Dict):
        """Analyze individual lines for quality issues"""
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Line length check
            if len(line) > 100:  # PEP8 recommends 79, but we'll be lenient
                if len(line) > 150:  # Very long lines
                    self.log_issue(
                        "style",
                        "warning",
                        file_path,
                        i,
                        f"Very long line ({len(line)} chars)",
                        "Consider breaking into multiple lines",
                    )

            # Security issues
            if any(pattern in line.lower() for pattern in ["password", "secret", "key"]) and "=" in line:
                if not any(safe in line.lower() for safe in ["config", "env", "get"]):
                    self.log_issue(
                        "security",
                        "warning",
                        file_path,
                        i,
                        "Potential hardcoded credential",
                        "Use environment variables for secrets",
                    )

            # TODO/FIXME tracking
            if any(keyword in line.upper() for keyword in ["TODO", "FIXME", "HACK", "XXX"]):
                self.log_issue(
                    "maintenance",
                    "info",
                    file_path,
                    i,
                    f"Maintenance comment: {line_stripped[:50]}...",
                    "Address technical debt when possible",
                )

            # Print statement detection (should use logging)
            if line_stripped.startswith("print(") and "test" not in file_path.name.lower():
                self.log_issue(
                    "logging",
                    "info",
                    file_path,
                    i,
                    "Print statement in production code",
                    "Use structured logging instead",
                )

            # Bare except detection
            if line_stripped == "except:":
                self.log_issue(
                    "error_handling",
                    "warning",
                    file_path,
                    i,
                    "Bare except clause",
                    "Catch specific exceptions or use 'except Exception:'",
                )

    def check_file_imports(self, file_path: Path, imports: List[Dict]) -> List[str]:
        """Check if imports are resolvable"""
        broken_imports = []

        for imp in imports:
            try:
                if imp["type"] == "import":
                    for module in imp["modules"]:
                        if not self.can_import_module(module):
                            broken_imports.append(f"Line {imp['line']}: Cannot import '{module}'")
                            self.log_issue(
                                "imports",
                                "error",
                                file_path,
                                imp["line"],
                                f"Cannot import '{module}'",
                                "Check if module exists or update import path",
                            )
                elif imp["type"] == "from" and imp["module"]:
                    if not self.can_import_module(imp["module"]):
                        broken_imports.append(f"Line {imp['line']}: Cannot import from '{imp['module']}'")
                        self.log_issue(
                            "imports",
                            "error",
                            file_path,
                            imp["line"],
                            f"Cannot import from '{imp['module']}'",
                            "Check if module exists or update import path",
                        )
            except Exception as e:
                self.log_issue(
                    "imports", "warning", file_path, imp["line"], f"Import check failed: {e}", "Review import statement"
                )

        return broken_imports

    def can_import_module(self, module_name: str) -> bool:
        """Check if a module can be imported"""
        try:
            spec = importlib.util.find_spec(module_name)
            return spec is not None
        except (ImportError, ValueError, ModuleNotFoundError):
            return False

    def scan_production_code(self) -> Dict[str, Any]:
        """Scan all production Python files (excluding tests and utilities)"""
        print("🔍 Scanning production codebase...")

        # Define production code patterns
        production_patterns = ["*.py"]

        exclude_patterns = ["__pycache__", "tests/", "test_", ".pyc"]

        python_files = []
        for pattern in production_patterns:
            for file_path in self.backend_path.rglob(pattern):
                if not any(exclude in str(file_path) for exclude in exclude_patterns):
                    python_files.append(file_path)

        print(f"📁 Found {len(python_files)} production Python files")

        for file_path in python_files:
            print(f"📄 Analyzing {file_path.relative_to(self.backend_path)}")
            analysis = self.analyze_python_file(file_path)
            self.file_analysis[str(file_path.relative_to(self.backend_path))] = analysis

            # Check imports
            if analysis["imports"]:
                broken_imports = self.check_file_imports(file_path, analysis["imports"])
                if broken_imports:
                    analysis["broken_imports"] = broken_imports

        return self.file_analysis

    def build_endpoint_inventory(self) -> Dict[str, List[Dict]]:
        """Build comprehensive endpoint inventory"""
        endpoints_by_file = {}
        all_endpoints = []

        for file_analysis in self.file_analysis.values():
            if file_analysis["endpoints"]:
                file_name = file_analysis["file"]
                endpoints_by_file[file_name] = file_analysis["endpoints"]
                all_endpoints.extend(file_analysis["endpoints"])

        # Group by HTTP method
        by_method = {}
        for endpoint in all_endpoints:
            method = endpoint["method"]
            if method not in by_method:
                by_method[method] = []
            by_method[method].append(endpoint)

        return {
            "by_file": endpoints_by_file,
            "by_method": by_method,
            "total_count": len(all_endpoints),
            "all_endpoints": all_endpoints,
        }

    def test_live_endpoints(self, base_url: str = "http://localhost:9099") -> Dict[str, Any]:
        """Test live endpoints if backend is running"""
        print(f"\\n🌐 Testing live endpoints at {base_url}...")

        test_results = {"tested": 0, "passed": 0, "failed": 0, "skipped": 0, "results": []}

        if not self.endpoint_inventory:
            print("⚠️  No endpoints found to test")
            return test_results

        all_endpoints = self.endpoint_inventory.get("all_endpoints", [])

        for endpoint in all_endpoints:
            method = endpoint["method"]
            path = endpoint["path"]

            # Skip parameterized paths for automated testing
            if "{" in path or "<" in path:
                test_results["skipped"] += 1
                test_results["results"].append(
                    {"method": method, "path": path, "status": "skipped", "reason": "parameterized path"}
                )
                continue

            test_results["tested"] += 1

            try:
                if method == "GET":
                    response = requests.get(f"{base_url}{path}", timeout=10)
                elif method == "POST":
                    # Send minimal valid JSON for POST requests
                    response = requests.post(f"{base_url}{path}", json={}, timeout=10)
                else:
                    test_results["skipped"] += 1
                    test_results["results"].append(
                        {
                            "method": method,
                            "path": path,
                            "status": "skipped",
                            "reason": f"method {method} not auto-tested",
                        }
                    )
                    continue

                # Consider 2xx, 3xx, and 4xx as successful (endpoint exists)
                if response.status_code < 500:
                    test_results["passed"] += 1
                    status = "passed"
                else:
                    test_results["failed"] += 1
                    status = "failed"

                test_results["results"].append(
                    {
                        "method": method,
                        "path": path,
                        "status": status,
                        "status_code": response.status_code,
                        "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                        "content_length": len(response.content),
                    }
                )

                print(
                    f"  {method:4} {path:30} → {response.status_code} ({response.elapsed.total_seconds()*1000:.0f}ms)"
                )

            except Exception as e:
                test_results["failed"] += 1
                test_results["results"].append({"method": method, "path": path, "status": "error", "error": str(e)})
                print(f"  {method:4} {path:30} → ERROR: {e}")

        return test_results

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality and analysis report"""
        # Calculate summary statistics
        total_files = len(self.file_analysis)
        total_lines = sum(f.get("lines", 0) for f in self.file_analysis.values())
        total_functions = sum(len(f.get("functions", [])) for f in self.file_analysis.values())
        total_classes = sum(len(f.get("classes", [])) for f in self.file_analysis.values())

        # Analyze issues by category and severity
        issues_by_category = {}
        issues_by_severity = {}

        for issue in self.issues:
            category = issue["category"]
            severity = issue["severity"]

            if category not in issues_by_category:
                issues_by_category[category] = []
            issues_by_category[category].append(issue)

            if severity not in issues_by_severity:
                issues_by_severity[severity] = []
            issues_by_severity[severity].append(issue)

        # Calculate quality scores
        error_count = len(issues_by_severity.get("error", []))
        warning_count = len(issues_by_severity.get("warning", []))
        info_count = len(issues_by_severity.get("info", []))

        # Simple quality score (0-100)
        quality_score = max(0, 100 - (error_count * 10) - (warning_count * 2) - (info_count * 0.5))

        report = {
            "metadata": {
                "scan_timestamp": datetime.now().isoformat(),
                "backend_path": str(self.backend_path),
                "analyzer_version": "1.0.0",
            },
            "summary": {
                "total_files": total_files,
                "total_lines": total_lines,
                "total_functions": total_functions,
                "total_classes": total_classes,
                "total_endpoints": self.endpoint_inventory.get("total_count", 0),
                "total_issues": len(self.issues),
                "quality_score": round(quality_score, 1),
            },
            "quality_metrics": {
                "issues_by_severity": {
                    "error": len(issues_by_severity.get("error", [])),
                    "warning": len(issues_by_severity.get("warning", [])),
                    "info": len(issues_by_severity.get("info", [])),
                },
                "issues_by_category": {cat: len(issues) for cat, issues in issues_by_category.items()},
                "quality_score": round(quality_score, 1),
            },
            "endpoint_inventory": self.endpoint_inventory,
            "file_analysis": self.file_analysis,
            "detailed_issues": self.issues,
        }

        return report


def main():
    """Main function to run comprehensive backend analysis"""
    print("🚀 Starting Comprehensive Backend Code Review")
    print("=" * 70)

    analyzer = BackendCodeAnalyzer()

    # Scan production code
    analyzer.scan_production_code()

    # Build endpoint inventory
    analyzer.endpoint_inventory = analyzer.build_endpoint_inventory()

    # Test live endpoints
    endpoint_test_results = {}
    try:
        endpoint_test_results = analyzer.test_live_endpoints()
    except Exception as e:
        print(f"⚠️  Endpoint testing failed: {e}")
        endpoint_test_results = {"error": str(e)}

    # Generate comprehensive report
    report = analyzer.generate_comprehensive_report()

    # Add endpoint test results to report
    report["endpoint_test_results"] = endpoint_test_results

    # Print summary
    print("\\n" + "=" * 70)
    print("📊 COMPREHENSIVE BACKEND ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"📁 Production files analyzed: {report['summary']['total_files']}")
    print(f"📄 Total lines of code: {report['summary']['total_lines']:,}")
    print(f"🔧 Functions: {report['summary']['total_functions']}")
    print(f"🏗️  Classes: {report['summary']['total_classes']}")
    print(f"🌐 API endpoints: {report['summary']['total_endpoints']}")
    print(f"📊 Quality score: {report['summary']['quality_score']}/100")
    print(f"❌ Total issues found: {report['summary']['total_issues']}")
    print(f"   - 🔴 Errors: {report['quality_metrics']['issues_by_severity']['error']}")
    print(f"   - 🟡 Warnings: {report['quality_metrics']['issues_by_severity']['warning']}")
    print(f"   - 🔵 Info: {report['quality_metrics']['issues_by_severity']['info']}")

    if "tested" in endpoint_test_results:
        print(f"\\n🌐 Endpoint Testing Results:")
        print(f"   - Tested: {endpoint_test_results['tested']}")
        print(f"   - ✅ Passed: {endpoint_test_results['passed']}")
        print(f"   - ❌ Failed: {endpoint_test_results['failed']}")
        print(f"   - ⏭️  Skipped: {endpoint_test_results['skipped']}")

    # Show top issue categories
    if report["quality_metrics"]["issues_by_category"]:
        print(f"\\n🔍 Top Issue Categories:")
        sorted_categories = sorted(
            report["quality_metrics"]["issues_by_category"].items(), key=lambda x: x[1], reverse=True
        )
        for category, count in sorted_categories[:5]:
            print(f"   - {category}: {count}")

    # Save detailed report
    report_path = "comprehensive_backend_analysis.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\\n💾 Detailed report saved to: {report_path}")

    # Create markdown summary
    create_markdown_report(report, endpoint_test_results)

    print("🎉 Comprehensive analysis completed!")

    return report


def create_markdown_report(report: Dict, endpoint_tests: Dict):
    """Create a markdown summary report"""
    md_content = f"""# Comprehensive Backend Code Review Report

**Generated**: {report['metadata']['scan_timestamp']}  
**Quality Score**: {report['summary']['quality_score']}/100  

## Executive Summary

| Metric | Value |
|--------|-------|
| Production Files | {report['summary']['total_files']} |
| Lines of Code | {report['summary']['total_lines']:,} |
| Functions | {report['summary']['total_functions']} |
| Classes | {report['summary']['total_classes']} |
| API Endpoints | {report['summary']['total_endpoints']} |
| Issues Found | {report['summary']['total_issues']} |

## Issue Summary

| Severity | Count |
|----------|-------|
| 🔴 Errors | {report['quality_metrics']['issues_by_severity']['error']} |
| 🟡 Warnings | {report['quality_metrics']['issues_by_severity']['warning']} |
| 🔵 Info | {report['quality_metrics']['issues_by_severity']['info']} |

## API Endpoints Discovered

"""

    if "all_endpoints" in report["endpoint_inventory"]:
        md_content += "| Method | Path | Function | File |\\n"
        md_content += "|--------|------|----------|------|\\n"
        for endpoint in report["endpoint_inventory"]["all_endpoints"]:
            md_content += (
                f"| {endpoint['method']} | `{endpoint['path']}` | {endpoint['function']} | {endpoint['file']} |\\n"
            )
    else:
        md_content += "No endpoints discovered.\\n"

    if "tested" in endpoint_tests:
        md_content += f"""
## Endpoint Testing Results

- **Tested**: {endpoint_tests['tested']}
- **Passed**: {endpoint_tests['passed']}
- **Failed**: {endpoint_tests['failed']}
- **Skipped**: {endpoint_tests['skipped']}
"""

    md_content += """
## Recommendations

Based on the analysis, here are the key areas for improvement:

1. **Address Error-level Issues**: Fix any import or syntax errors immediately
2. **Code Style**: Review warnings related to line length and formatting
3. **Security**: Address any potential security issues flagged
4. **Documentation**: Improve docstring coverage for better maintainability
5. **Testing**: Ensure all endpoints have proper test coverage

## Next Steps

1. Review the detailed JSON report for specific file-level issues
2. Prioritize fixing error-level issues first
3. Implement automated code quality checks in CI/CD
4. Consider adding pre-commit hooks for code formatting
5. Establish coding standards documentation

---
*This report was generated automatically. Review findings and apply fixes as appropriate.*
"""

    with open("backend_analysis_summary.md", "w") as f:
        f.write(md_content)

    print("📝 Markdown summary saved to: backend_analysis_summary.md")


if __name__ == "__main__":
    main()
