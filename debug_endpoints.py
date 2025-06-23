#!/usr/bin/env python3
"""
Test script to check if pipeline endpoints can be loaded
"""

import sys
import traceback

print("Testing pipeline endpoint imports...")

try:
    # Try to import the main module and check for syntax errors
    print("1. Checking main.py syntax...")
    import ast
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    ast.parse(content)
    print("✅ Syntax is valid")
    
    # Check if we can import specific functions
    print("2. Testing imports...")
    from main import app
    print("✅ FastAPI app imported successfully")
      # List all routes
    print("3. Checking registered routes...")
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            methods = getattr(route, 'methods', ['GET'])
            if methods:
                method = list(methods)[0] if isinstance(methods, set) else str(methods[0])
                routes.append(f"{method} {route.path}")
            else:
                routes.append(f"GET {route.path}")
    
    print(f"Found {len(routes)} routes:")
    for route in sorted(routes):
        print(f"  {route}")
    
    # Check for pipeline endpoints specifically
    pipeline_routes = [r for r in routes if '/api/' in r and ('memory' in r or 'learning' in r or 'pipeline' in r)]
    print(f"\nPipeline-related routes: {len(pipeline_routes)}")
    for route in pipeline_routes:
        print(f"  {route}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    traceback.print_exc()
