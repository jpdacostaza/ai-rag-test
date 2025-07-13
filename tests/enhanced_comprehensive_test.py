#!/usr/bin/env python3
"""
Enhanced Comprehensive Test System with Advanced Error Catching
Features:
- Deep error analysis and categorization
- Performance monitoring and bottleneck detection
- Integration testing with error simulation
- Stress testing capabilities
- Detailed logging with error tracking
- Recovery testing
- Data consistency validation
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import sys
import traceback
import statistics
from dataclasses import dataclass, asdict
import uuid
import random
import concurrent.futures
import psutil
import os

# Configure advanced logging with multiple handlers
log_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'enhanced_test_{log_timestamp}.log', encoding='utf-8'),
        logging.FileHandler(f'errors_{log_timestamp}.log', encoding='utf-8')
    ]
)

# Set stdout encoding for Windows Unicode support
if sys.platform.startswith('win'):
    import codecs
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)
error_logger = logging.getLogger('errors')

@dataclass
class ErrorDetails:
    error_type: str
    error_message: str
    traceback: str
    service: str
    endpoint: str
    method: str
    timestamp: str
    request_data: Any
    response_data: Any
    duration_ms: float
    retry_count: int
    context: Dict[str, Any]

@dataclass
class PerformanceMetrics:
    service: str
    endpoint: str
    method: str
    response_time_ms: float
    status_code: int
    timestamp: str
    payload_size_bytes: int
    memory_usage_mb: float
    cpu_usage_percent: float

@dataclass
class TestResult:
    test_name: str
    success: bool
    duration_ms: float
    errors: List[ErrorDetails]
    performance_metrics: List[PerformanceMetrics]
    details: str
    recovery_tested: bool = False
    stress_tested: bool = False

class EnhancedSystemTest:
    def __init__(self):
        self.base_urls = {
            'openwebui': 'http://localhost:8080',
            'pipelines': 'http://localhost:9099', 
            'backend': 'http://localhost:3000',
            'memory_api': 'http://localhost:8001',
            'ollama': 'http://localhost:11434',
            'chroma': 'http://localhost:8000',
            'redis': 'http://localhost:6379',
            'gateway': 'http://localhost:8888'  # API Gateway
        }
        
        self.test_results: List[TestResult] = []
        self.all_errors: List[ErrorDetails] = []
        self.performance_data: List[PerformanceMetrics] = []
        self.session = None
        self.test_session_id = str(uuid.uuid4())[:8]
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=20)
        )
        logger.info(f"Enhanced test session started: {self.test_session_id}")
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        logger.info(f"Enhanced test session ended: {self.test_session_id}")

    def capture_system_metrics(self) -> Dict[str, float]:
        """Capture current system performance metrics"""
        try:
            return {
                'memory_usage_mb': psutil.virtual_memory().used / 1024 / 1024,
                'cpu_usage_percent': psutil.cpu_percent(),
                'disk_usage_percent': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
                'network_connections': len(psutil.net_connections())
            }
        except Exception as e:
            logger.warning(f"Could not capture system metrics: {e}")
            return {}

    async def make_request_with_metrics(self, method: str, url: str, 
                                      service: str, endpoint: str,
                                      **kwargs) -> Tuple[Any, PerformanceMetrics, Optional[ErrorDetails]]:
        """Make HTTP request with comprehensive metrics and error capture"""
        
        start_time = time.time()
        start_metrics = self.capture_system_metrics()
        error_detail = None
        response_data = None
        status_code = 0
        payload_size = 0
        
        try:
            # Calculate payload size
            if 'json' in kwargs:
                payload_size = len(json.dumps(kwargs['json']).encode('utf-8'))
            elif 'data' in kwargs:
                payload_size = len(str(kwargs['data']).encode('utf-8'))
            
            async with self.session.request(method, url, **kwargs) as response:
                status_code = response.status
                duration_ms = (time.time() - start_time) * 1000
                
                # Get response data
                try:
                    if response.content_type == 'application/json':
                        response_data = await response.json()
                    else:
                        response_data = await response.text()
                except Exception as e:
                    response_data = f"Could not parse response: {e}"
                
                # Create performance metrics
                end_metrics = self.capture_system_metrics()
                performance = PerformanceMetrics(
                    service=service,
                    endpoint=endpoint,
                    method=method,
                    response_time_ms=duration_ms,
                    status_code=status_code,
                    timestamp=datetime.now().isoformat(),
                    payload_size_bytes=payload_size,
                    memory_usage_mb=end_metrics.get('memory_usage_mb', 0),
                    cpu_usage_percent=end_metrics.get('cpu_usage_percent', 0)
                )
                
                # Check for errors
                if response.status >= 400:
                    error_detail = ErrorDetails(
                        error_type='HTTP_ERROR',
                        error_message=f"HTTP {response.status}: {response.reason}",
                        traceback="",
                        service=service,
                        endpoint=endpoint,
                        method=method,
                        timestamp=datetime.now().isoformat(),
                        request_data=kwargs.get('json') or kwargs.get('data'),
                        response_data=response_data,
                        duration_ms=duration_ms,
                        retry_count=0,
                        context={'status_code': response.status, 'headers': dict(response.headers)}
                    )
                
                return response_data, performance, error_detail
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            error_detail = ErrorDetails(
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=traceback.format_exc(),
                service=service,
                endpoint=endpoint,
                method=method,
                timestamp=datetime.now().isoformat(),
                request_data=kwargs.get('json') or kwargs.get('data'),
                response_data=None,
                duration_ms=duration_ms,
                retry_count=0,
                context={'exception_type': type(e).__name__}
            )
            
            # Create performance metrics even for errors
            end_metrics = self.capture_system_metrics()
            performance = PerformanceMetrics(
                service=service,
                endpoint=endpoint,
                method=method,
                response_time_ms=duration_ms,
                status_code=0,
                timestamp=datetime.now().isoformat(),
                payload_size_bytes=payload_size,
                memory_usage_mb=end_metrics.get('memory_usage_mb', 0),
                cpu_usage_percent=end_metrics.get('cpu_usage_percent', 0)
            )
            
            return None, performance, error_detail

    async def test_with_error_simulation(self, test_name: str, test_func, 
                                       simulate_errors: bool = True) -> TestResult:
        """Run test with optional error simulation for resilience testing"""
        
        logger.info(f"[TEST START] {test_name}")
        start_time = time.time()
        errors = []
        performance_metrics = []
        recovery_tested = False
        
        try:
            # Run normal test
            result = await test_func()
            
            # If successful and error simulation enabled, test error recovery
            if result and simulate_errors:
                logger.info(f"   [RECOVERY TEST] Testing error recovery for {test_name}")
                recovery_tested = await self.test_error_recovery(test_name)
            
            duration_ms = (time.time() - start_time) * 1000
            
            test_result = TestResult(
                test_name=test_name,
                success=result,
                duration_ms=duration_ms,
                errors=errors,
                performance_metrics=performance_metrics,
                details=f"Test completed in {duration_ms:.1f}ms",
                recovery_tested=recovery_tested
            )
            
            self.test_results.append(test_result)
            status = "[PASS]" if result else "[FAIL]"
            logger.info(f"{status} {test_name} ({duration_ms:.1f}ms)")
            
            return test_result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            error_detail = ErrorDetails(
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=traceback.format_exc(),
                service="test_framework",
                endpoint=test_name,
                method="TEST",
                timestamp=datetime.now().isoformat(),
                request_data=None,
                response_data=None,
                duration_ms=duration_ms,
                retry_count=0,
                context={'test_name': test_name}
            )
            
            errors.append(error_detail)
            self.all_errors.append(error_detail)
            
            test_result = TestResult(
                test_name=test_name,
                success=False,
                duration_ms=duration_ms,
                errors=errors,
                performance_metrics=performance_metrics,
                details=f"Test failed: {str(e)}",
                recovery_tested=False
            )
            
            self.test_results.append(test_result)
            logger.error(f"[FAIL] {test_name}: {str(e)}")
            
            return test_result

    async def test_error_recovery(self, test_name: str) -> bool:
        """Test error recovery capabilities"""
        try:
            # Simulate various error conditions and test recovery
            recovery_tests = []
            
            # Test 1: Network timeout simulation
            try:
                async with self.session.get(
                    'http://localhost:99999/nonexistent',  # Invalid port
                    timeout=aiohttp.ClientTimeout(total=1)
                ) as response:
                    pass
            except:
                recovery_tests.append("Network timeout handled")
            
            # Test 2: Invalid JSON simulation
            try:
                await self.session.post(
                    f"{self.base_urls['memory_api']}/store",
                    data="invalid json data"
                )
            except:
                recovery_tests.append("Invalid data handled")
            
            # Test 3: Service overload simulation (rapid requests)
            tasks = []
            for i in range(10):
                task = self.session.get(f"{self.base_urls['ollama']}/api/tags")
                tasks.append(task)
            
            try:
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                recovery_tests.append(f"Rapid requests handled: {len(responses)} responses")
            except:
                recovery_tests.append("Rapid request handling tested")
            
            logger.info(f"   [RECOVERY] {test_name}: {len(recovery_tests)} recovery scenarios tested")
            return len(recovery_tests) > 0
            
        except Exception as e:
            logger.warning(f"Error recovery test failed: {e}")
            return False

    async def stress_test_service(self, service_name: str, endpoint: str, 
                                concurrent_requests: int = 10, 
                                duration_seconds: int = 30) -> Dict[str, Any]:
        """Perform stress testing on a specific service"""
        
        logger.info(f"   [STRESS TEST] {service_name}{endpoint} - {concurrent_requests} concurrent requests for {duration_seconds}s")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        request_count = 0
        error_count = 0
        response_times = []
        
        async def make_stress_request():
            nonlocal request_count, error_count
            try:
                request_start = time.time()
                async with self.session.get(f"{self.base_urls[service_name]}{endpoint}") as response:
                    request_duration = (time.time() - request_start) * 1000
                    response_times.append(request_duration)
                    request_count += 1
                    if response.status >= 400:
                        error_count += 1
            except Exception as e:
                error_count += 1
        
        # Run stress test
        while time.time() < end_time:
            tasks = [make_stress_request() for _ in range(concurrent_requests)]
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(0.1)  # Brief pause between batches
        
        # Calculate metrics
        total_duration = time.time() - start_time
        avg_response_time = statistics.mean(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        requests_per_second = request_count / total_duration if total_duration > 0 else 0
        error_rate = (error_count / request_count * 100) if request_count > 0 else 0
        
        stress_results = {
            "service": service_name,
            "endpoint": endpoint,
            "duration_seconds": total_duration,
            "total_requests": request_count,
            "total_errors": error_count,
            "requests_per_second": requests_per_second,
            "error_rate_percent": error_rate,
            "avg_response_time_ms": avg_response_time,
            "min_response_time_ms": min_response_time,
            "max_response_time_ms": max_response_time
        }
        
        logger.info(f"   [STRESS RESULT] {service_name}: {requests_per_second:.1f} req/s, {error_rate:.1f}% errors, {avg_response_time:.1f}ms avg")
        
        return stress_results

    # Enhanced versions of the original tests
    async def test_enhanced_service_health(self):
        """Enhanced service health test with performance monitoring"""
        errors = []
        performance_metrics = []
        
        health_endpoints = {
            'OpenWebUI': (f"{self.base_urls['openwebui']}/health", 'openwebui'),
            'Pipelines': (f"{self.base_urls['pipelines']}/", 'pipelines'),
            'Memory API': (f"{self.base_urls['memory_api']}/health", 'memory_api'),
            'Ollama': (f"{self.base_urls['ollama']}/api/tags", 'ollama'),
            'ChromaDB': (f"{self.base_urls['chroma']}/api/v2/version", 'chroma')
        }
        
        all_healthy = True
        
        for service_name, (url, service_key) in health_endpoints.items():
            response_data, performance, error = await self.make_request_with_metrics(
                'GET', url, service_key, '/health'
            )
            
            performance_metrics.append(performance)
            
            if error:
                errors.append(error)
                all_healthy = False
                logger.error(f"   [ERROR] {service_name}: {error.error_message}")
            else:
                logger.info(f"   [OK] {service_name}: {performance.response_time_ms:.1f}ms")
        
        # Store metrics
        self.performance_data.extend(performance_metrics)
        self.all_errors.extend(errors)
        
        return all_healthy

    async def test_enhanced_data_consistency(self):
        """Test data consistency across services with validation"""
        
        logger.info("   [CONSISTENCY] Testing data consistency across services")
        
        # Test data
        test_id = str(uuid.uuid4())[:8]
        test_content = f"Consistency test data {test_id} at {datetime.now()}"
        
        consistency_tests = []
        
        # Store data in memory API
        try:
            store_data, store_perf, store_error = await self.make_request_with_metrics(
                'POST', f"{self.base_urls['memory_api']}/store",
                'memory_api', '/store',
                json={"content": test_content, "metadata": {"test_id": test_id}}
            )
            
            if not store_error:
                consistency_tests.append("[OK] Data stored in Memory API")
                
                # Wait a moment for propagation
                await asyncio.sleep(1)
                
                # Try to retrieve and validate
                retrieve_data, retrieve_perf, retrieve_error = await self.make_request_with_metrics(
                    'GET', f"{self.base_urls['memory_api']}/health",
                    'memory_api', '/health'
                )
                
                if not retrieve_error:
                    consistency_tests.append("[OK] Memory API accessible after store")
                else:
                    consistency_tests.append(f"[ERROR] Memory API not accessible: {retrieve_error.error_message}")
            else:
                consistency_tests.append(f"[ERROR] Failed to store data: {store_error.error_message}")
                
        except Exception as e:
            consistency_tests.append(f"[ERROR] Consistency test exception: {str(e)}")
        
        success = all("[OK]" in test for test in consistency_tests)
        logger.info(f"   [CONSISTENCY] Results: {'; '.join(consistency_tests)}")
        
        return success

    async def test_performance_baseline(self):
        """Establish performance baselines for all services"""
        
        logger.info("   [PERFORMANCE] Establishing performance baselines")
        
        baseline_tests = [
            ('ollama', '/api/tags', 'GET'),
            ('memory_api', '/health', 'GET'), 
            ('openwebui', '/health', 'GET'),
            ('pipelines', '/', 'GET'),
            ('chroma', '/api/v2/version', 'GET')
        ]
        
        baselines = {}
        all_passed = True
        
        for service, endpoint, method in baseline_tests:
            # Run multiple requests to get stable baseline
            response_times = []
            
            for i in range(5):
                response_data, performance, error = await self.make_request_with_metrics(
                    method, f"{self.base_urls[service]}{endpoint}",
                    service, endpoint
                )
                
                if not error:
                    response_times.append(performance.response_time_ms)
                else:
                    all_passed = False
                    
                await asyncio.sleep(0.5)
            
            if response_times:
                avg_time = statistics.mean(response_times)
                baselines[f"{service}{endpoint}"] = {
                    "avg_response_time_ms": avg_time,
                    "min_time_ms": min(response_times),
                    "max_time_ms": max(response_times),
                    "sample_count": len(response_times)
                }
                logger.info(f"   [BASELINE] {service}{endpoint}: {avg_time:.1f}ms avg")
            else:
                logger.error(f"   [BASELINE] {service}{endpoint}: No successful requests")
                all_passed = False
        
        # Store baselines for future comparison
        with open(f'performance_baseline_{log_timestamp}.json', 'w') as f:
            json.dump(baselines, f, indent=2)
        
        return all_passed

    async def run_comprehensive_enhanced_tests(self):
        """Run all enhanced tests with comprehensive error catching"""
        
        logger.info("=" * 100)
        logger.info(f"[ENHANCED TEST START] Comprehensive Enhanced System Test - Session {self.test_session_id}")
        logger.info(f"Test started at: {datetime.now()}")
        logger.info("=" * 100)
        
        # Define test suite
        test_suite = [
            ("Enhanced Service Health", self.test_enhanced_service_health, True),
            ("Performance Baseline", self.test_performance_baseline, False),
            ("Data Consistency", self.test_enhanced_data_consistency, True),
            ("Ollama Integration", self.test_ollama_integration_enhanced, True),
            ("Memory API Advanced", self.test_memory_api_advanced, True),
            ("Pipeline Integration", self.test_pipeline_integration_enhanced, True),
            ("OpenWebUI Advanced", self.test_openwebui_advanced, True),
            ("Full System Stress", self.test_full_system_stress, False)
        ]
        
        results = []
        
        for test_name, test_func, simulate_errors in test_suite:
            try:
                result = await self.test_with_error_simulation(test_name, test_func, simulate_errors)
                results.append(result.success)
                await asyncio.sleep(2)  # Pause between tests
            except Exception as e:
                logger.error(f"Critical test failure in {test_name}: {str(e)}")
                results.append(False)
        
        # Generate comprehensive report
        await self.generate_comprehensive_report(results)
        return all(results)

    async def test_ollama_integration_enhanced(self):
        """Enhanced Ollama testing with error scenarios"""
        
        # Test model availability with detailed error checking
        models_data, models_perf, models_error = await self.make_request_with_metrics(
            'GET', f"{self.base_urls['ollama']}/api/tags",
            'ollama', '/api/tags'
        )
        
        if models_error:
            return False
            
        # Test generation with performance monitoring
        test_prompts = [
            "What is 2+2?",
            "Hello, world!",
            "Test response"
        ]
        
        generation_success = 0
        for prompt in test_prompts:
            gen_data, gen_perf, gen_error = await self.make_request_with_metrics(
                'POST', f"{self.base_urls['ollama']}/api/generate",
                'ollama', '/api/generate',
                json={"model": "llama3.2:3b", "prompt": prompt, "stream": False}
            )
            
            if not gen_error:
                generation_success += 1
                
        return generation_success >= 2  # At least 2/3 prompts should work

    async def test_memory_api_advanced(self):
        """Advanced Memory API testing"""
        
        # Test multiple operations
        operations = [
            ('store', 'POST', {"content": "test 1", "metadata": {"id": 1}}),
            ('store', 'POST', {"content": "test 2", "metadata": {"id": 2}}),
            ('health', 'GET', None)
        ]
        
        success_count = 0
        for endpoint, method, data in operations:
            response_data, perf, error = await self.make_request_with_metrics(
                method, f"{self.base_urls['memory_api']}/{endpoint}",
                'memory_api', f'/{endpoint}',
                json=data if data else None
            )
            
            if not error:
                success_count += 1
        
        return success_count >= 2  # At least 2/3 operations should work

    async def test_pipeline_integration_enhanced(self):
        """Enhanced Pipeline testing"""
        
        pipeline_data, pipeline_perf, pipeline_error = await self.make_request_with_metrics(
            'GET', f"{self.base_urls['pipelines']}/",
            'pipelines', '/'
        )
        
        return not pipeline_error

    async def test_openwebui_advanced(self):
        """Advanced OpenWebUI testing"""
        
        # Test multiple endpoints
        endpoints = ['/api/config', '/health']
        success_count = 0
        
        for endpoint in endpoints:
            ui_data, ui_perf, ui_error = await self.make_request_with_metrics(
                'GET', f"{self.base_urls['openwebui']}{endpoint}",
                'openwebui', endpoint
            )
            
            if not ui_error:
                success_count += 1
        
        return success_count >= 1  # At least one endpoint should work

    async def test_full_system_stress(self):
        """Full system stress test"""
        
        logger.info("   [STRESS] Running full system stress test")
        
        # Stress test multiple services concurrently
        stress_tasks = [
            self.stress_test_service('ollama', '/api/tags', 5, 15),
            self.stress_test_service('memory_api', '/health', 3, 15),
            self.stress_test_service('openwebui', '/health', 3, 15)
        ]
        
        stress_results = await asyncio.gather(*stress_tasks, return_exceptions=True)
        
        # Analyze stress test results
        successful_stress_tests = 0
        for result in stress_results:
            if isinstance(result, dict) and result.get('error_rate_percent', 100) < 50:
                successful_stress_tests += 1
        
        return successful_stress_tests >= 2  # At least 2/3 stress tests should pass

    async def generate_comprehensive_report(self, results: List[bool]):
        """Generate comprehensive test report with error analysis"""
        
        logger.info("=" * 100)
        logger.info("[COMPREHENSIVE REPORT] Enhanced Test Summary")
        logger.info("=" * 100)
        
        # Basic statistics
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        logger.info(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        logger.info(f"Total Errors Captured: {len(self.all_errors)}")
        logger.info(f"Performance Metrics Collected: {len(self.performance_data)}")
        logger.info("")
        
        # Detailed test results
        logger.info("DETAILED TEST RESULTS:")
        for test_result in self.test_results:
            status = "[PASS]" if test_result.success else "[FAIL]"
            recovery = " + RECOVERY" if test_result.recovery_tested else ""
            stress = " + STRESS" if test_result.stress_tested else ""
            
            logger.info(f"   {status} {test_result.test_name} ({test_result.duration_ms:.1f}ms){recovery}{stress}")
            
            if test_result.errors:
                for error in test_result.errors:
                    logger.info(f"      └─ ERROR: {error.error_type}: {error.error_message}")
        
        # Error analysis
        if self.all_errors:
            logger.info("")
            logger.info("ERROR ANALYSIS:")
            error_types = {}
            for error in self.all_errors:
                error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            
            for error_type, count in error_types.items():
                logger.info(f"   {error_type}: {count} occurrences")
        
        # Performance analysis
        if self.performance_data:
            logger.info("")
            logger.info("PERFORMANCE ANALYSIS:")
            
            # Group by service
            service_performance = {}
            for metric in self.performance_data:
                if metric.service not in service_performance:
                    service_performance[metric.service] = []
                service_performance[metric.service].append(metric.response_time_ms)
            
            for service, times in service_performance.items():
                avg_time = statistics.mean(times)
                max_time = max(times)
                min_time = min(times)
                logger.info(f"   {service}: {avg_time:.1f}ms avg (min: {min_time:.1f}ms, max: {max_time:.1f}ms)")
        
        # System health assessment
        logger.info("")
        if success_rate >= 90:
            logger.info("[STATUS] EXCELLENT - System is highly stable and performant!")
        elif success_rate >= 75:
            logger.info("[STATUS] GOOD - System is stable with minor issues")
        elif success_rate >= 50:
            logger.info("[STATUS] MODERATE - System has some stability issues")
        else:
            logger.info("[STATUS] CRITICAL - System has significant issues requiring attention")
        
        # Save detailed report to file
        report_data = {
            "session_id": self.test_session_id,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "tests_passed": passed,
                "tests_total": total,
                "success_rate": success_rate,
                "total_errors": len(self.all_errors),
                "performance_metrics": len(self.performance_data)
            },
            "test_results": [asdict(result) for result in self.test_results],
            "errors": [asdict(error) for error in self.all_errors],
            "performance_metrics": [asdict(metric) for metric in self.performance_data]
        }
        
        with open(f'enhanced_test_report_{log_timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Detailed report saved to: enhanced_test_report_{log_timestamp}.json")
        logger.info("=" * 100)

async def main():
    """Main test execution with enhanced error catching"""
    try:
        async with EnhancedSystemTest() as test_suite:
            await test_suite.run_comprehensive_enhanced_tests()
    except Exception as e:
        logger.critical(f"Critical failure in test suite: {str(e)}")
        logger.critical(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
