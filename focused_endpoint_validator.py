#!/usr/bin/env python3
"""
Focused Endpoint Validation
===========================
Validates key endpoints against their implementations and tests functionality.
"""

import ast
import json
import requests
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8001"
API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def test_endpoint(method, path, data=None, description=""):
    """Test a specific endpoint and return result."""
    url = f"{BASE_URL}{path}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=15)
        else:
            return {"status": "unsupported_method"}
        
        return {
            "status": "success" if response.status_code < 400 else "error",
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds(),
            "content": response.text[:200] if response.text else "",
            "description": description
        }
    
    except Exception as e:
        return {"status": "exception", "error": str(e), "description": description}

def get_routes_from_app():
    """Get routes directly from FastAPI app."""
    try:
        from main import app
        
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = getattr(route, 'methods', set())
                path = getattr(route, 'path', '')
                if methods and path:
                    for method in methods:
                        if method != 'OPTIONS':
                            routes.append(f"{method} {path}")
        
        return sorted(routes)
    except Exception as e:
        print(f"❌ Error getting app routes: {e}")
        return []

def find_endpoint_definitions():
    """Find endpoint definitions in main files."""
    endpoint_files = {
        'main.py': [],
        'upload.py': [],
        'enhanced_integration.py': [],
        'feedback_router.py': [],
        'model_manager.py': []
    }
    
    for filename in endpoint_files.keys():
        if Path(filename).exists():
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple regex search for endpoint decorators
                import re
                pattern = r'@\w+\.(get|post|put|delete|patch)\([\'"]([^\'\"]+)[\'"]\)'
                matches = re.findall(pattern, content)
                
                for method, path in matches:
                    endpoint_files[filename].append(f"{method.upper()} {path}")
                    
            except Exception as e:
                print(f"⚠️ Error reading {filename}: {e}")
    
    return endpoint_files

def main():
    print("🚀 FOCUSED ENDPOINT VALIDATION")
    print(f"🎯 Target: {BASE_URL}")
    
    # Get live routes
    print_section("LIVE ROUTE DISCOVERY")
    live_routes = get_routes_from_app()
    print(f"📡 Found {len(live_routes)} live routes:")
    for route in live_routes:
        print(f"   {route}")
    
    # Find definitions
    print_section("ENDPOINT DEFINITIONS")
    definitions = find_endpoint_definitions()
    total_defined = sum(len(endpoints) for endpoints in definitions.values())
    print(f"📝 Found {total_defined} defined endpoints across files:")
    for filename, endpoints in definitions.items():
        if endpoints:
            print(f"   {filename}: {len(endpoints)} endpoints")
            for endpoint in endpoints:
                print(f"      {endpoint}")
    
    # Test key endpoints
    print_section("KEY ENDPOINT TESTING")
    
    key_tests = [
        ("GET", "/", None, "Root health check"),
        ("GET", "/health", None, "Basic health"),
        ("GET", "/health/detailed", None, "Detailed health"),
        ("GET", "/api/pipeline/status", None, "Pipeline status"),
        ("POST", "/api/memory/retrieve", {
            "user_id": "test_user",
            "query": "test query",
            "limit": 3
        }, "Memory retrieval"),
        ("POST", "/api/learning/process_interaction", {
            "user_id": "test_user",
            "conversation_id": "test_conv",
            "user_message": "Hello",
            "assistant_response": "Hi there",
            "response_time": 1.0
        }, "Learning storage"),
        ("GET", "/v1/models", None, "OpenAI models endpoint"),
        ("POST", "/v1/chat/completions", {
            "model": "llama3.2:3b",
            "messages": [{"role": "user", "content": "Test message"}],
            "max_tokens": 5
        }, "Chat completions"),
        ("GET", "/models", None, "Internal models"),
        ("POST", "/upload/search", {
            "query": "test",
            "user_id": "test_user"
        }, "Document search"),
    ]
    
    results = {}
    for method, path, data, description in key_tests:
        print(f"🔄 Testing {method} {path} - {description}")
        result = test_endpoint(method, path, data, description)
        results[f"{method} {path}"] = result
        
        status = result['status']
        if status == 'success':
            code = result['status_code']
            time_ms = result['response_time'] * 1000
            print(f"   ✅ HTTP {code} ({time_ms:.0f}ms)")
        elif status == 'error':
            code = result['status_code']
            print(f"   ❌ HTTP {code}")
        else:
            error = result.get('error', 'unknown')
            print(f"   ❌ {status}: {error}")
        
        time.sleep(0.5)  # Brief pause between tests
    
    # Summary
    print_section("VALIDATION SUMMARY")
    
    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    total_tests = len(results)
    success_rate = success_count / total_tests * 100
    
    print(f"📊 Test Results:")
    print(f"   ✅ Successful: {success_count}/{total_tests}")
    print(f"   📈 Success Rate: {success_rate:.1f}%")
    
    # Detailed results
    print(f"\n📋 Detailed Results:")
    for endpoint, result in results.items():
        status = result['status']
        desc = result['description']
        if status == 'success':
            code = result['status_code']
            print(f"   ✅ {endpoint} → HTTP {code} ({desc})")
        else:
            print(f"   ❌ {endpoint} → {status} ({desc})")
    
    # Cross-reference check
    print(f"\n🔄 Cross-Reference Analysis:")
    live_set = set(live_routes)
    defined_set = set()
    for endpoints in definitions.values():
        defined_set.update(endpoints)
    
    common = live_set & defined_set
    live_only = live_set - defined_set
    defined_only = defined_set - live_set
    
    print(f"   📊 Common (live + defined): {len(common)}")
    print(f"   📡 Live only: {len(live_only)}")
    print(f"   📝 Defined only: {len(defined_only)}")
    
    if live_only:
        print(f"   🔍 Live but not found in code:")
        for endpoint in sorted(live_only):
            print(f"      {endpoint}")
    
    # Final assessment
    print_section("FINAL ASSESSMENT")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT: All key endpoints fully functional!")
    elif success_rate >= 80:
        print("✅ GOOD: Most endpoints working, minor issues.")
    elif success_rate >= 60:
        print("⚠️ PARTIAL: Some endpoints working, needs attention.")
    else:
        print("❌ CRITICAL: Multiple endpoint failures detected.")
    
    # Memory pipeline specific check
    memory_endpoints = [
        "GET /api/pipeline/status",
        "POST /api/memory/retrieve",
        "POST /api/learning/process_interaction"
    ]
    
    memory_working = all(
        results.get(ep, {}).get('status') == 'success' 
        for ep in memory_endpoints
    )
    
    if memory_working:
        print("🧠 MEMORY PIPELINE: ✅ Fully operational!")
    else:
        print("🧠 MEMORY PIPELINE: ❌ Issues detected!")
        for ep in memory_endpoints:
            status = results.get(ep, {}).get('status', 'not_tested')
            print(f"   {ep}: {status}")
    
    return {
        'success_rate': success_rate,
        'memory_pipeline': memory_working,
        'total_live_routes': len(live_routes),
        'total_defined': total_defined,
        'results': results
    }

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted")
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
