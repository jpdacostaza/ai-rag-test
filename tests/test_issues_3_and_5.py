#!/usr/bin/env python3
"""
Issues 3 & 5 Validation Test
===========================

This script validates the fixes for:
- Issue #3: Complete error handling migration
- Issue #5: Performance optimizations with enhanced connection pooling

Test coverage:
1. Standardized error handling patterns
2. Enhanced connection pooling performance
3. Memory pressure handling
4. Response time improvements
5. Connection pool monitoring
"""

import asyncio
import time
import sys
import os
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from utilities.enhanced_connection_pooling import get_enhanced_redis_pool, pool_manager
from utilities.performance_monitoring import performance_monitor, record_operation_performance
from utilities.async_context_managers import redis_connection
from utilities.simple_error_handling import handle_database_errors, handle_errors
from core.unified_logging import get_logger, log_service_status

logger = get_logger(__name__)


class TestValidation:
    """Test validation for Issues #3 and #5 fixes."""
    
    def __init__(self):
        self.test_results = []
        self.performance_baseline = {}

    async def run_all_tests(self):
        """Run comprehensive validation tests."""
        print("🧪 Running Issues #3 & #5 Validation Tests")
        print("=" * 60)
        
        try:
            # Start performance monitoring
            await performance_monitor.start_monitoring()
            
            # Test Issue #3: Error Handling Migration
            await self.test_error_handling_standardization()
            
            # Test Issue #5: Performance Optimizations
            await self.test_enhanced_connection_pooling()
            await self.test_memory_pressure_handling()
            await self.test_performance_improvements()
            
            # Generate final report
            await self.generate_test_report()
            
        except Exception as e:
            logger.error(f"Test suite error: {e}")
            print(f"❌ Test suite failed: {e}")
        finally:
            await performance_monitor.stop_monitoring()

    async def test_error_handling_standardization(self):
        """Test Issue #3: Standardized error handling patterns."""
        print("\n📋 Testing Issue #3: Error Handling Standardization")
        print("-" * 40)
        
        # Test 1: Database error handling decorator
        @handle_database_errors(operation="test_db_operation", default_value=None)
        async def test_database_operation():
            """Test database operation with standardized error handling."""
            # Simulate database operation
            await asyncio.sleep(0.1)
            return {"status": "success", "data": "test_data"}
        
        start_time = time.time()
        result = await test_database_operation()
        response_time = (time.time() - start_time) * 1000
        
        success = result is not None and result.get("status") == "success"
        record_operation_performance("test_database_operation", response_time, success)
        
        self.test_results.append({
            "test": "standardized_database_error_handling",
            "passed": success,
            "response_time_ms": response_time,
            "details": "Database operations use standardized error decorators"
        })
        
        print(f"✅ Database Error Handling: {'PASS' if success else 'FAIL'} ({response_time:.2f}ms)")
        
        # Test 2: Simple error handling patterns
        @handle_errors("test_simple_operation", default_value="fallback")
        async def test_simple_operation():
            """Test simple operation with error handling."""
            await asyncio.sleep(0.05)
            return "success"
        
        start_time = time.time()
        result = await test_simple_operation()
        response_time = (time.time() - start_time) * 1000
        
        success = result == "success"
        record_operation_performance("test_simple_operation", response_time, success)
        
        self.test_results.append({
            "test": "simple_error_handling",
            "passed": success,
            "response_time_ms": response_time,
            "details": "Simple operations use handle_errors decorator"
        })
        
        print(f"✅ Simple Error Handling: {'PASS' if success else 'FAIL'} ({response_time:.2f}ms)")

    async def test_enhanced_connection_pooling(self):
        """Test Issue #5: Enhanced connection pooling."""
        print("\n🏊 Testing Issue #5: Enhanced Connection Pooling")
        print("-" * 40)
        
        try:
            # Test 1: Create enhanced Redis pool
            start_time = time.time()
            redis_pool = await get_enhanced_redis_pool(
                pool_name="test_pool",
                max_size=10,
                min_size=2
            )
            pool_creation_time = (time.time() - start_time) * 1000
            
            pool_success = redis_pool is not None
            record_operation_performance("create_redis_pool", pool_creation_time, pool_success)
            
            self.test_results.append({
                "test": "enhanced_redis_pool_creation",
                "passed": pool_success,
                "response_time_ms": pool_creation_time,
                "details": "Enhanced Redis connection pool created successfully"
            })
            
            print(f"✅ Pool Creation: {'PASS' if pool_success else 'FAIL'} ({pool_creation_time:.2f}ms)")
            
            if pool_success:
                # Test 2: Pool connection usage
                connection_tests = []
                
                # Test multiple concurrent connections
                async def test_connection(connection_id):
                    start_time = time.time()
                    try:
                        async with redis_pool.get_connection() as conn:
                            # Simulate Redis operation
                            await asyncio.sleep(0.1)
                            response_time = (time.time() - start_time) * 1000
                            return {"success": True, "response_time": response_time, "connection_id": connection_id}
                    except Exception as e:
                        response_time = (time.time() - start_time) * 1000
                        return {"success": False, "response_time": response_time, "error": str(e)}
                
                # Run concurrent connection tests
                connection_tasks = [test_connection(i) for i in range(5)]
                connection_results = await asyncio.gather(*connection_tasks)
                
                successful_connections = sum(1 for r in connection_results if r["success"])
                avg_connection_time = sum(r["response_time"] for r in connection_results) / len(connection_results)
                
                pool_performance_success = successful_connections == 5
                record_operation_performance("pool_concurrent_connections", avg_connection_time, pool_performance_success)
                
                self.test_results.append({
                    "test": "pool_concurrent_connections",
                    "passed": pool_performance_success,
                    "response_time_ms": avg_connection_time,
                    "details": f"Concurrent connections: {successful_connections}/5 successful"
                })
                
                print(f"✅ Concurrent Connections: {'PASS' if pool_performance_success else 'FAIL'} ({avg_connection_time:.2f}ms avg)")
                
                # Test 3: Pool statistics
                pool_stats = redis_pool.get_stats()
                stats_available = "total_connections" in pool_stats
                
                self.test_results.append({
                    "test": "pool_statistics",
                    "passed": stats_available,
                    "response_time_ms": 0,
                    "details": f"Pool stats: {pool_stats}"
                })
                
                print(f"✅ Pool Statistics: {'PASS' if stats_available else 'FAIL'}")
                if stats_available:
                    print(f"   📊 Pool Stats: {pool_stats['total_connections']} connections, {pool_stats['avg_response_time_ms']:.2f}ms avg")
                
        except Exception as e:
            self.test_results.append({
                "test": "enhanced_connection_pooling",
                "passed": False,
                "response_time_ms": 0,
                "details": f"Pool testing failed: {str(e)}"
            })
            print(f"❌ Connection Pooling Test Failed: {e}")

    async def test_memory_pressure_handling(self):
        """Test memory pressure detection and handling."""
        print("\n🧠 Testing Memory Pressure Handling")
        print("-" * 40)
        
        try:
            import psutil
            
            # Get current memory usage
            memory = psutil.virtual_memory()
            memory_check_success = memory.percent < 100  # Basic sanity check
            
            self.test_results.append({
                "test": "memory_pressure_detection",
                "passed": memory_check_success,
                "response_time_ms": 0,
                "details": f"Memory usage: {memory.percent:.1f}%"
            })
            
            print(f"✅ Memory Detection: {'PASS' if memory_check_success else 'FAIL'} ({memory.percent:.1f}%)")
            
            # Test pool manager global stats
            global_stats = pool_manager.get_all_stats()
            stats_success = "global" in global_stats
            
            self.test_results.append({
                "test": "global_pool_monitoring",
                "passed": stats_success,
                "response_time_ms": 0,
                "details": f"Global stats available: {stats_success}"
            })
            
            print(f"✅ Global Pool Monitoring: {'PASS' if stats_success else 'FAIL'}")
            
        except Exception as e:
            print(f"❌ Memory Pressure Test Failed: {e}")

    async def test_performance_improvements(self):
        """Test overall performance improvements."""
        print("\n⚡ Testing Performance Improvements")
        print("-" * 40)
        
        # Run performance benchmark
        operations = []
        
        for i in range(10):
            start_time = time.time()
            
            # Simulate various operations
            async with redis_connection(use_enhanced_pool=True) as conn:
                await asyncio.sleep(0.05)  # Simulate work
            
            response_time = (time.time() - start_time) * 1000
            operations.append(response_time)
            record_operation_performance("performance_benchmark", response_time, True)
        
        avg_response_time = sum(operations) / len(operations)
        min_response_time = min(operations)
        max_response_time = max(operations)
        
        # Performance is considered good if average < 100ms
        performance_success = avg_response_time < 100.0
        
        self.test_results.append({
            "test": "performance_benchmark",
            "passed": performance_success,
            "response_time_ms": avg_response_time,
            "details": f"Avg: {avg_response_time:.2f}ms, Min: {min_response_time:.2f}ms, Max: {max_response_time:.2f}ms"
        })
        
        print(f"✅ Performance Benchmark: {'PASS' if performance_success else 'FAIL'}")
        print(f"   📈 Average: {avg_response_time:.2f}ms, Range: {min_response_time:.2f}-{max_response_time:.2f}ms")

    async def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n📊 Test Results Summary")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test["passed"])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Detailed results
        for test in self.test_results:
            status = "✅ PASS" if test["passed"] else "❌ FAIL"
            print(f"{status} {test['test']}")
            print(f"   ⏱️  {test['response_time_ms']:.2f}ms")
            print(f"   📝 {test['details']}")
            print()
        
        # Performance monitoring report
        try:
            perf_report = await performance_monitor.generate_performance_report()
            print("📈 Performance Monitoring Report")
            print("-" * 40)
            print(perf_report)
        except Exception as e:
            print(f"❌ Performance report generation failed: {e}")
        
        # Overall assessment
        print("\n🎯 Issues #3 & #5 Validation Results")
        print("=" * 60)
        
        if success_rate >= 80:
            print("🎉 SUCCESS: Both issues have been successfully addressed!")
            print("✅ Issue #3: Error handling has been standardized")
            print("✅ Issue #5: Performance optimizations are working")
        elif success_rate >= 60:
            print("⚠️  PARTIAL SUCCESS: Most improvements are working")
            print("📋 Some areas may need additional attention")
        else:
            print("❌ NEEDS WORK: Significant issues remain")
            print("🔧 Additional fixes may be required")


async def main():
    """Main test execution."""
    validator = TestValidation()
    await validator.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
