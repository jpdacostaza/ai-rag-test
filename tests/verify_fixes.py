#!/usr/bin/env python3
"""
Final Endpoint Verification Script
=================================
Verifies all endpoints are properly configured and importable after quality fixes.
"""

import sys
import traceback
from typing import List, Dict, Any

def test_router_imports() -> Dict[str, Any]:
    """Test that all routers can be imported successfully"""
    results = {
        "success": [],
        "failures": [],
        "total_tested": 0
    }
    
    routers_to_test = [
        ("routes.gateway", "gateway_router"),
        ("routes.health", "health_router"), 
        ("routes.chat", "chat_router"),
        ("routes.models", "models_router"),
        ("routes.upload", "upload_router"),
        ("routes.debug", "debug_router"),
        ("routes.memory", "memory_router"),
        ("services.model_manager", "router"),
    ]
    
    for module_path, router_name in routers_to_test:
        results["total_tested"] += 1
        try:
            module = __import__(module_path, fromlist=[router_name])
            router = getattr(module, router_name)
            
            # Verify it's a router object
            if hasattr(router, 'routes'):
                endpoint_count = len(router.routes)
                results["success"].append({
                    "module": module_path,
                    "router": router_name,
                    "endpoints": endpoint_count,
                    "prefix": getattr(router, 'prefix', '/'),
                    "tags": getattr(router, 'tags', [])
                })
                print(f"[OK] {module_path}.{router_name} - {endpoint_count} endpoints")
            else:
                results["failures"].append({
                    "module": module_path,
                    "router": router_name,
                    "error": "Not a valid router object"
                })
                print(f"[FAIL] {module_path}.{router_name} - Invalid router")
                
        except Exception as e:
            results["failures"].append({
                "module": module_path, 
                "router": router_name,
                "error": str(e)
            })
            print(f"[FAIL] {module_path}.{router_name} - {str(e)}")
    
    return results

def test_core_imports() -> Dict[str, Any]:
    """Test core application imports"""
    results = {"success": [], "failures": []}
    
    core_imports = [
        "config.config_unified",
        "core.main",
        "services.database_manager", 
        "utilities.enhanced_web_search",
        "utilities.error_patterns"
    ]
    
    for module_name in core_imports:
        try:
            __import__(module_name)
            results["success"].append(module_name)
            print(f"[OK] Core import: {module_name}")
        except Exception as e:
            results["failures"].append({"module": module_name, "error": str(e)})
            print(f"[FAIL] Core import failed: {module_name} - {str(e)}")
    
    return results

def verify_file_organization() -> Dict[str, Any]:
    """Verify critical files are in correct locations"""
    import os
    
    critical_files = [
        "memory/api/enhanced_memory_api.py",
        "memory/functions/memory_filter_function.py", 
        "routes/gateway.py",
        "core/main.py",
        "docker-compose.yml"
    ]
    
    results = {"found": [], "missing": []}
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            results["found"].append({"file": file_path, "size": file_size})
            print(f"[OK] File exists: {file_path} ({file_size} bytes)")
        else:
            results["missing"].append(file_path)
            print(f"[FAIL] Missing: {file_path}")
    
    # Check that removed files are gone
    removed_files = [
        "docker-compose.yml.backup",
        "memory_system"  # directory
    ]
    
    for file_path in removed_files:
        if not os.path.exists(file_path):
            print(f"[OK] Confirmed removed: {file_path}")
        else:
            print(f"[WARN]  Still exists (should be removed): {file_path}")
    
    return results

def main():
    """Run all verification tests"""
    print("=" * 60)
    print("[SEARCH] FINAL ENDPOINT VERIFICATION")
    print("=" * 60)
    
    print("\n Testing Router Imports...")
    router_results = test_router_imports()
    
    print("\n Testing Core Imports...")
    core_results = test_core_imports()
    
    print("\n[FOLDER] Verifying File Organization...")
    file_results = verify_file_organization()
    
    # Summary
    print("\n" + "=" * 60)
    print("[CHART] VERIFICATION SUMMARY")
    print("=" * 60)
    
    total_routers = router_results["total_tested"]
    successful_routers = len(router_results["success"])
    failed_routers = len(router_results["failures"])
    
    print(f" Routers: {successful_routers}/{total_routers} successful")
    
    successful_core = len(core_results["success"])
    failed_core = len(core_results["failures"])
    total_core = successful_core + failed_core
    
    print(f" Core Imports: {successful_core}/{total_core} successful")
    
    found_files = len(file_results["found"])
    missing_files = len(file_results["missing"])
    total_files = found_files + missing_files
    
    print(f"[FOLDER] Critical Files: {found_files}/{total_files} found")
    
    # Overall status
    if failed_routers == 0 and failed_core == 0 and missing_files == 0:
        print("\n ALL VERIFICATIONS PASSED! System is ready.")
        return 0
    else:
        print("\n[WARN]  Some issues found - check details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
