#!/usr/bin/env python3
"""
Test Suite for Error Handling Patterns
=====================================

Tests the new unified error handling system to ensure it works correctly
and provides the expected behavior for different error scenarios.
"""

import asyncio
import sys
import os
from typing import List, Dict, Any

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities.error_patterns import (
    handle_service_errors,
    error_context,
    sync_error_context,
    ServiceErrorConfigs,
    ErrorHandlerConfig,
    ServiceType,
    ErrorAction,
    ErrorSeverity,
    handle_database_errors,
    handle_llm_errors,
    handle_memory_errors,
    handle_cache_errors
)


def test_decorator_basic():
    """Test basic decorator functionality."""
    print("\n🧪 Testing basic decorator functionality...")
    
    @handle_service_errors(
        config=ErrorHandlerConfig(
            service_type=ServiceType.GENERAL,
            action=ErrorAction.RETURN_DEFAULT,
            default_value="default_result"
        ),
        service_name="TestService",
        operation_name="test_operation"
    )
    def failing_function():
        raise ValueError("Test error")
    
    @handle_service_errors(
        config=ErrorHandlerConfig(
            service_type=ServiceType.GENERAL,
            action=ErrorAction.RETURN_DEFAULT,
            default_value="success_result"
        )
    )
    def succeeding_function():
        return "success_result"
    
    # Test failing function returns default
    result1 = failing_function()
    assert result1 == "default_result", f"Expected 'default_result', got '{result1}'"
    print("✅ Failing function returned default value correctly")
    
    # Test succeeding function works normally
    result2 = succeeding_function()
    assert result2 == "success_result", f"Expected 'success_result', got '{result2}'"
    print("✅ Succeeding function worked normally")


async def test_async_decorator():
    """Test async decorator functionality."""
    print("\n🧪 Testing async decorator functionality...")
    
    @handle_service_errors(
        config=ErrorHandlerConfig(
            service_type=ServiceType.DATABASE,
            action=ErrorAction.RETURN_EMPTY,
            default_value=[],
            max_retries=2
        ),
        service_name="DatabaseService",
        operation_name="async_operation"
    )
    async def async_failing_function():
        raise ConnectionError("Database connection failed")
    
    @handle_service_errors(
        config=ErrorHandlerConfig(
            service_type=ServiceType.DATABASE,
            action=ErrorAction.RETURN_DEFAULT,
            default_value=["data1", "data2"]
        )
    )
    async def async_succeeding_function():
        return ["data1", "data2"]
    
    # Test async failing function
    result1 = await async_failing_function()
    assert result1 == [], f"Expected empty list, got '{result1}'"
    print("✅ Async failing function returned empty list correctly")
    
    # Test async succeeding function
    result2 = await async_succeeding_function()
    assert result2 == ["data1", "data2"], f"Expected ['data1', 'data2'], got '{result2}'"
    print("✅ Async succeeding function worked normally")


async def test_context_manager():
    """Test error context manager."""
    print("\n🧪 Testing error context manager...")
    
    # Test successful operation
    async with error_context(
        "TestService",
        "successful_operation",
        config=ErrorHandlerConfig(service_type=ServiceType.GENERAL)
    ) as ctx:
        ctx["operation"] = "success"
        ctx["result"] = "test_result"
    
    print("✅ Context manager handled successful operation")
    
    # Test failing operation with non-raising config
    try:
        async with error_context(
            "TestService", 
            "failing_operation",
            config=ErrorHandlerConfig(
                service_type=ServiceType.GENERAL,
                action=ErrorAction.LOG_ONLY,
                severity=ErrorSeverity.LOW
            )
        ) as ctx:
            ctx["operation"] = "failure"
            raise ValueError("Test context error")
        
        print("✅ Context manager handled failing operation with LOG_ONLY")
    except ValueError:
        print("❌ Context manager should not have raised with LOG_ONLY action")


