"""
Comprehensive System Analysis and Optimization Check
"""
import requests
import time
import concurrent.futures
import json
import statistics

BASE_URL = "http://localhost:9099"

def comprehensive_system_analysis():
    """Run comprehensive system analysis"""
    print("🔍 Comprehensive System Analysis & Optimization Check")
    print("=" * 70)
    
    results = {
        "health": {},
        "performance": {},
        "cache": {},
        "endpoints": {},
        "error_handling": {},
        "concurrency": {},
        "recommendations": []
    }
    
    # 1. Deep Health Analysis
    print("\n1️⃣ Deep Health Analysis...")
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=10)
        if health.status_code == 200:
            health_data = health.json()
            print(f"   ✅ Main Health: {health_data.get('status', 'unknown')}")
            
            # Check individual services
            databases = health_data.get('databases', {})
            for service, status in databases.items():
                if isinstance(status, dict):
                    service_status = status.get('status', 'unknown')
                    print(f"   📊 {service.title()}: {service_status}")
                    if service_status != 'healthy':
                        results["recommendations"].append(f"Service {service} needs attention")
            
            results["health"]["status"] = "healthy"
            results["health"]["services"] = len(databases)
        else:
            print(f"   ❌ Health check failed: {health.status_code}")
            results["health"]["status"] = "unhealthy"
            results["recommendations"].append("Health endpoint returning errors")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        results["health"]["status"] = "error"
        results["recommendations"].append("Health endpoint unreachable")
    
    # 2. Performance Benchmarking
    print("\n2️⃣ Performance Benchmarking...")
    
    performance_tests = [
        {"endpoint": "/health", "method": "GET", "iterations": 10},
        {"endpoint": "/v1/models", "method": "GET", "iterations": 5},
        {"endpoint": "/debug/cache", "method": "GET", "iterations": 5},
        {"endpoint": "/pipelines", "method": "GET", "iterations": 3}
    ]
    
    for test in performance_tests:
        endpoint = test["endpoint"]
        iterations = test["iterations"]
        times = []
        
        print(f"   🔄 Testing {endpoint} ({iterations} iterations)...")
        
        for i in range(iterations):
            start = time.time()
            try:
                if test["method"] == "GET":
                    resp = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                duration = (time.time() - start) * 1000
                
                if resp.status_code == 200:
                    times.append(duration)
                else:
                    print(f"      ⚠️  Iteration {i+1}: {resp.status_code}")
            except Exception as e:
                print(f"      ❌ Iteration {i+1}: {str(e)[:30]}...")
        
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"      📊 Avg: {avg_time:.2f}ms, Min: {min_time:.2f}ms, Max: {max_time:.2f}ms")
            
            results["performance"][endpoint] = {
                "avg": avg_time,
                "min": min_time,
                "max": max_time,
                "samples": len(times)
            }
            
            # Performance recommendations
            if avg_time > 1000:
                results["recommendations"].append(f"{endpoint} is slow (avg {avg_time:.0f}ms)")
            elif avg_time > 500:
                results["recommendations"].append(f"{endpoint} could be optimized (avg {avg_time:.0f}ms)")
    
    # 3. Advanced Cache Analysis
    print("\n3️⃣ Advanced Cache Analysis...")
    
    initial_cache = requests.get(f"{BASE_URL}/debug/cache").json()
    print(f"   📊 Initial cache: {initial_cache['hit_count']} hits, {initial_cache['miss_count']} misses")
    
    # Test cache with different scenarios
    cache_scenarios = [
        {"user": "cache_test_1", "message": "Simple test", "description": "Basic cache test"},
        {"user": "cache_test_1", "message": "Simple test", "description": "Same user, same message (should hit)"},
        {"user": "cache_test_2", "message": "Simple test", "description": "Different user, same message (should miss)"},
        {"user": "cache_test_1", "message": "Different message", "description": "Same user, different message (should miss)"},
        {"user": "cache_test_1", "message": "Simple test", "description": "Original combo again (should hit)"}
    ]
    
    cache_results = []
    
    for i, scenario in enumerate(cache_scenarios):
        print(f"   {i+1}. {scenario['description']}")
        
        start = time.time()
        try:
            resp = requests.post(f"{BASE_URL}/chat", json={
                "user_id": scenario["user"],
                "message": scenario["message"],
                "model": "llama3.2:3b"
            }, timeout=30)
            
            duration = (time.time() - start) * 1000
            
            if resp.status_code == 200:
                cache_results.append({"scenario": i+1, "duration": duration, "status": "success"})
                
                if duration < 100:
                    print(f"      🚀 Very fast: {duration:.2f}ms (likely cached)")
                elif duration < 1000:
                    print(f"      ⚡ Fast: {duration:.2f}ms")
                else:
                    print(f"      🐌 Slow: {duration:.2f}ms (likely uncached)")
            else:
                print(f"      ❌ Failed: {resp.status_code}")
                cache_results.append({"scenario": i+1, "duration": duration, "status": "failed"})
        except Exception as e:
            print(f"      ❌ Error: {str(e)[:40]}...")
            cache_results.append({"scenario": i+1, "duration": 0, "status": "error"})
        
        time.sleep(1)  # Brief pause between requests
    
    # Analyze cache effectiveness
    final_cache = requests.get(f"{BASE_URL}/debug/cache").json()
    hits_gained = final_cache['hit_count'] - initial_cache['hit_count']
    misses_gained = final_cache['miss_count'] - initial_cache['miss_count']
    
    print(f"   📈 Cache analysis: +{hits_gained} hits, +{misses_gained} misses")
    
    results["cache"] = {
        "hits_gained": hits_gained,
        "misses_gained": misses_gained,
        "hit_rate": final_cache.get('hit_rate', '0%'),
        "cache_size": final_cache.get('size', 0)
    }
    
    # Expected: scenarios 2 and 5 should be cache hits
    expected_hits = 2
    if hits_gained >= expected_hits:
        print(f"   ✅ Cache working optimally ({hits_gained}/{expected_hits} expected hits)")
    elif hits_gained > 0:
        print(f"   ⚠️  Cache partially working ({hits_gained}/{expected_hits} expected hits)")
        results["recommendations"].append("Cache hit rate could be improved")
    else:
        print(f"   ❌ Cache not working ({hits_gained}/{expected_hits} expected hits)")
        results["recommendations"].append("Cache system needs debugging")
    
    # 4. Endpoint Coverage Test
    print("\n4️⃣ Endpoint Coverage Test...")
    
    endpoints_to_test = [
        {"url": "/", "method": "GET", "expected": 200},
        {"url": "/health", "method": "GET", "expected": 200},
        {"url": "/upload/health", "method": "GET", "expected": 200},
        {"url": "/v1/models", "method": "GET", "expected": 200},
        {"url": "/pipelines", "method": "GET", "expected": 200},
        {"url": "/debug/cache", "method": "GET", "expected": 200},
        {"url": "/debug/config", "method": "GET", "expected": 200},
        {"url": "/nonexistent", "method": "GET", "expected": 404}
    ]
    
    endpoint_results = []
    
    for endpoint in endpoints_to_test:
        try:
            resp = requests.get(f"{BASE_URL}{endpoint['url']}", timeout=10)
            status = "✅" if resp.status_code == endpoint["expected"] else "❌"
            print(f"   {status} {endpoint['url']}: {resp.status_code} (expected {endpoint['expected']})")
            
            endpoint_results.append({
                "url": endpoint["url"],
                "actual": resp.status_code,
                "expected": endpoint["expected"],
                "status": "pass" if resp.status_code == endpoint["expected"] else "fail"
            })
        except Exception as e:
            print(f"   ❌ {endpoint['url']}: Error - {str(e)[:30]}...")
            endpoint_results.append({
                "url": endpoint["url"],
                "actual": "error",
                "expected": endpoint["expected"],
                "status": "error"
            })
    
    passed_endpoints = [r for r in endpoint_results if r["status"] == "pass"]
    results["endpoints"] = {
        "total": len(endpoint_results),
        "passed": len(passed_endpoints),
        "success_rate": len(passed_endpoints) / len(endpoint_results) * 100
    }
    
    # 5. Error Handling Deep Test
    print("\n5️⃣ Error Handling Deep Test...")
    
    error_tests = [
        {"payload": {"user_id": "", "message": "test", "model": "llama3.2:3b"}, "desc": "Empty user_id"},
        {"payload": {"user_id": "test", "message": "", "model": "llama3.2:3b"}, "desc": "Empty message"},
        {"payload": {"user_id": "test", "message": "test"}, "desc": "Missing model"},
        {"payload": {"message": "test", "model": "llama3.2:3b"}, "desc": "Missing user_id"},
        {"payload": {}, "desc": "Empty payload"}
    ]
    
    error_handling_score = 0
    
    for test in error_tests:
        try:
            resp = requests.post(f"{BASE_URL}/chat", json=test["payload"], timeout=10)
            if 400 <= resp.status_code < 500:  # Client error expected
                print(f"   ✅ {test['desc']}: {resp.status_code} (good validation)")
                error_handling_score += 1
            else:
                print(f"   ⚠️  {test['desc']}: {resp.status_code} (unexpected)")
        except Exception as e:
            print(f"   ❌ {test['desc']}: {str(e)[:30]}...")
    
    results["error_handling"] = {
        "score": error_handling_score,
        "total": len(error_tests),
        "percentage": error_handling_score / len(error_tests) * 100
    }
    
    # 6. Concurrency Test
    print("\n6️⃣ Concurrency Test...")
    
    def make_concurrent_request(i):
        try:
            start = time.time()
            resp = requests.get(f"{BASE_URL}/health", timeout=15)
            duration = (time.time() - start) * 1000
            return {"id": i, "status": resp.status_code, "duration": duration}
        except Exception as e:
            return {"id": i, "status": "error", "duration": 0, "error": str(e)}
    
    print("   🔄 Running 10 concurrent health checks...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        concurrent_results = list(executor.map(make_concurrent_request, range(10)))
    
    successful_concurrent = [r for r in concurrent_results if r["status"] == 200]
    
    if successful_concurrent:
        avg_concurrent_time = statistics.mean([r["duration"] for r in successful_concurrent])
        print(f"   📊 Concurrent results: {len(successful_concurrent)}/10 successful, avg {avg_concurrent_time:.2f}ms")
        
        results["concurrency"] = {
            "successful": len(successful_concurrent),
            "total": 10,
            "success_rate": len(successful_concurrent) / 10 * 100,
            "avg_duration": avg_concurrent_time
        }
        
        if len(successful_concurrent) < 8:
            results["recommendations"].append("Concurrency handling could be improved")
    
    # 7. Generate Final Report
    print("\n7️⃣ Analysis Summary...")
    
    overall_score = 0
    max_score = 0
    
    # Health score
    if results["health"]["status"] == "healthy":
        overall_score += 20
    max_score += 20
    
    # Performance score (based on health endpoint performance)
    if "/health" in results["performance"]:
        health_perf = results["performance"]["/health"]["avg"]
        if health_perf < 50:
            overall_score += 20
        elif health_perf < 100:
            overall_score += 15
        elif health_perf < 200:
            overall_score += 10
    max_score += 20
    
    # Cache score
    if results["cache"]["hits_gained"] >= 2:
        overall_score += 20
    elif results["cache"]["hits_gained"] >= 1:
        overall_score += 10
    max_score += 20
    
    # Endpoint score
    if results["endpoints"]["success_rate"] >= 90:
        overall_score += 20
    elif results["endpoints"]["success_rate"] >= 75:
        overall_score += 15
    max_score += 20
    
    # Error handling score
    if results["error_handling"]["percentage"] >= 80:
        overall_score += 20
    elif results["error_handling"]["percentage"] >= 60:
        overall_score += 15
    max_score += 20
    
    final_percentage = (overall_score / max_score) * 100
    
    print(f"\n📊 OVERALL SYSTEM SCORE: {overall_score}/{max_score} ({final_percentage:.1f}%)")
    
    if final_percentage >= 90:
        print("   🏆 EXCELLENT - System is production-ready and highly optimized")
    elif final_percentage >= 75:
        print("   ✅ GOOD - System is solid with minor optimization opportunities")
    elif final_percentage >= 60:
        print("   ⚠️  FAIR - System works but needs improvements")
    else:
        print("   ❌ POOR - System needs significant improvements")
    
    # Recommendations
    if results["recommendations"]:
        print(f"\n💡 Recommendations ({len(results['recommendations'])}):")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"   {i}. {rec}")
    else:
        print(f"\n✅ No specific recommendations - system is well optimized!")
    
    # Save detailed results
    with open("comprehensive_analysis_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: comprehensive_analysis_results.json")
    
    return final_percentage >= 75

if __name__ == "__main__":
    is_optimized = comprehensive_system_analysis()
    
    if is_optimized:
        print("\n🎯 SYSTEM STATUS: OPTIMIZED ✅")
    else:
        print("\n🔧 SYSTEM STATUS: NEEDS OPTIMIZATION ⚠️")
