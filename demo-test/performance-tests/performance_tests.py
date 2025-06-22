#!/usr/bin/env python3
"""
Performance & Load Test Suite
=============================

Comprehensive performance testing for the backend system:
- Response time measurement under various loads
- Concurrent request handling
- Memory and resource usage patterns
- Database performance under load
- Cache performance verification
- Streaming response performance
- Error rate analysis under stress
- Recovery testing after load spikes

This module stress-tests the system to ensure it performs well under real-world conditions.
"""

import asyncio
import json
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Tuple

import requests


class PerformanceTestSuite:
    """Comprehensive performance testing suite."""
    
    def __init__(self, base_url: str = "http://localhost:8001", 
                 api_key: str = "f2b985dd-219f-45b1-a90e-170962cc7082"):
        self.base_url = base_url
        self.api_key = api_key
        self.results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        })
    
    def make_single_request(self, endpoint: str, payload: Dict = None, method: str = "GET") -> Dict:
        """Make a single timed request."""
        start_time = time.time()
        try:
            if method == "GET":
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=30)
            else:
                response = self.session.post(f"{self.base_url}{endpoint}", json=payload, timeout=30)
            
            duration = time.time() - start_time
            
            return {
                "success": True,
                "status_code": response.status_code,
                "duration": duration,
                "response_size": len(response.content),
                "timestamp": time.time()
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "duration": duration,
                "timestamp": time.time()
            }
    
    def test_response_times(self):
        """Test basic response times for key endpoints."""
        print("⏱️  Testing Response Times...")
        
        endpoints = [
            ("/health/simple", None, "GET"),
            ("/health", None, "GET"),
            ("/v1/models", None, "GET"),
            ("/chat", {"user_id": "perf_test", "message": "Hello"}, "POST"),
            ("/chat", {"user_id": "perf_test", "message": "What is 2+2?"}, "POST"),
            ("/chat", {"user_id": "perf_test", "message": "What time is it?"}, "POST"),
        ]
        
        for endpoint, payload, method in endpoints:
            measurements = []
            
            # Take 10 measurements for each endpoint
            for i in range(10):
                result = self.make_single_request(endpoint, payload, method)
                if result["success"]:
                    measurements.append(result["duration"])
                time.sleep(0.1)  # Small delay between requests
            
            if measurements:
                avg_time = statistics.mean(measurements)
                min_time = min(measurements)
                max_time = max(measurements)
                median_time = statistics.median(measurements)
                
                performance_result = {
                    "test": f"Response Time - {method} {endpoint}",
                    "measurements": len(measurements),
                    "average_time": f"{avg_time:.3f}s",
                    "min_time": f"{min_time:.3f}s",
                    "max_time": f"{max_time:.3f}s",
                    "median_time": f"{median_time:.3f}s",
                    "acceptable": avg_time < 5.0,  # 5 second threshold
                    "timestamp": datetime.now().isoformat()
                }
                
                self.results.append(performance_result)
                
                status = "✅" if performance_result["acceptable"] else "⚠️"
                print(f"  {status} {method} {endpoint}: {avg_time:.3f}s avg (min: {min_time:.3f}s, max: {max_time:.3f}s)")
            else:
                print(f"  ❌ {method} {endpoint}: No successful measurements")
    
    def test_concurrent_requests(self):
        """Test system under concurrent load."""
        print("🔀 Testing Concurrent Request Handling...")
        
        def concurrent_chat_request(user_id: int) -> Dict:
            """Single concurrent request function."""
            return self.make_single_request(
                "/chat",
                {"user_id": f"concurrent_user_{user_id}", "message": f"Concurrent test {user_id}"},
                "POST"
            )
        
        # Test different concurrency levels
        concurrency_levels = [5, 10, 20]
        
        for concurrency in concurrency_levels:
            print(f"  Testing {concurrency} concurrent requests...")
            
            start_time = time.time()
            results = []
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                # Submit all requests
                futures = [executor.submit(concurrent_chat_request, i) for i in range(concurrency)]
                
                # Collect results
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        results.append({"success": False, "error": str(e), "duration": 0})
            
            total_time = time.time() - start_time
            
            # Analyze results
            successful = [r for r in results if r["success"]]
            failed = len(results) - len(successful)
            
            if successful:
                avg_response_time = statistics.mean([r["duration"] for r in successful])
                max_response_time = max([r["duration"] for r in successful])
                throughput = len(successful) / total_time
            else:
                avg_response_time = 0
                max_response_time = 0
                throughput = 0
            
            concurrency_result = {
                "test": f"Concurrent Load - {concurrency} requests",
                "total_requests": concurrency,
                "successful_requests": len(successful),
                "failed_requests": failed,
                "success_rate": f"{(len(successful)/concurrency*100):.1f}%",
                "total_time": f"{total_time:.2f}s",
                "average_response_time": f"{avg_response_time:.3f}s",
                "max_response_time": f"{max_response_time:.3f}s",
                "throughput": f"{throughput:.1f} req/s",
                "acceptable": failed == 0 and avg_response_time < 10.0,
                "timestamp": datetime.now().isoformat()
            }
            
            self.results.append(concurrency_result)
            
            status = "✅" if concurrency_result["acceptable"] else "⚠️"
            print(f"    {status} {len(successful)}/{concurrency} successful, {throughput:.1f} req/s, {avg_response_time:.3f}s avg")
    
    def test_sustained_load(self):
        """Test system under sustained load over time."""
        print("⏳ Testing Sustained Load (60 seconds)...")
        
        duration = 60  # 60 seconds
        request_interval = 1  # 1 request per second
        
        start_time = time.time()
        end_time = start_time + duration
        request_count = 0
        results = []
        
        while time.time() < end_time:
            result = self.make_single_request(
                "/chat",
                {"user_id": f"sustained_user_{request_count}", "message": f"Sustained test {request_count}"},
                "POST"
            )
            results.append(result)
            request_count += 1
            
            # Wait for next interval
            next_request_time = start_time + (request_count * request_interval)
            sleep_time = next_request_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Analyze sustained load results
        successful = [r for r in results if r["success"]]
        failed = len(results) - len(successful)
        
        if successful:
            response_times = [r["duration"] for r in successful]
            avg_response_time = statistics.mean(response_times)
            response_time_std = statistics.stdev(response_times) if len(response_times) > 1 else 0
            
            # Check for performance degradation over time
            first_half = response_times[:len(response_times)//2]
            second_half = response_times[len(response_times)//2:]
            
            if first_half and second_half:
                first_half_avg = statistics.mean(first_half)
                second_half_avg = statistics.mean(second_half)
                degradation = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0
            else:
                degradation = 0
        else:
            avg_response_time = 0
            response_time_std = 0
            degradation = 0
        
        sustained_result = {
            "test": "Sustained Load",
            "duration": f"{duration}s",
            "total_requests": request_count,
            "successful_requests": len(successful),
            "failed_requests": failed,
            "success_rate": f"{(len(successful)/request_count*100):.1f}%" if request_count > 0 else "0%",
            "average_response_time": f"{avg_response_time:.3f}s",
            "response_time_std": f"{response_time_std:.3f}s",
            "performance_degradation": f"{degradation:.1f}%",
            "stable_performance": abs(degradation) < 20,  # Less than 20% degradation
            "timestamp": datetime.now().isoformat()
        }
        
        self.results.append(sustained_result)
        
        status = "✅" if sustained_result["stable_performance"] and failed == 0 else "⚠️"
        print(f"  {status} {len(successful)}/{request_count} successful over {duration}s")
        print(f"    Avg response: {avg_response_time:.3f}s, Degradation: {degradation:.1f}%")
    
    def test_cache_performance(self):
        """Test cache performance with repeated requests."""
        print("💾 Testing Cache Performance...")
        
        # Test message that should be cacheable
        cache_test_message = "What is 2+2?"
        user_id = "cache_perf_test"
        
        # First request (cache miss)
        print("  Testing cache miss...")
        first_result = self.make_single_request(
            "/chat",
            {"user_id": user_id, "message": cache_test_message},
            "POST"
        )
        
        time.sleep(1)  # Brief pause
        
        # Second request (should be cache hit)
        print("  Testing cache hit...")
        second_result = self.make_single_request(
            "/chat",
            {"user_id": user_id, "message": cache_test_message},
            "POST"
        )
        
        if first_result["success"] and second_result["success"]:
            first_time = first_result["duration"]
            second_time = second_result["duration"]
            speedup = (first_time - second_time) / first_time * 100 if first_time > 0 else 0
            
            cache_result = {
                "test": "Cache Performance",
                "first_request_time": f"{first_time:.3f}s",
                "second_request_time": f"{second_time:.3f}s",
                "speedup_percentage": f"{speedup:.1f}%",
                "cache_effective": speedup > 10,  # At least 10% speedup
                "timestamp": datetime.now().isoformat()
            }
            
            self.results.append(cache_result)
            
            status = "✅" if cache_result["cache_effective"] else "⚠️"
            print(f"  {status} Cache speedup: {speedup:.1f}% ({first_time:.3f}s → {second_time:.3f}s)")
        else:
            print("  ❌ Cache test failed - requests unsuccessful")
    
    def test_memory_leak_detection(self):
        """Test for potential memory leaks with many requests."""
        print("🧠 Testing Memory Leak Detection...")
        
        # Send many requests and monitor response times for degradation
        num_requests = 50
        response_times = []
        
        for i in range(num_requests):
            result = self.make_single_request(
                "/chat",
                {"user_id": f"memory_test_{i}", "message": f"Memory test {i}"},
                "POST"
            )
            
            if result["success"]:
                response_times.append(result["duration"])
            
            if i % 10 == 0:
                print(f"    Completed {i+1}/{num_requests} requests...")
        
        if len(response_times) >= 20:  # Need enough data points
            # Analyze trend in response times
            first_quarter = response_times[:len(response_times)//4]
            last_quarter = response_times[-len(response_times)//4:]
            
            first_avg = statistics.mean(first_quarter)
            last_avg = statistics.mean(last_quarter)
            
            trend_increase = ((last_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
            
            memory_result = {
                "test": "Memory Leak Detection",
                "total_requests": num_requests,
                "successful_requests": len(response_times),
                "first_quarter_avg": f"{first_avg:.3f}s",
                "last_quarter_avg": f"{last_avg:.3f}s",
                "response_time_trend": f"{trend_increase:.1f}%",
                "potential_leak": trend_increase > 50,  # More than 50% increase
                "timestamp": datetime.now().isoformat()
            }
            
            self.results.append(memory_result)
            
            status = "⚠️" if memory_result["potential_leak"] else "✅"
            print(f"  {status} Response time trend: {trend_increase:.1f}% increase over {num_requests} requests")
        else:
            print("  ❌ Insufficient data for memory leak analysis")
    
    def test_error_recovery(self):
        """Test system recovery after error conditions."""
        print("🔄 Testing Error Recovery...")
        
        # Send some invalid requests to trigger errors
        print("  Triggering error conditions...")
        for i in range(5):
            self.make_single_request("/chat", {"invalid": "data"}, "POST")
        
        time.sleep(2)  # Brief recovery time
        
        # Test if system recovers with valid requests
        print("  Testing recovery...")
        recovery_results = []
        for i in range(5):
            result = self.make_single_request(
                "/chat",
                {"user_id": f"recovery_test_{i}", "message": "Recovery test"},
                "POST"
            )
            recovery_results.append(result)
        
        successful_recovery = sum(1 for r in recovery_results if r["success"])
        
        recovery_result = {
            "test": "Error Recovery",
            "recovery_requests": len(recovery_results),
            "successful_recovery": successful_recovery,
            "recovery_rate": f"{(successful_recovery/len(recovery_results)*100):.1f}%",
            "full_recovery": successful_recovery == len(recovery_results),
            "timestamp": datetime.now().isoformat()
        }
        
        self.results.append(recovery_result)
        
        status = "✅" if recovery_result["full_recovery"] else "⚠️"
        print(f"  {status} Recovery rate: {recovery_result['recovery_rate']}")
    
    def run_all_performance_tests(self):
        """Run all performance tests and generate report."""
        print("🚀 Starting Comprehensive Performance & Load Tests")
        print("=" * 60)
        print("⚠️  Warning: These tests will generate significant load on the system")
        print("=" * 60)
        
        # Run all performance test suites
        self.test_response_times()
        print()
        self.test_concurrent_requests()
        print()
        self.test_sustained_load()
        print()
        self.test_cache_performance()
        print()
        self.test_memory_leak_detection()
        print()
        self.test_error_recovery()
        
        # Generate summary report
        total_tests = len(self.results)
        acceptable_tests = sum(1 for r in self.results if r.get("acceptable", True) or r.get("cache_effective", True) or r.get("full_recovery", True))
        performance_issues = total_tests - acceptable_tests
        
        print("\n" + "=" * 60)
        print("🚀 PERFORMANCE TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Performance Tests: {total_tests}")
        print(f"Acceptable Performance: {acceptable_tests}")
        print(f"Performance Issues: {performance_issues}")
        print(f"Performance Score: {(acceptable_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        # Show performance issues
        issues = [r for r in self.results if not (r.get("acceptable", True) and r.get("cache_effective", True) and r.get("full_recovery", True))]
        if issues:
            print("\n⚠️  PERFORMANCE ISSUES DETECTED:")
            for result in issues:
                test_name = result.get('test', 'Unknown test')
                if not result.get("acceptable", True):
                    print(f"  - {test_name}: Poor response times or success rate")
                if not result.get("cache_effective", True) and "Cache" in test_name:
                    print(f"  - {test_name}: Cache not providing expected speedup")
                if not result.get("full_recovery", True) and "Recovery" in test_name:
                    print(f"  - {test_name}: System not recovering properly from errors")
        
        # Performance recommendations
        print("\n💡 PERFORMANCE RECOMMENDATIONS:")
        avg_response_times = []
        for result in self.results:
            if "average_time" in result:
                try:
                    avg_time = float(result["average_time"].rstrip("s"))
                    avg_response_times.append(avg_time)
                except:
                    pass
        
        if avg_response_times:
            overall_avg = statistics.mean(avg_response_times)
            if overall_avg > 2.0:
                print("  - Consider optimizing database queries and caching")
            if overall_avg > 5.0:
                print("  - Response times are high - review system resources")
            else:
                print("  - Response times are within acceptable range")
        
        # Save detailed report
        report_file = f"demo-test/performance_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w') as f:
                json.dump({
                    "summary": {
                        "total_tests": total_tests,
                        "acceptable_performance": acceptable_tests,
                        "performance_issues": performance_issues,
                        "performance_score": f"{(acceptable_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
                    },
                    "results": self.results
                }, f, indent=2, default=str)
            print(f"\n📄 Detailed performance report saved: {report_file}")
        except Exception as e:
            print(f"\n⚠️  Could not save report: {e}")
        
        print("\n🏁 Performance tests completed!")
        return performance_issues == 0


def main():
    """Run performance tests."""
    suite = PerformanceTestSuite()
    success = suite.run_all_performance_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