def test_convenience_decorators():
    """Test convenience decorators for different service types."""
    print("\n🧪 Testing convenience decorators...")
    
    @handle_database_errors(operation_name="db_operation", default_value=[])
    def db_function():
        raise Exception("Database error")
    
    @handle_memory_errors(operation_name="memory_operation")
    def memory_function():
        raise Exception("Memory error")
    
    @handle_cache_errors(operation_name="cache_operation")
    def cache_function():
        raise Exception("Cache error")
    
    # Test database decorator
    result1 = db_function()
    assert result1 == [], f"Expected empty list, got '{result1}'"
    print("✅ Database decorator returned correct default")
    
    # Test memory decorator
    result2 = memory_function()
    assert result2 == [], f"Expected empty list, got '{result2}'"
    print("✅ Memory decorator returned correct default")
    
    # Test cache decorator (LOG_ONLY action)
    result3 = cache_function()
    assert result3 is None, f"Expected None, got '{result3}'"
    print("✅ Cache decorator handled error correctly")


def test_retry_mechanism():
    """Test retry mechanism."""
    print("\n🧪 Testing retry mechanism...")
    
    attempt_count = 0
    
    @handle_service_errors(
        config=ErrorHandlerConfig(
            service_type=ServiceType.GENERAL,
            action=ErrorAction.RETURN_DEFAULT,
            default_value="failed_after_retries",
            max_retries=3,
            retry_delay=0.1
        ),
        service_name="RetryService",
        operation_name="retry_test"
    )
    def retry_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionError(f"Attempt {attempt_count} failed")
        return f"Success on attempt {attempt_count}"
    
    result = retry_function()
    assert result == "Success on attempt 3", f"Expected success message, got '{result}'"
    assert attempt_count == 3, f"Expected 3 attempts, got {attempt_count}"
    print("✅ Retry mechanism worked correctly")


async def test_fallback_function():
    """Test fallback function mechanism."""
    print("\n🧪 Testing fallback function...")
    
    def fallback():
        return "fallback_result"
    
    @handle_service_errors(
        config=ErrorHandlerConfig(
            service_type=ServiceType.GENERAL,
            action=ErrorAction.FALLBACK,
            fallback_function=fallback
        ),
        service_name="FallbackService",
        operation_name="fallback_test"
    )
    async def fallback_function():
        raise Exception("Primary function failed")
    
    result = await fallback_function()
    assert result == "fallback_result", f"Expected 'fallback_result', got '{result}'"
    print("✅ Fallback function worked correctly")


def test_pre_configured_services():
    """Test pre-configured service error configs."""
    print("\n🧪 Testing pre-configured service configs...")
    
    # Test that all pre-configured configs exist and have correct types
    configs = [
        ServiceErrorConfigs.DATABASE,
        ServiceErrorConfigs.LLM,
        ServiceErrorConfigs.MEMORY,
        ServiceErrorConfigs.CACHE,
        ServiceErrorConfigs.API,
        ServiceErrorConfigs.VALIDATION
    ]
    
    for config in configs:
        assert isinstance(config, ErrorHandlerConfig), f"Config should be ErrorHandlerConfig instance"
        assert isinstance(config.service_type, ServiceType), f"Service type should be ServiceType enum"
        assert isinstance(config.action, ErrorAction), f"Action should be ErrorAction enum"
        assert isinstance(config.severity, ErrorSeverity), f"Severity should be ErrorSeverity enum"
    
    print("✅ All pre-configured service configs are valid")


async def main():
    """Run all error handling pattern tests."""
    print("🚀 Error Handling Patterns Test Suite")
    print("=" * 50)
    
    try:
        # Run synchronous tests
        test_decorator_basic()
        test_convenience_decorators()
        test_retry_mechanism()
        test_pre_configured_services()
        
        # Run asynchronous tests
        await test_async_decorator()
        await test_context_manager()
        await test_fallback_function()
        
        print("\n" + "=" * 50)
        print("✅ All error handling pattern tests passed!")
        print("🎉 Error handling patterns are working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        exit(1)
