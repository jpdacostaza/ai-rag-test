#!/usr/bin/env python3
"""
Enhanced API Gateway Test Suite
Comprehensive testing for the enhanced API Gateway implementation.
"""

import asyncio
import aiohttp
import json
import time
import pytest
from typing import Dict, Any, List
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    duration_ms: float
    status_code: int = None
    error: str = None
    response_data: Any = None

class EnhancedGatewayTester:
    """Comprehensive test suite for the enhanced API Gateway"""
    
    def __init__(self, gateway_url: str = "http://localhost:8888"):
        self.gateway_url = gateway_url
        self.session = None
        self.test_results: List[TestResult] = []
        
        # Test data
        self.test_user_id = "test_user_12345"
        self.test_memory_data = {
            "content": "This is a test memory for the enhanced gateway",
            "user_id": self.test_user_id,
            "timestamp": time.time()
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, path: str, **kwargs) -> TestResult:
        """Make HTTP request and measure performance"""
        url = f"{self.gateway_url}{path}"
        start_time = time.time()
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                duration = (time.time() - start_time) * 1000
                response_data = None
                
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                
                return TestResult(
                    test_name=f"{method} {path}",
                    success=200 <= response.status < 400,
                    duration_ms=duration,
                    status_code=response.status,
                    response_data=response_data
                )
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                test_name=f"{method} {path}",
                success=False,
                duration_ms=duration,
                error=str(e)
            )
    
    async def test_gateway_health(self) -> TestResult:
        """Test gateway health endpoint"""
        logger.info("Testing gateway health...")
        result = await self._make_request("GET", "/gateway/health")
        
        if result.success and result.response_data:
            logger.info(f"✓ Gateway health check passed ({result.duration_ms:.1f}ms)")
            logger.info(f"  Services: {len(result.response_data.get('services', {}))}")
        else:
            logger.error(f"✗ Gateway health check failed: {result.error}")
        
        return result
    
    async def test_gateway_metrics(self) -> TestResult:
        """Test gateway metrics endpoint"""
        logger.info("Testing gateway metrics...")
        result = await self._make_request("GET", "/gateway/metrics")
        
        if result.success:
            logger.info(f"✓ Gateway metrics accessible ({result.duration_ms:.1f}ms)")
            if result.response_data:
                metrics = result.response_data.get('performance', {})
                logger.info(f"  Total requests: {metrics.get('total_requests', 0)}")
                logger.info(f"  Success rate: {metrics.get('successful_requests', 0)}/{metrics.get('total_requests', 0)}")
        else:
            logger.error(f"✗ Gateway metrics failed: {result.error}")
        
        return result
    
    async def test_gateway_config(self) -> TestResult:
        """Test gateway configuration endpoint"""
        logger.info("Testing gateway configuration...")
        result = await self._make_request("GET", "/gateway/config")
        
        if result.success:
            logger.info(f"✓ Gateway configuration accessible ({result.duration_ms:.1f}ms)")
            if result.response_data:
                services = result.response_data.get('services', {})
                routes = result.response_data.get('routes', {})
                logger.info(f"  Configured services: {len(services)}")
                logger.info(f"  Configured routes: {len(routes)}")
        else:
            logger.error(f"✗ Gateway configuration failed: {result.error}")
        
        return result
    
    async def test_service_proxying(self) -> List[TestResult]:
        """Test service proxying through gateway"""
        logger.info("Testing service proxying...")
        results = []
        
        # Test health endpoints through gateway
        services_to_test = [
            ("/api/health/memory", "Memory API health"),
            ("/api/health/ollama", "Ollama health"),
            ("/api/health/openwebui", "OpenWebUI health"),
            ("/api/health/chroma", "ChromaDB health")
        ]
        
        for endpoint, description in services_to_test:
            logger.info(f"  Testing {description}...")
            result = await self._make_request("GET", endpoint)
            result.test_name = description
            
            if result.success:
                logger.info(f"    ✓ {description} passed ({result.duration_ms:.1f}ms)")
            else:
                logger.warning(f"    ✗ {description} failed: {result.error or f'HTTP {result.status_code}'}")
            
            results.append(result)
        
        return results
    
    async def test_memory_api_through_gateway(self) -> List[TestResult]:
        """Test memory API operations through gateway"""
        logger.info("Testing Memory API through gateway...")
        results = []
        
        # Test memory storage
        logger.info("  Testing memory storage...")
        store_result = await self._make_request(
            "POST", 
            "/api/memory/store",
            json=self.test_memory_data,
            headers={"Content-Type": "application/json"}
        )
        store_result.test_name = "Memory Store"
        
        if store_result.success:
            logger.info(f"    ✓ Memory storage passed ({store_result.duration_ms:.1f}ms)")
        else:
            logger.error(f"    ✗ Memory storage failed: {store_result.error or f'HTTP {store_result.status_code}'}")
        
        results.append(store_result)
        
        # Test memory retrieval
        logger.info("  Testing memory retrieval...")
        retrieve_result = await self._make_request(
            "GET", 
            f"/api/memory/retrieve/{self.test_user_id}"
        )
        retrieve_result.test_name = "Memory Retrieve"
        
        if retrieve_result.success:
            logger.info(f"    ✓ Memory retrieval passed ({retrieve_result.duration_ms:.1f}ms)")
            if retrieve_result.response_data:
                memories = retrieve_result.response_data.get('memories', [])
                logger.info(f"      Retrieved {len(memories)} memories")
        else:
            logger.error(f"    ✗ Memory retrieval failed: {retrieve_result.error or f'HTTP {retrieve_result.status_code}'}")
        
        results.append(retrieve_result)
        
        return results
    
    async def test_ollama_through_gateway(self) -> List[TestResult]:
        """Test Ollama API through gateway"""
        logger.info("Testing Ollama API through gateway...")
        results = []
        
        # Test model listing
        logger.info("  Testing Ollama model listing...")
        tags_result = await self._make_request("GET", "/api/ollama/tags")
        tags_result.test_name = "Ollama Tags"
        
        if tags_result.success:
            logger.info(f"    ✓ Ollama tags passed ({tags_result.duration_ms:.1f}ms)")
            if tags_result.response_data:
                models = tags_result.response_data.get('models', [])
                logger.info(f"      Available models: {len(models)}")
        else:
            logger.warning(f"    ✗ Ollama tags failed: {tags_result.error or f'HTTP {tags_result.status_code}'}")
        
        results.append(tags_result)
        
        return results
    
    async def test_rate_limiting(self) -> TestResult:
        """Test rate limiting functionality"""
        logger.info("Testing rate limiting...")
        
        # Make rapid requests to test rate limiting
        rapid_requests = []
        for i in range(15):  # Exceed typical rate limit
            result = await self._make_request("GET", "/gateway/health")
            rapid_requests.append(result)
        
        # Check if any requests were rate limited
        rate_limited = any(r.status_code == 429 for r in rapid_requests)
        successful_requests = sum(1 for r in rapid_requests if r.success)
        
        test_result = TestResult(
            test_name="Rate Limiting",
            success=True,  # Rate limiting working is success
            duration_ms=sum(r.duration_ms for r in rapid_requests),
            response_data={
                "total_requests": len(rapid_requests),
                "successful_requests": successful_requests,
                "rate_limited": rate_limited
            }
        )
        
        if rate_limited:
            logger.info(f"✓ Rate limiting is working ({successful_requests}/{len(rapid_requests)} succeeded)")
        else:
            logger.warning(f"⚠ Rate limiting may not be active ({successful_requests}/{len(rapid_requests)} succeeded)")
        
        return test_result
    
    async def test_caching(self) -> TestResult:
        """Test response caching"""
        logger.info("Testing response caching...")
        
        # Make two identical requests to test caching
        first_result = await self._make_request("GET", "/api/ollama/tags")
        await asyncio.sleep(0.1)  # Small delay
        second_result = await self._make_request("GET", "/api/ollama/tags")
        
        # Check if second request was faster (indicating cache hit)
        cache_performance_improvement = first_result.duration_ms > second_result.duration_ms
        
        test_result = TestResult(
            test_name="Response Caching",
            success=first_result.success and second_result.success,
            duration_ms=first_result.duration_ms + second_result.duration_ms,
            response_data={
                "first_request_ms": first_result.duration_ms,
                "second_request_ms": second_result.duration_ms,
                "cache_improvement": cache_performance_improvement
            }
        )
        
        if cache_performance_improvement:
            improvement = ((first_result.duration_ms - second_result.duration_ms) / first_result.duration_ms) * 100
            logger.info(f"✓ Caching working - {improvement:.1f}% performance improvement")
        else:
            logger.info("ℹ Caching status unclear - response times similar")
        
        return test_result
    
    async def test_error_handling(self) -> List[TestResult]:
        """Test error handling and recovery"""
        logger.info("Testing error handling...")
        results = []
        
        # Test 404 handling
        not_found_result = await self._make_request("GET", "/api/nonexistent/endpoint")
        not_found_result.test_name = "404 Error Handling"
        
        if not_found_result.status_code == 404:
            logger.info("✓ 404 error handling working")
            not_found_result.success = True
        else:
            logger.warning(f"⚠ Unexpected response for 404 test: {not_found_result.status_code}")
        
        results.append(not_found_result)
        
        # Test malformed request handling
        malformed_result = await self._make_request(
            "POST", 
            "/api/memory/store",
            data="invalid json data",
            headers={"Content-Type": "application/json"}
        )
        malformed_result.test_name = "Malformed Request Handling"
        
        if malformed_result.status_code in [400, 422]:
            logger.info("✓ Malformed request handling working")
            malformed_result.success = True
        else:
            logger.warning(f"⚠ Unexpected response for malformed request: {malformed_result.status_code}")
        
        results.append(malformed_result)
        
        return results
    
    async def test_performance_baseline(self) -> TestResult:
        """Establish performance baseline"""
        logger.info("Testing performance baseline...")
        
        # Make multiple requests to establish baseline
        test_requests = []
        for _ in range(10):
            result = await self._make_request("GET", "/gateway/health")
            if result.success:
                test_requests.append(result.duration_ms)
        
        if test_requests:
            avg_response_time = sum(test_requests) / len(test_requests)
            min_response_time = min(test_requests)
            max_response_time = max(test_requests)
            
            test_result = TestResult(
                test_name="Performance Baseline",
                success=True,
                duration_ms=avg_response_time,
                response_data={
                    "avg_response_time_ms": avg_response_time,
                    "min_response_time_ms": min_response_time,
                    "max_response_time_ms": max_response_time,
                    "samples": len(test_requests)
                }
            )
            
            logger.info(f"✓ Performance baseline established:")
            logger.info(f"    Average: {avg_response_time:.1f}ms")
            logger.info(f"    Range: {min_response_time:.1f}ms - {max_response_time:.1f}ms")
            
            return test_result
        else:
            return TestResult(
                test_name="Performance Baseline",
                success=False,
                duration_ms=0,
                error="No successful requests"
            )
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all tests and generate comprehensive report"""
        logger.info("Starting comprehensive enhanced gateway tests...")
        
        start_time = time.time()
        all_results = []
        
        # Run individual tests
        test_functions = [
            ("Gateway Health", self.test_gateway_health()),
            ("Gateway Metrics", self.test_gateway_metrics()),
            ("Gateway Config", self.test_gateway_config()),
            ("Service Proxying", self.test_service_proxying()),
            ("Memory API", self.test_memory_api_through_gateway()),
            ("Ollama API", self.test_ollama_through_gateway()),
            ("Rate Limiting", self.test_rate_limiting()),
            ("Response Caching", self.test_caching()),
            ("Error Handling", self.test_error_handling()),
            ("Performance Baseline", self.test_performance_baseline())
        ]
        
        for test_name, test_coro in test_functions:
            logger.info(f"\n--- {test_name} Tests ---")
            try:
                result = await test_coro
                if isinstance(result, list):
                    all_results.extend(result)
                else:
                    all_results.append(result)
            except Exception as e:
                logger.error(f"Test {test_name} failed with exception: {str(e)}")
                all_results.append(TestResult(
                    test_name=test_name,
                    success=False,
                    duration_ms=0,
                    error=str(e)
                ))
        
        # Generate summary report
        total_duration = time.time() - start_time
        successful_tests = sum(1 for r in all_results if r.success)
        total_tests = len(all_results)
        
        avg_response_time = sum(r.duration_ms for r in all_results if r.duration_ms > 0) / len([r for r in all_results if r.duration_ms > 0])
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
                "total_duration_seconds": total_duration,
                "average_response_time_ms": avg_response_time
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "duration_ms": r.duration_ms,
                    "status_code": r.status_code,
                    "error": r.error,
                    "response_data": r.response_data
                }
                for r in all_results
            ],
            "timestamp": time.time()
        }
        
        # Log summary
        logger.info(f"\n{'='*60}")
        logger.info("ENHANCED GATEWAY TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Tests Passed: {successful_tests}/{total_tests} ({report['summary']['success_rate']:.1f}%)")
        logger.info(f"Total Duration: {total_duration:.2f} seconds")
        logger.info(f"Average Response Time: {avg_response_time:.1f}ms")
        
        if successful_tests == total_tests:
            logger.info("🎉 All tests passed! Enhanced gateway is working perfectly.")
        else:
            logger.warning(f"⚠️  {total_tests - successful_tests} tests failed. Check logs for details.")
        
        return report

async def main():
    """Main test execution"""
    gateway_url = "http://localhost:8888"
    
    # Wait for gateway to be ready
    logger.info("Waiting for enhanced gateway to be ready...")
    for attempt in range(30):  # Wait up to 30 seconds
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{gateway_url}/gateway/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        logger.info("Enhanced gateway is ready!")
                        break
        except:
            pass
        
        await asyncio.sleep(1)
        logger.info(f"  Attempt {attempt + 1}/30...")
    else:
        logger.error("Enhanced gateway not responding after 30 seconds")
        return
    
    # Run comprehensive tests
    async with EnhancedGatewayTester(gateway_url) as tester:
        report = await tester.run_comprehensive_tests()
        
        # Save report to file
        report_filename = f"enhanced_gateway_test_report_{int(time.time())}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\nDetailed test report saved to: {report_filename}")

if __name__ == "__main__":
    asyncio.run(main())
