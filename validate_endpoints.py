#!/usr/bin/env python3
"""
Endpoint Validation Script
==========================

This script validates all endpoints defined in the FastAPI backend,
cross-references imports, and checks for completeness.
"""

import os
import sys
import re
from pathlib import Path

def check_file_exists(filepath):
    """Check if a file exists and return status."""
    return os.path.exists(filepath)

def extract_endpoints_from_file(filepath):
    """Extract API endpoints from a Python file."""
    if not os.path.exists(filepath):
        return []
    
    endpoints = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find all @router.method or @app.method patterns
        patterns = [
            r'@(?:router|app|health_router|chat_router|models_router|enhanced_router|upload_router|feedback_router)\.(get|post|put|delete|patch)\([\'"](.*?)[\'"]',
            r'@(?:router|app|health_router|chat_router|models_router|enhanced_router|upload_router|feedback_router)\.(get|post|put|delete|patch)\(\s*[\'"](.*?)[\'"]',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for method, path in matches:
                endpoints.append({
                    'method': method.upper(),
                    'path': path,
                    'file': os.path.basename(filepath)
                })
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    
    return endpoints

def validate_imports_in_file(filepath):
    """Check if all imports in a file are resolvable."""
    if not os.path.exists(filepath):
        return False, f"File {filepath} does not exist"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract import statements
        import_patterns = [
            r'from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import',
            r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
        ]
        
        imports = []
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)
        
        # Check if imported files exist (basic check)
        missing_imports = []
        for imp in imports:
            # Convert module path to file path
            if '.' in imp:
                parts = imp.split('.')
                # Check if it's a relative import
                potential_paths = [
                    f"{'/'.join(parts)}.py",
                    f"{'/'.join(parts)}/__init__.py",
                    f"{parts[0]}.py"
                ]
            else:
                potential_paths = [f"{imp}.py", f"{imp}/__init__.py"]
            
            # Check if any of the potential paths exist
            found = False
            for path in potential_paths:
                if os.path.exists(path) or imp in ['fastapi', 'pydantic', 'redis', 'httpx', 'chromadb', 'json', 'time', 'os', 'sys', 'logging', 'typing', 'datetime', 'uuid', 'asyncio']:
                    found = True
                    break
            
            if not found:
                missing_imports.append(imp)
        
        return len(missing_imports) == 0, missing_imports
    
    except Exception as e:
        return False, f"Error validating imports: {e}"

def main():
    """Main validation function."""
    print("🔍 FastAPI Backend Endpoint Validation")
    print("=" * 50)
    
    # Define all router files based on main.py imports
    router_files = [
        'main.py',
        'routes/health.py',
        'routes/chat.py', 
        'routes/models.py',
        'model_manager.py',
        'upload.py',
        'enhanced_integration.py',
        'feedback_router.py',
        'pipelines/pipelines_v1_routes.py'
    ]
    
    all_endpoints = []
    missing_files = []
    import_issues = []
    
    print("\n📁 Checking Router Files:")
    for router_file in router_files:
        if check_file_exists(router_file):
            print(f"  ✅ {router_file}")
            endpoints = extract_endpoints_from_file(router_file)
            all_endpoints.extend(endpoints)
            
            # Check imports
            valid_imports, import_result = validate_imports_in_file(router_file)
            if not valid_imports:
                import_issues.append({
                    'file': router_file,
                    'issues': import_result
                })
        else:
            print(f"  ❌ {router_file} - MISSING")
            missing_files.append(router_file)
    
    print(f"\n🌐 Found Endpoints ({len(all_endpoints)} total):")
    
    # Group endpoints by method
    endpoints_by_method = {}
    for endpoint in all_endpoints:
        method = endpoint['method']
        if method not in endpoints_by_method:
            endpoints_by_method[method] = []
        endpoints_by_method[method].append(endpoint)
    
    for method in sorted(endpoints_by_method.keys()):
        print(f"\n  {method}:")
        for endpoint in endpoints_by_method[method]:
            print(f"    {endpoint['path']} ({endpoint['file']})")
    
    # Check for critical OpenAI-compatible endpoints
    print(f"\n🎯 Critical Endpoints Check:")
    critical_endpoints = [
        ('POST', '/v1/chat/completions'),
        ('GET', '/v1/models'),
        ('GET', '/health'),
        ('POST', '/chat')
    ]
    
    for method, path in critical_endpoints:
        found = any(e['method'] == method and e['path'] == path for e in all_endpoints)
        status = "✅" if found else "❌"
        print(f"  {status} {method} {path}")
    
    # Report missing files
    if missing_files:
        print(f"\n❌ Missing Files:")
        for file in missing_files:
            print(f"  - {file}")
    
    # Report import issues
    if import_issues:
        print(f"\n⚠️  Import Issues:")
        for issue in import_issues:
            print(f"  📁 {issue['file']}:")
            if isinstance(issue['issues'], list):
                for imp in issue['issues']:
                    print(f"    - {imp}")
            else:
                print(f"    - {issue['issues']}")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  Total endpoints: {len(all_endpoints)}")
    print(f"  Router files found: {len(router_files) - len(missing_files)}/{len(router_files)}")
    print(f"  Missing files: {len(missing_files)}")
    print(f"  Import issues: {len(import_issues)}")
    
    # Check directory structure
    print(f"\n📁 Directory Structure Check:")
    expected_dirs = ['routes', 'services', 'utilities', 'pipelines', 'handlers', 'tests']
    for dir_name in expected_dirs:
        exists = os.path.exists(dir_name)
        status = "✅" if exists else "❌"
        print(f"  {status} {dir_name}/")
    
    return len(missing_files) == 0 and len(import_issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
