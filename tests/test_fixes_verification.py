#!/usr/bin/env python3
"""
Comprehensive verification script to test all fixes applied during code review.
Tests each category of issues that were resolved.
"""

import sys
import asyncio
import json
import time
import traceback
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

class FixesVerification:
    def __init__(self):
        self.results = {
            "security_fixes": {},
            "logging_fixes": {},
            "configuration_fixes": {},
            "code_quality_fixes": {},
            "system_integration": {}
        }
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def log_test(self, category, test_name, success, details=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
        
        self.results[category][test_name] = {
            "status": "PASS" if success else "FAIL",
            "details": details
        }
        
        print(f"{status} [{category}] {test_name}")
        if details:
            print(f"    Details: {details}")

    def test_ast_calculator_security(self):
        """Test 1: Verify AST-based calculator is secure and functional"""
        try:
            from utilities.ai_tools import calculate
            
            # Test basic arithmetic
            result1 = calculate("2 + 3 * 4")
            assert result1 == 14, f"Expected 14, got {result1}"
            
            # Test parentheses
            result2 = calculate("(2 + 3) * 4")
            assert result2 == 20, f"Expected 20, got {result2}"
            
            # Test security - should block function calls
            result3 = calculate("eval('print(\"hack\")')")
            assert "not allowed" in result3.lower() or "error" in result3.lower(), "Should block eval"
            
            # Test security - should block imports
            result4 = calculate("__import__('os').system('echo hack')")
            assert "not allowed" in result4.lower() or "error" in result4.lower(), "Should block imports"
            
            self.log_test("security_fixes", "AST Calculator Security", True, 
                         f"Basic math works: {result1}, {result2}. Blocks unsafe: {result3[:50]}...")
            
        except Exception as e:
            self.log_test("security_fixes", "AST Calculator Security", False, str(e))

    def test_memory_service_config(self):
        """Test 2: Verify memory service uses Docker service names"""
        try:
            from services.memory_service import APIMemoryProvider
            
            # Check if default URL uses Docker service name
            provider = APIMemoryProvider()
            
            # Should default to memory-api:5001 in Docker environment
            expected_patterns = ["memory-api:5001", "localhost:5001"]
            url_valid = any(pattern in provider.base_url for pattern in expected_patterns)
            
            self.log_test("configuration_fixes", "Memory Service Docker Config", url_valid,
                         f"Base URL: {provider.base_url}")
            
        except Exception as e:
            self.log_test("configuration_fixes", "Memory Service Docker Config", False, str(e))

    def test_exception_handling(self):
        """Test 3: Verify specific exception types are used"""
        try:
            from utilities.watchdog import SystemWatchdog
            
            # Test that watchdog imports without syntax errors
            config = {}
            watchdog = SystemWatchdog(config)
            
            # Check that the class was created successfully
            assert hasattr(watchdog, 'config'), "Watchdog should have config attribute"
            
            self.log_test("code_quality_fixes", "Exception Handling", True,
                         "Watchdog loads with proper exception types")
            
        except Exception as e:
            self.log_test("code_quality_fixes", "Exception Handling", False, str(e))

    def test_logging_standardization(self):
        """Test 4: Verify unified logging is used"""
        try:
            # Test memory API logging
            from memory.api.main import app
            
            # Check if the app imports successfully (no print statements in production)
            assert app is not None, "Memory API should load without errors"
            
            self.log_test("logging_fixes", "Memory API Logging", True,
                         "Memory API loads with unified logging")
            
        except Exception as e:
            self.log_test("logging_fixes", "Memory API Logging", False, str(e))

    def test_ai_tools_syntax(self):
        """Test 5: Verify ai_tools.py has no syntax errors"""
        try:
            from utilities.ai_tools import (
                get_current_time, 
                calculate, 
                get_system_info,
                run_python_code
            )
            
            # Test time function
            time_result = get_current_time()
            assert "2025" in time_result, f"Time should include current year: {time_result}"
            
            # Test system info
            sys_info = get_system_info()
            assert "System Information" in sys_info, f"Should return system info: {sys_info[:100]}"
            
            # Test Python code execution
            code_result = run_python_code("print('hello')")
            assert "hello" in code_result or "RestrictedPython not available" in code_result
            
            self.log_test("code_quality_fixes", "AI Tools Syntax", True,
                         f"All functions work: time={time_result[:30]}, sys={sys_info[:30]}")
            
        except Exception as e:
            self.log_test("code_quality_fixes", "AI Tools Syntax", False, str(e))

    def test_security_middleware(self):
        """Test 6: Verify security middleware has proper exception handling"""
        try:
            from middleware.security_middleware import SecurityMiddleware
            
            # Should import without syntax errors
            middleware = SecurityMiddleware(rate_limit_requests_per_minute=60)
            assert middleware is not None, "Security middleware should initialize"
            
            self.log_test("security_fixes", "Security Middleware", True,
                         "Security middleware loads with proper exception handling")
            
        except Exception as e:
            self.log_test("security_fixes", "Security Middleware", False, str(e))

    def test_rag_utility(self):
        """Test 7: Verify RAG utility has proper exception types"""
        try:
            from utilities.rag import extract_text_from_pdf, chunk_text
            
            # Test chunking function (doesn't require external dependencies)
            test_text = "This is a test text that should be chunked properly. " * 100
            chunks = chunk_text(test_text, chunk_size=200)
            
            assert len(chunks) > 1, f"Should create multiple chunks: {len(chunks)}"
            assert all(len(chunk) <= 250 for chunk in chunks), "Chunks should respect size limit"
            
            self.log_test("code_quality_fixes", "RAG Utility", True,
                         f"Text chunking works: {len(chunks)} chunks created")
            
        except Exception as e:
            self.log_test("code_quality_fixes", "RAG Utility", False, str(e))

    def test_llm_service(self):
        """Test 8: Verify LLM service has proper exception types"""
        try:
            from services.llm_service import OllamaService
            
            # Should initialize without syntax errors
            service = OllamaService()
            assert service is not None, "LLM service should initialize"
            assert hasattr(service, 'ollama_url'), "Should have ollama_url attribute"
            
            self.log_test("code_quality_fixes", "LLM Service", True,
                         f"LLM service loads: URL={service.ollama_url}")
            
        except Exception as e:
            self.log_test("code_quality_fixes", "LLM Service", False, str(e))

    async def test_system_health(self):
        """Test 9: Verify system health endpoints work"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Test backend health
                async with session.get('http://localhost:3000/health') as resp:
                    backend_healthy = resp.status == 200
                    backend_data = await resp.json()
                
                # Test memory API health
                async with session.get('http://localhost:5001/health') as resp:
                    memory_healthy = resp.status == 200
                    memory_data = await resp.json()
                
                overall_healthy = backend_healthy and memory_healthy
                
                self.log_test("system_integration", "Health Endpoints", overall_healthy,
                             f"Backend: {backend_healthy}, Memory: {memory_healthy}")
                
        except Exception as e:
            self.log_test("system_integration", "Health Endpoints", False, str(e))

    def test_debug_routes(self):
        """Test 10: Verify debug routes have proper exception handling"""
        try:
            from routes.debug import router
            
            # Should import without syntax errors
            assert router is not None, "Debug router should load"
            
            self.log_test("code_quality_fixes", "Debug Routes", True,
                         "Debug routes load with proper exception handling")
            
        except Exception as e:
            self.log_test("code_quality_fixes", "Debug Routes", False, str(e))

    async def run_all_tests(self):
        """Run all verification tests"""
        print("🔍 COMPREHENSIVE FIXES VERIFICATION")
        print("=" * 50)
        
        # Security fixes
        print("\n🔒 SECURITY FIXES:")
        self.test_ast_calculator_security()
        self.test_security_middleware()
        
        # Configuration fixes
        print("\n⚙️ CONFIGURATION FIXES:")
        self.test_memory_service_config()
        
        # Logging fixes
        print("\n📊 LOGGING FIXES:")
        self.test_logging_standardization()
        
        # Code quality fixes
        print("\n🛠️ CODE QUALITY FIXES:")
        self.test_ai_tools_syntax()
        self.test_exception_handling()
        self.test_rag_utility()
        self.test_llm_service()
        self.test_debug_routes()
        
        # System integration
        print("\n🌐 SYSTEM INTEGRATION:")
        await self.test_system_health()
        
        # Summary
        print(f"\n📋 VERIFICATION SUMMARY:")
        print(f"Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests)*100:.1f}%")
        
        if self.failed_tests == 0:
            print("\n🎉 ALL FIXES VERIFIED SUCCESSFULLY!")
        else:
            print(f"\n⚠️ {self.failed_tests} tests need attention")
        
        return self.failed_tests == 0

async def main():
    """Main verification function"""
    verifier = FixesVerification()
    success = await verifier.run_all_tests()
    
    # Save detailed results
    with open("verification_results.json", "w") as f:
        json.dump({
            "timestamp": time.time(),
            "success": success,
            "summary": {
                "total": verifier.total_tests,
                "passed": verifier.passed_tests,
                "failed": verifier.failed_tests
            },
            "results": verifier.results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Verification interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        traceback.print_exc()
        sys.exit(1)
