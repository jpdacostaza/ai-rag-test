#!/usr/bin/env python3
"""
Comprehensive Code Analysis and Cleanup Tool
============================================

This script performs a thorough analysis of all Python files:
1. Syntax validation
2. Import verification
3. Duplicate code detection
4. Cross-reference validation
5. Critical functionality verification
"""

import ast
import os
import sys
import re
import importlib.util
from pathlib import Path
from collections import defaultdict
import subprocess

def check_syntax(filepath):
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"

def extract_imports(filepath):
    """Extract all imports from a Python file."""
    imports = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST to get imports
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
    except Exception as e:
        print(f"Error extracting imports from {filepath}: {e}")
    
    return imports

def extract_functions(filepath):
    """Extract all function definitions from a Python file."""
    functions = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
    except Exception as e:
        print(f"Error extracting functions from {filepath}: {e}")
    
    return functions

def find_duplicate_functions():
    """Find duplicate function definitions across files."""
    all_functions = defaultdict(list)
    
    for filepath in Path('.').rglob('*.py'):
        # Skip problematic directories
        if any(skip in str(filepath) for skip in ['venv', '__pycache__', 'storage', '.git']):
            continue
        try:
            if filepath.is_file():
                functions = extract_functions(str(filepath))
                for func in functions:
                    all_functions[func].append(str(filepath))
        except (OSError, IOError) as e:
            # Skip files that can't be accessed
            continue
    
    duplicates = {func: files for func, files in all_functions.items() if len(files) > 1}
    return duplicates

def check_critical_files():
    """Check that all critical files exist and are functional."""
    critical_files = [
        'main.py',
        'config.py',
        'models.py',
        'database_manager.py',
        'database.py',
        'human_logging.py',
        'error_handler.py',
        'startup.py',
        'routes/health.py',
        'routes/chat.py',
        'routes/models.py',
        'services/llm_service.py',
        'services/streaming_service.py',
        'utilities/ai_tools.py'
    ]
    
    missing = []
    syntax_errors = []
    
    for file in critical_files:
        if not os.path.exists(file):
            missing.append(file)
        else:
            valid, error = check_syntax(file)
            if not valid:
                syntax_errors.append((file, error))
    
    return missing, syntax_errors

def validate_imports_comprehensive():
    """Comprehensive import validation across all Python files."""
    all_files = list(Path('.').rglob('*.py'))
    import_issues = defaultdict(list)
    
    # Standard library modules (partial list)
    stdlib_modules = {
        'os', 'sys', 'json', 'time', 'datetime', 'uuid', 'asyncio', 'logging',
        'typing', 're', 'pathlib', 'collections', 'itertools', 'functools',
        'dataclasses', 'contextlib', 'io', 'math', 'platform', 'subprocess',
        'enum', 'hashlib', 'traceback', 'threading', 'argparse', 'tempfile',
        'urllib', 'ast', 'importlib'
    }
    
    # Third-party modules we expect to have
    thirdparty_modules = {
        'fastapi', 'pydantic', 'redis', 'httpx', 'chromadb', 'sentence_transformers',
        'langchain', 'wikipedia', 'beautifulsoup4', 'uvicorn', 'RestrictedPython',
        'bs4', 'zoneinfo', 'requests', 'torch', 'tenacity', 'starlette'
    }
    
    # Local modules (files in our project)
    local_modules = set()
    for filepath in all_files:
        module_name = str(filepath.relative_to('.').with_suffix(''))
        module_name = module_name.replace('/', '.').replace('\\', '.')
        local_modules.add(module_name)
        # Also add the directory as a module if it has __init__.py
        if filepath.name == '__init__.py':
            parent_module = str(filepath.parent.relative_to('.'))
            parent_module = parent_module.replace('/', '.').replace('\\', '.')
            if parent_module != '.':
                local_modules.add(parent_module)
    
    for filepath in all_files:
        # Skip problematic directories  
        if any(skip in str(filepath) for skip in ['venv', '__pycache__', 'storage', '.git']):
            continue
            
        imports = extract_imports(str(filepath))
        for imp in imports:
            # Skip if it's a standard library module
            if imp.split('.')[0] in stdlib_modules:
                continue
            # Skip if it's a known third-party module
            if imp.split('.')[0] in thirdparty_modules:
                continue
            # Check if it's a local module
            if imp in local_modules or imp.replace('.', '/') in [str(f.with_suffix('')) for f in all_files]:
                continue
            # Check if the base module exists as a file
            base_module = imp.split('.')[0]
            if (Path(f"{base_module}.py").exists() or 
                Path(base_module).is_dir() and Path(f"{base_module}/__init__.py").exists()):
                continue
            
            import_issues[str(filepath)].append(imp)
    
    return dict(import_issues)

