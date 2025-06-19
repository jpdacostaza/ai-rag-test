#!/usr/bin/env python3
"""
Comprehensive Integration Test for Startup Memory Health + Cache Manager + Backend
Tests all the newly added features working together in realistic scenarios.
"""

import sys
import os
import time
import json
import requests
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from human_logging import init_logging, log_service_status

def test_startup_memory_health():
    """Test the standalone startup memory health check."""
    print("=" * 60)
    print("🏁 Testing Startup Memory Health Check")
    print("=" * 60)
    
    try:
        from startup_memory_health import startup_memory_health_check
        
        start_time = time.time()
        result = startup_memory_health_check()
        duration = time.time() - start_time
        
        print(f"✅ Health check completed in {duration:.2f}s")
        print(f"📊 Overall Status: {result['overall_status']}")
        print(f"🔴 Redis: {result['redis']['status']}")
        print(f"🟣 ChromaDB: {result['chromadb']['status']}")
        
        if result['redis']['status'] == 'healthy':
            details = result['redis']['details']
            print(f"   └─ Cache keys: {details.get('cache_keys', 0)}")
            print(f"   └─ Version: {details.get('version', 'unknown')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Startup health check failed: {e}")
        return None

def test_cache_manager_integration():
    """Test cache manager with the enhanced logging and validation."""
    print("\n" + "=" * 60)
    print("⚡ Testing Cache Manager Integration")
    print("=" * 60)
    
    try:
        from database import get_cache_manager
        
        cache_manager = get_cache_manager()
        if not cache_manager:
            print("❌ Cache manager not available")
            return False
        
        print("✅ Cache manager available")
        
        # Test cache operations with logging
        test_scenarios = [
            ("Basic text response", "Hello, how can I help you today?"),
            ("Long response", "This is a longer response that contains multiple sentences. " * 5),
            ("Special characters", "Response with émojis 🎉 and special chars: @#$%^&*()"),
        ]
        
        results = {}
        
        for scenario, response in test_scenarios:
            key = f"integration_test_{scenario.lower().replace(' ', '_')}"
            
            print(f"\n🧪 Testing: {scenario}")
            
            # Test set operation
            success = cache_manager.set_with_validation(key, response, ttl=30)
            print(f"   Set: {'✅' if success else '❌'}")
            
            # Test get operation
            retrieved = cache_manager.get_with_validation(key)
            get_success = retrieved == response
            print(f"   Get: {'✅' if get_success else '❌'}")
            
            # Clean up
            cache_manager.redis_client.delete(key)
            
            results[scenario] = success and get_success
        
        # Test cache stats
        stats = cache_manager.get_cache_stats()
        print(f"\n📈 Cache Statistics:")
        print(f"   Total keys: {stats.get('total_keys', 0)}")
        print(f"   Version: {stats.get('version', 'unknown')}")
        print(f"   Memory usage: {stats.get('memory_usage', 'unknown')}")
        
        return all(results.values())
        
    except Exception as e:
        print(f"❌ Cache manager test failed: {e}")
        return False

def test_backend_health_endpoints():
    """Test the backend health endpoints including the new memory endpoint."""
    print("\n" + "=" * 60)
    print("🌐 Testing Backend Health Endpoints")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    endpoints_to_test = [
        "/health",
        "/health/simple", 
        "/health/detailed",
        "/health/redis",
        "/health/chromadb",
        "/health/memory"  # New endpoint
    ]
    
    results = {}
    
    for endpoint in endpoints_to_test:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\n🔍 Testing: {endpoint}")
            
            start_time = time.time()
            response = requests.get(url, timeout=30)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                print(f"   Status: ✅ 200 OK ({duration:.2f}s)")
                data = response.json()
                
                # Show key information for each endpoint
                if endpoint == "/health":
                    print(f"   Summary: {data.get('summary', 'N/A')}")
                    if 'cache' in data:
                        cache_info = data['cache']
                        print(f"   Cache keys: {cache_info.get('total_keys', 0)}")
                
                elif endpoint == "/health/memory":
                    health = data.get('health', {})
                    print(f"   Overall: {health.get('overall_status', 'unknown')}")
                    print(f"   Redis: {health.get('redis', {}).get('status', 'unknown')}")
                    print(f"   ChromaDB: {health.get('chromadb', {}).get('status', 'unknown')}")
                
                elif endpoint == "/health/detailed":
                    print(f"   Overall: {data.get('overall_status', 'unknown')}")
                    services = data.get('services', {})
                    print(f"   Services: {len(services)} monitored")
                
                results[endpoint] = True
            else:
                print(f"   Status: ❌ {response.status_code}")
                results[endpoint] = False
                
        except requests.exceptions.ConnectionError:
            print(f"   Status: ❌ Connection failed (backend not running?)")
            results[endpoint] = False
        except Exception as e:
            print(f"   Status: ❌ Error: {e}")
            results[endpoint] = False
    
    return results

