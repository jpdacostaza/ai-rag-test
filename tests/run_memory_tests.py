#!/usr/bin/env python3
"""
Enhanced Memory System Test Runner
==================================

This script runs all comprehensive tests for the enhanced memory system.

Usage:
    python run_memory_tests.py              # Run all tests
    python run_memory_tests.py --basic      # Run basic tests only
    python run_memory_tests.py --deletion   # Run deletion tests only
    python run_memory_tests.py --quick      # Run quick smoke tests
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

async def run_comprehensive_tests():
    """Run the comprehensive test suite."""
    print("🚀 Running Comprehensive Memory System Tests...")
    try:
        from tests.test_enhanced_memory_system import TestEnhancedMemorySystem
        test_suite = TestEnhancedMemorySystem()
        return await test_suite.run_all_tests()
    except Exception as e:
        print(f"❌ Comprehensive tests failed: {e}")
        return False

async def run_deletion_tests():
    """Run the deletion-specific tests."""
    print("🚀 Running Memory Deletion Tests...")
    try:
        from tests.test_memory_deletion import MemoryDeletionTest
        deletion_test = MemoryDeletionTest()
        return await deletion_test.run_tests()
    except Exception as e:
        print(f"❌ Deletion tests failed: {e}")
        return False

async def run_quick_smoke_tests():
    """Run quick smoke tests to verify basic functionality."""
    print("🚀 Running Quick Smoke Tests...")
    
    try:
        # Import and test basic pipeline functionality
        from pipelines.enhanced_memory_pipeline import Pipeline
        
        pipeline = Pipeline()
        
        # Test 1: Pipeline initialization
        print("📋 Test 1: Pipeline Initialization")
        assert pipeline.valves.max_memories == 100, "Max memories should be 100"
        assert pipeline.valves.memory_threshold == 0.0, "Threshold should be 0.0"
        assert pipeline.valves.unlimited_storage == True, "Unlimited storage should be enabled"
        print("  ✅ Pipeline configuration correct")
        
        # Test 2: Command detection
        print("📋 Test 2: Command Detection")
        test_commands = [
            "Remember this: I like coffee",
            "Forget about my password", 
            "Save this important note"
        ]
        
        for cmd in test_commands:
            result = pipeline.detect_explicit_memory_commands(cmd)
            assert result["has_command"] == True, f"Should detect command in: {cmd}"
        print("  ✅ Command detection working")
        
        # Test 3: User validation
        print("📋 Test 3: User Validation")
        valid_user = {"id": "12345678-1234-1234-1234-123456789012", "email": "test@example.com"}
        user_id = pipeline.get_user_identifier(valid_user)
        assert user_id is not None, "Should validate correct user"
        
        invalid_user = {"id": "invalid"}
        user_id = pipeline.get_user_identifier(invalid_user)
        assert user_id is None, "Should reject invalid user"
        print("  ✅ User validation working")
        
        # Test 4: Document detection
        print("📋 Test 4: Document Detection")
        doc_message = [{"role": "user", "content": "My technical skills include Python and my work experience spans 5 years."}]
        doc_info = pipeline.detect_document_content(doc_message)
        assert doc_info["is_document"] == True, "Should detect document content"
        print("  ✅ Document detection working")
        
        print("\n🎉 All smoke tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Smoke tests failed: {e}")
        return False

async def check_environment():
    """Check if the test environment is ready."""
    print("🔍 Checking test environment...")
    
    # Check if memory API is running
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8001/health")
            if response.status_code == 200:
                print("  ✅ Memory API is running")
                return True
            else:
                print(f"  ⚠️ Memory API returned status {response.status_code}")
                return False
    except Exception as e:
        print(f"  ❌ Memory API not accessible: {e}")
        print("  💡 Make sure Docker containers are running: docker-compose up -d")
        return False

def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Enhanced Memory System Test Runner")
    parser.add_argument("--basic", action="store_true", help="Run basic comprehensive tests")
    parser.add_argument("--deletion", action="store_true", help="Run deletion tests only")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke tests")
    parser.add_argument("--skip-env-check", action="store_true", help="Skip environment check")
    
    args = parser.parse_args()
    
    async def run_tests():
        # Check environment unless skipped
        if not args.skip_env_check:
            if not await check_environment():
                print("\n❌ Environment check failed. Use --skip-env-check to bypass.")
                return False
        
        success = True
        
        if args.quick:
            success = await run_quick_smoke_tests()
        elif args.deletion:
            success = await run_deletion_tests()
        elif args.basic:
            success = await run_comprehensive_tests()
        else:
            # Run all tests
            print("🎯 Running ALL test suites...\n")
            
            smoke_success = await run_quick_smoke_tests()
            print("\n" + "="*50 + "\n")
            
            comprehensive_success = await run_comprehensive_tests()
            print("\n" + "="*50 + "\n")
            
            deletion_success = await run_deletion_tests()
            
            success = smoke_success and comprehensive_success and deletion_success
            
            print("\n" + "="*70)
            print("📊 FINAL TEST RESULTS")
            print(f"  🚀 Smoke Tests: {'✅ PASSED' if smoke_success else '❌ FAILED'}")
            print(f"  🧪 Comprehensive Tests: {'✅ PASSED' if comprehensive_success else '❌ FAILED'}")
            print(f"  🗑️ Deletion Tests: {'✅ PASSED' if deletion_success else '❌ FAILED'}")
            print("="*70)
            
            if success:
                print("🎉 ALL TEST SUITES PASSED! Memory system is working perfectly!")
            else:
                print("❌ Some test suites failed. Please review the issues above.")
        
        return success
    
    # Run the tests
    success = asyncio.run(run_tests())
    return 0 if success else 1

if __name__ == "__main__":
    exit(exit_code := main())
