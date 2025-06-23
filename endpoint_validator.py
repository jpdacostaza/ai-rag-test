#!/usr/bin/env python3
"""
Comprehensive Endpoint Cross-Reference Validator
===============================================
Validates all endpoints against their implementations across all files.
"""

import ast
import json
import requests
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Configuration
BASE_URL = "http://localhost:8001"
API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

class EndpointValidator:
    def __init__(self):
        self.backend_files = []
        self.declared_endpoints = []
        self.imported_routers = []
        self.test_results = {}
        self.file_references = {}
        
    def scan_project_files(self):
        """Scan all Python files in the project."""
        print("🔍 Scanning project files...")
        
        project_root = Path(".")
        python_files = list(project_root.rglob("*.py"))
        
        for file_path in python_files:
            if file_path.name.startswith('.') or 'venv' in str(file_path) or '__pycache__' in str(file_path):
                continue
            self.backend_files.append(file_path)
        
        print(f"📁 Found {len(self.backend_files)} Python files")
        return self.backend_files
    
    def extract_endpoints_from_file(self, file_path: Path) -> List[Dict]:
        """Extract endpoint definitions from a Python file."""
        endpoints = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
              # Parse AST
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Look for decorators
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            # Handle @app.post("/path"), @router.get("/path"), etc.
                            func = getattr(decorator, 'func', None)
                            if func and hasattr(func, 'attr'):
                                method_name = str(func.attr)
                                if method_name in ['get', 'post', 'put', 'delete', 'patch']:
                                    
                                    args = getattr(decorator, 'args', [])
                                    if args:
                                        path_arg = args[0]
                                        if isinstance(path_arg, ast.Constant):
                                            endpoint = {
                                                'method': method_name.upper(),
                                                'path': str(path_arg.value),
                                                'function': node.name,
                                                'file': str(file_path),
                                                'line': node.lineno
                                            }
                                            endpoints.append(endpoint)
        
        except Exception as e:
            print(f"⚠️ Error parsing {file_path}: {e}")
        
        return endpoints
    
    def extract_all_endpoints(self):
        """Extract all endpoints from all files."""
        print("🔍 Extracting endpoints from all files...")
        
        all_endpoints = []
        for file_path in self.backend_files:
            file_endpoints = self.extract_endpoints_from_file(file_path)
            all_endpoints.extend(file_endpoints)
            
            if file_endpoints:
                self.file_references[str(file_path)] = file_endpoints
        
        self.declared_endpoints = all_endpoints
        print(f"📡 Found {len(all_endpoints)} declared endpoints")
        return all_endpoints
    
    def get_live_routes(self):
        """Get routes from the live FastAPI application."""
        print("🌐 Getting live routes from FastAPI app...")
        
        try:
            # Import the app and get routes
            sys.path.insert(0, '.')
            from main import app
            
            live_routes = []
            for route in app.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    methods = getattr(route, 'methods', set())
                    path = getattr(route, 'path', '')
                    if methods and path:
                        for method in methods:
                            if method != 'OPTIONS':  # Skip OPTIONS
                                live_routes.append({
                                    'method': method,
                                    'path': path,
                                    'name': getattr(route, 'name', 'unknown')
                                })
            
            print(f"🚀 Found {len(live_routes)} live routes")
            return live_routes
        
        except Exception as e:
            print(f"❌ Error getting live routes: {e}")
            traceback.print_exc()
            return []
    
    def test_endpoint_response(self, method: str, path: str) -> Dict:
        """Test an endpoint and return result."""
        test_url = f"{BASE_URL}{path}"
        
        # Skip certain paths that require specific parameters
        skip_paths = [
            '/docs', '/redoc', '/openapi.json',
            '/{', '/models/{model_name}', '/health/history/{service_name}'
        ]
        
        if any(skip in path for skip in skip_paths):
            return {"status": "skipped", "reason": "parameterized or docs path"}
        
        try:
            # Prepare test data based on endpoint
            data = None
            if method in ['POST', 'PUT', 'PATCH']:
                # Provide test data for different endpoints
                if '/api/memory/retrieve' in path:
                    data = {"user_id": "test", "query": "test", "limit": 1}
                elif '/api/learning/process_interaction' in path:
                    data = {
                        "user_id": "test", "conversation_id": "test", 
                        "user_message": "test", "assistant_response": "test"
                    }
                elif '/upload/document' in path:
                    return {"status": "skipped", "reason": "file upload endpoint"}
                elif '/v1/chat/completions' in path:
                    data = {
                        "model": "llama3.2:3b",
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 5
                    }
                else:
                    data = {}
            
            # Make request
            if method == 'GET':
                response = requests.get(test_url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(test_url, headers=headers, json=data, timeout=15)
            elif method == 'PUT':
                response = requests.put(test_url, headers=headers, json=data, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(test_url, headers=headers, timeout=10)
            else:
                return {"status": "unsupported_method"}
            
            return {
                "status": "success" if response.status_code < 400 else "error",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "content_length": len(response.content)
            }
        
        except requests.exceptions.Timeout:
            return {"status": "timeout"}
        except requests.exceptions.ConnectionError:
            return {"status": "connection_error"}
        except Exception as e:
            return {"status": "exception", "error": str(e)}
    
    def cross_reference_endpoints(self):
        """Cross-reference declared vs live endpoints."""
        print("🔄 Cross-referencing declared vs live endpoints...")
        
        declared_set = set((ep['method'], ep['path']) for ep in self.declared_endpoints)
        live_routes = self.get_live_routes()
        live_set = set((route['method'], route['path']) for route in live_routes)
        
        # Find differences
        declared_only = declared_set - live_set
        live_only = live_set - declared_set
        common = declared_set & live_set
        
        print(f"📊 Cross-reference results:")
        print(f"   Common endpoints: {len(common)}")
        print(f"   Declared only: {len(declared_only)}")
        print(f"   Live only: {len(live_only)}")
        
        if declared_only:
            print(f"\n⚠️ Declared but not live:")
            for method, path in declared_only:
                print(f"   {method} {path}")
        
        if live_only:
            print(f"\n⚠️ Live but not found in code:")
            for method, path in live_only:
                print(f"   {method} {path}")
        
        return {
            'common': common,
            'declared_only': declared_only,
            'live_only': live_only,
            'live_routes': live_routes
        }
    
    def test_all_endpoints(self, live_routes: List[Dict]):
        """Test all live endpoints."""
        print("🧪 Testing all live endpoints...")
        
        results = {}
        total_endpoints = len(live_routes)
        
        for i, route in enumerate(live_routes, 1):
            method = route['method']
            path = route['path']
            endpoint_key = f"{method} {path}"
            
            print(f"🔄 [{i}/{total_endpoints}] Testing {endpoint_key}...")
            
            result = self.test_endpoint_response(method, path)
            results[endpoint_key] = result
            
            # Brief delay between requests
            time.sleep(0.1)
        
        return results
    
    def generate_report(self, cross_ref: Dict, test_results: Dict):
        """Generate comprehensive validation report."""
        print("\n" + "="*80)
        print("📋 COMPREHENSIVE ENDPOINT VALIDATION REPORT")
        print("="*80)
        
        # File analysis
        print(f"\n📁 PROJECT FILE ANALYSIS:")
        print(f"   Total Python files scanned: {len(self.backend_files)}")
        print(f"   Files with endpoints: {len(self.file_references)}")
        
        print(f"\n📡 ENDPOINT INVENTORY:")
        print(f"   Declared endpoints: {len(self.declared_endpoints)}")
        print(f"   Live endpoints: {len(cross_ref['live_routes'])}")
        print(f"   Common (declared + live): {len(cross_ref['common'])}")
        
        # Test results summary
        success_count = sum(1 for r in test_results.values() if r.get('status') == 'success')
        error_count = sum(1 for r in test_results.values() if r.get('status') == 'error')
        skipped_count = sum(1 for r in test_results.values() if r.get('status') == 'skipped')
        other_count = len(test_results) - success_count - error_count - skipped_count
        
        print(f"\n🧪 ENDPOINT TESTING RESULTS:")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   ⏭️ Skipped: {skipped_count}")
        print(f"   ⚠️ Other: {other_count}")
        print(f"   📊 Success rate: {success_count/len(test_results)*100:.1f}%")
        
        # Detailed results
        print(f"\n🔍 DETAILED TEST RESULTS:")
        for endpoint, result in test_results.items():
            status = result.get('status', 'unknown')
            if status == 'success':
                code = result.get('status_code', 'N/A')
                time_ms = result.get('response_time', 0) * 1000
                print(f"   ✅ {endpoint} → HTTP {code} ({time_ms:.1f}ms)")
            elif status == 'error':
                code = result.get('status_code', 'N/A')
                print(f"   ❌ {endpoint} → HTTP {code}")
            elif status == 'skipped':
                reason = result.get('reason', 'unknown')
                print(f"   ⏭️ {endpoint} → skipped ({reason})")
            else:
                print(f"   ⚠️ {endpoint} → {status}")
        
        # File reference breakdown
        print(f"\n📂 ENDPOINT DISTRIBUTION BY FILE:")
        for file_path, endpoints in self.file_references.items():
            filename = Path(file_path).name
            print(f"   {filename}: {len(endpoints)} endpoints")
            for ep in endpoints:
                print(f"      {ep['method']} {ep['path']} → {ep['function']}()")
        
        # Key endpoints validation
        print(f"\n🎯 KEY MEMORY PIPELINE ENDPOINTS:")
        key_endpoints = [
            'GET /api/pipeline/status',
            'POST /api/memory/retrieve', 
            'POST /api/learning/process_interaction',
            'POST /v1/chat/completions',
            'POST /upload/document'
        ]
        
        for endpoint in key_endpoints:
            if endpoint in test_results:
                result = test_results[endpoint]
                status = result.get('status', 'unknown')
                if status == 'success':
                    print(f"   ✅ {endpoint}")
                else:
                    print(f"   ❌ {endpoint} → {status}")
            else:
                print(f"   ❓ {endpoint} → not found")
        
        print(f"\n🏁 VALIDATION COMPLETE")
        return {
            'total_files': len(self.backend_files),
            'total_declared': len(self.declared_endpoints),
            'total_live': len(cross_ref['live_routes']),
            'test_results': test_results,
            'success_rate': success_count/len(test_results)*100 if test_results else 0
        }

def main():
    """Run comprehensive endpoint validation."""
    print("🚀 COMPREHENSIVE ENDPOINT CROSS-REFERENCE VALIDATOR")
    print(f"🎯 Target: {BASE_URL}")
    print("="*80)
    
    validator = EndpointValidator()
    
    # Step 1: Scan files
    validator.scan_project_files()
    
    # Step 2: Extract endpoints
    validator.extract_all_endpoints()
    
    # Step 3: Cross-reference
    cross_ref = validator.cross_reference_endpoints()
    
    # Step 4: Test endpoints
    test_results = validator.test_all_endpoints(cross_ref['live_routes'])
    
    # Step 5: Generate report
    final_report = validator.generate_report(cross_ref, test_results)
    
    return final_report

if __name__ == "__main__":
    try:
        report = main()
        
        # Final status
        if report['success_rate'] >= 80:
            print("🎉 VALIDATION PASSED: System is highly functional!")
        elif report['success_rate'] >= 60:
            print("✅ VALIDATION PARTIAL: Most endpoints working, some issues.")
        else:
            print("⚠️ VALIDATION CONCERNS: Multiple endpoint issues detected.")
        
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted by user")
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        traceback.print_exc()