def test_memory_system_integration():
    """Test the complete memory system integration."""
    print("\n" + "=" * 60)
    print("🧠 Testing Complete Memory System Integration")
    print("=" * 60)
    
    try:
        from startup_memory_health import initialize_memory_systems
        
        print("🔄 Running complete memory system initialization...")
        start_time = time.time()
        success = initialize_memory_systems()
        duration = time.time() - start_time
        
        print(f"📊 Initialization: {'✅ Success' if success else '❌ Failed'} ({duration:.2f}s)")
        
        # Test that systems are working after initialization
        if success:
            print("\n🧪 Testing post-initialization functionality...")
            
            # Test cache manager is available and working
            from database import get_cache_manager
            cache_manager = get_cache_manager()
            
            if cache_manager:
                # Quick functionality test
                test_key = "post_init_test"
                test_value = f"test_{int(time.time())}"
                
                cache_manager.set_with_validation(test_key, test_value, ttl=10)
                retrieved = cache_manager.get_with_validation(test_key)
                cache_manager.redis_client.delete(test_key)
                
                cache_working = retrieved == test_value
                print(f"   Cache operations: {'✅' if cache_working else '❌'}")
                
                return cache_working
            else:
                print("   ❌ Cache manager not available after initialization")
                return False
        
        return success
        
    except Exception as e:
        print(f"❌ Memory system integration test failed: {e}")
        return False

def test_real_world_scenario():
    """Test a realistic scenario combining all features."""
    print("\n" + "=" * 60)
    print("🌍 Testing Real-World Scenario")
    print("=" * 60)
    
    try:
        # Simulate a chat request that would use the cache
        base_url = "http://localhost:8001"
        
        chat_payload = {
            "messages": [
                {"role": "user", "content": "What is the capital of France?"}
            ],
            "model": "gpt-4o-mini",
            "max_tokens": 100
        }
        
        print("💬 Sending chat request to test cache integration...")
        
        # First request (should miss cache)
        start_time = time.time()
        response1 = requests.post(f"{base_url}/v1/chat/completions", 
                                 json=chat_payload, 
                                 timeout=30)
        duration1 = time.time() - start_time
        
        if response1.status_code == 200:
            print(f"   First request: ✅ {response1.status_code} ({duration1:.2f}s)")
            
            # Second identical request (should hit cache if working)
            start_time = time.time()
            response2 = requests.post(f"{base_url}/v1/chat/completions", 
                                     json=chat_payload, 
                                     timeout=30)
            duration2 = time.time() - start_time
            
            if response2.status_code == 200:
                print(f"   Second request: ✅ {response2.status_code} ({duration2:.2f}s)")
                
                # Check if second request was faster (indicating cache hit)
                if duration2 < duration1 * 0.8:  # 20% faster suggests cache hit
                    print("   🎯 Cache hit detected (faster response)")
                else:
                    print("   ⏱️ Similar timing (cache may not have hit)")
                
                return True
            else:
                print(f"   Second request: ❌ {response2.status_code}")
                return False
        else:
            print(f"   First request: ❌ {response1.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Backend not available for real-world test")
        return False
    except Exception as e:
        print(f"   ❌ Real-world test failed: {e}")
        return False

def main():
    """Run comprehensive integration tests."""
    init_logging(level="INFO")
    
    print("🧪 COMPREHENSIVE INTEGRATION TEST")
    print("Testing all newly added memory/cache features together")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Track results
    test_results = {}
    
    # Run all tests
    test_results["Startup Memory Health"] = test_startup_memory_health() is not None
    test_results["Cache Manager Integration"] = test_cache_manager_integration()
    test_results["Backend Health Endpoints"] = all(test_backend_health_endpoints().values())
    test_results["Memory System Integration"] = test_memory_system_integration()
    test_results["Real-World Scenario"] = test_real_world_scenario()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print("\n" + "-" * 60)
    print(f"📊 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Integration is working perfectly.")
        log_service_status("INTEGRATION_TEST", "ready", f"All {total} integration tests passed successfully")
    elif passed > total * 0.7:
        print("⚠️ Most tests passed, minor issues detected.")
        log_service_status("INTEGRATION_TEST", "degraded", f"{passed}/{total} integration tests passed")
    else:
        print("❌ Multiple failures detected, integration needs attention.")
        log_service_status("INTEGRATION_TEST", "failed", f"Only {passed}/{total} integration tests passed")
    
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