def check_endpoint_completeness():
    """Verify all endpoints are properly defined and cross-referenced."""
    endpoint_files = [
        'main.py', 'routes/health.py', 'routes/chat.py', 'routes/models.py',
        'model_manager.py', 'upload.py', 'enhanced_integration.py',
        'feedback_router.py', 'pipelines/pipelines_v1_routes.py'
    ]
    
    total_endpoints = 0
    endpoint_issues = []
    
    for file in endpoint_files:
        if not os.path.exists(file):
            endpoint_issues.append(f"Missing endpoint file: {file}")
            continue
            
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count endpoints
            endpoint_patterns = [
                r'@(?:router|app|.*_router)\.(get|post|put|delete|patch)\(',
            ]
            
            for pattern in endpoint_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                total_endpoints += len(matches)
                
        except Exception as e:
            endpoint_issues.append(f"Error reading {file}: {e}")
    
    return total_endpoints, endpoint_issues

def analyze_code_quality():
    """Analyze code quality issues."""
    quality_issues = []
    
    # Check for common patterns that indicate issues
    problematic_patterns = [
        (r'# TODO', 'TODO comments found'),
        (r'# FIXME', 'FIXME comments found'),
        (r'# XXX', 'XXX comments found'),
        (r'print\(.*\)', 'Debug print statements found'),
        (r'import \*', 'Wildcard imports found'),
    ]
    
    for filepath in Path('.').rglob('*.py'):
        # Skip problematic directories
        if any(skip in str(filepath) for skip in ['venv', '__pycache__', 'storage', '.git']):
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern, message in problematic_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    quality_issues.append(f"{filepath}: {message} ({len(matches)} occurrences)")
                    
        except Exception as e:
            quality_issues.append(f"Error analyzing {filepath}: {e}")
    
    return quality_issues

def main():
    """Main analysis function."""
    print("Comprehensive Code Analysis and Cleanup")
    print("=" * 60)
    
    # 1. Check critical files
    print("\n1. Critical Files Check:")
    missing_critical, syntax_errors = check_critical_files()
    
    if missing_critical:
        print("[X] Missing critical files:")
        for file in missing_critical:
            print(f"   - {file}")
    else:
        print("[OK] All critical files present")
    
    if syntax_errors:
        print("[X] Syntax errors in critical files:")
        for file, error in syntax_errors:
            print(f"   - {file}: {error}")
    else:
        print("[OK] No syntax errors in critical files")
    
    # Comprehensive syntax check
    print("\n2. Comprehensive Syntax Check:")
    all_files = list(Path('.').rglob('*.py'))
    syntax_ok = 0
    syntax_fail = 0
    
    for filepath in all_files:
        # Skip problematic directories
        if any(skip in str(filepath) for skip in ['venv', '__pycache__', 'storage', '.git']):
            continue
        valid, error = check_syntax(str(filepath))
        if valid:
            syntax_ok += 1
        else:
            syntax_fail += 1
            print(f"[X] {filepath}: {error}")
    
    print(f"[OK] Syntax check: {syntax_ok} OK, {syntax_fail} FAILED")
    
    # 3. Import validation
    print("\n3. Import Validation:")
    import_issues = validate_imports_comprehensive()
    
    if import_issues:
        print("[!] Import issues found:")
        for file, issues in import_issues.items():
            print(f"    {file}:")
            for issue in issues:
                print(f"      - {issue}")
    else:
        print("[OK] All imports appear valid")
    
    # 4. Duplicate function detection
    print("\n4. Duplicate Function Detection:")
    duplicates = find_duplicate_functions()
    
    if duplicates:
        print("[!] Duplicate functions found:")
        for func, files in duplicates.items():
            if len(files) > 1:
                print(f"   [DUP] {func}: {files}")
    else:
        print("[OK] No duplicate functions found")
    
    # 5. Endpoint completeness
    print("\n5. Endpoint Completeness:")
    total_endpoints, endpoint_issues = check_endpoint_completeness()
    
    print(f"[STATS] Total endpoints found: {total_endpoints}")
    if endpoint_issues:
        print("[X] Endpoint issues:")
        for issue in endpoint_issues:
            print(f"   - {issue}")
    else:
        print("[OK] All endpoint files accessible")
    
    # 6. Code quality analysis
    print("\n6. Code Quality Analysis:")
    quality_issues = analyze_code_quality()
    
    if quality_issues:
        print("[!] Code quality issues:")
        for issue in quality_issues[:10]:  # Show first 10 issues
            print(f"   - {issue}")
        if len(quality_issues) > 10:
            print(f"   ... and {len(quality_issues) - 10} more issues")
    else:
        print("[OK] No major code quality issues found")
    
    # 7. Summary
    print(f"\n[SUMMARY] SUMMARY:")
    print(f"   Total Python files: {len(all_files)}")
    print(f"   Syntax errors: {syntax_fail}")
    print(f"   Import issues: {len(import_issues)}")
    print(f"   Duplicate functions: {len(duplicates)}")
    print(f"   Total endpoints: {total_endpoints}")
    print(f"   Quality issues: {len(quality_issues)}")
    
    # Overall status
    if syntax_fail == 0 and len(import_issues) == 0 and len(missing_critical) == 0:
        print("\n🎉 OVERALL STATUS: HEALTHY [OK]")
        return True
    else:
        print("\n[!] OVERALL STATUS: NEEDS ATTENTION [X]")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
