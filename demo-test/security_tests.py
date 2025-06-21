#!/usr/bin/env python3
"""
Authentication & Security Test Suite
====================================

Comprehensive testing for authentication, authorization, and security features:
- API key validation with various formats
- Authorization header testing
- Security vulnerability testing
- Rate limiting verification
- Input validation and sanitization
- Error handling for security scenarios
- Session management security
- CORS and security headers

This module ensures the backend is secure against common attacks.
"""

import json
import random
import string
import time
from datetime import datetime
from typing import Dict, List

import requests


class SecurityTestSuite:
    """Comprehensive security testing suite."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.valid_api_key = "f2b985dd-219f-45b1-a90e-170962cc7082"
        self.results = []
    
    def test_auth_scenario(self, test_name: str, headers: Dict, expected_status: int, 
                          endpoint: str = "/health/simple") -> Dict:
        """Test authentication scenario."""
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=headers,
                timeout=10
            )
            
            duration = time.time() - start_time
            success = response.status_code == expected_status
            
            result = {
                "test": test_name,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "duration": f"{duration:.2f}s",
                "response_size": len(response.content),
                "timestamp": datetime.now().isoformat()
            }
            
            if not success:
                result["response_preview"] = response.text[:200]
        
        except Exception as e:
            duration = time.time() - start_time
            result = {
                "test": test_name,
                "endpoint": endpoint,
                "success": False,
                "error": str(e),
                "duration": f"{duration:.2f}s",
                "timestamp": datetime.now().isoformat()
            }
        
        self.results.append(result)
        return result
    
    def test_api_key_authentication(self):
        """Test API key authentication scenarios."""
        print("🔐 Testing API Key Authentication...")
        
        auth_tests = [
            ("Valid X-API-Key", {"X-API-Key": self.valid_api_key}, 200),
            ("Valid Authorization Bearer", {"Authorization": f"Bearer {self.valid_api_key}"}, 200),
            ("Invalid API Key", {"X-API-Key": "invalid-key-12345"}, 401),
            ("Malformed Bearer Token", {"Authorization": "Bearer"}, 401),
            ("Empty API Key", {"X-API-Key": ""}, 401),
            ("Missing Authentication", {}, 401),
            ("Wrong Header Name", {"API-Key": self.valid_api_key}, 401),
            ("Case Sensitive Test", {"x-api-key": self.valid_api_key}, 401),
        ]
        
        for test_name, headers, expected_status in auth_tests:
            result = self.test_auth_scenario(test_name, headers, expected_status)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {test_name}: {result['actual_status']} ({result['duration']})")
    
    def test_query_parameter_auth(self):
        """Test authentication via query parameters."""
        print("🔗 Testing Query Parameter Authentication...")
        
        try:
            # Test valid API key in query parameter
            response = requests.get(
                f"{self.base_url}/health/simple",
                params={"api_key": self.valid_api_key},
                timeout=10
            )
            
            result = {
                "test": "Query Parameter Auth",
                "success": response.status_code == 200,
                "status": response.status_code,
                "timestamp": datetime.now().isoformat()
            }
            
            # Test invalid API key in query parameter
            response2 = requests.get(
                f"{self.base_url}/health/simple",
                params={"api_key": "invalid-key"},
                timeout=10
            )
            
            result2 = {
                "test": "Invalid Query Parameter Auth",
                "success": response2.status_code == 401,
                "status": response2.status_code,
                "timestamp": datetime.now().isoformat()
            }
            
            self.results.extend([result, result2])
            
            status1 = "✅" if result["success"] else "❌"
            status2 = "✅" if result2["success"] else "❌"
            print(f"  {status1} Valid Query Param: {result['status']}")
            print(f"  {status2} Invalid Query Param: {result2['status']}")
            
        except Exception as e:
            result = {
                "test": "Query Parameter Auth",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(result)
            print(f"  ❌ Query Parameter Auth: Error - {str(e)}")
    
    def test_input_validation(self):
        """Test input validation and sanitization."""
        print("🛡️  Testing Input Validation...")
        
        malicious_inputs = [
            ("SQL Injection", "'; DROP TABLE users; --"),
            ("XSS Attempt", "<script>alert('xss')</script>"),
            ("Command Injection", "; rm -rf /"),
            ("Path Traversal", "../../../etc/passwd"),
            ("NoSQL Injection", "{'$ne': null}"),
            ("LDAP Injection", ")(cn=*))(|(cn=*"),
            ("XML External Entity", "<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>"),
            ("Extremely Long Input", "A" * 10000),
        ]
        
        headers = {"X-API-Key": self.valid_api_key, "Content-Type": "application/json"}
        
        for test_name, malicious_input in malicious_inputs:
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/chat",
                    headers=headers,
                    json={
                        "user_id": "security_test",
                        "message": malicious_input
                    },
                    timeout=15
                )
                
                duration = time.time() - start_time
                
                # Server should handle malicious input gracefully (not crash)
                success = response.status_code in [200, 400, 422]  # Valid response codes
                
                result = {
                    "test": f"Input Validation - {test_name}",
                    "input_type": test_name,
                    "success": success,
                    "status": response.status_code,
                    "duration": f"{duration:.2f}s",
                    "response_length": len(response.content),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Check if response contains the malicious input (potential vulnerability)
                if malicious_input in response.text:
                    result["warning"] = "Malicious input reflected in response"
                
                self.results.append(result)
                status = "✅" if success else "❌"
                warning = " ⚠️" if "warning" in result else ""
                print(f"  {status} {test_name}: {response.status_code}{warning}")
                
            except Exception as e:
                result = {
                    "test": f"Input Validation - {test_name}",
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                self.results.append(result)
                print(f"  ❌ {test_name}: Error - {str(e)}")
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        print("🚦 Testing Rate Limiting...")
        
        headers = {"X-API-Key": self.valid_api_key, "Content-Type": "application/json"}
        
        try:
            # Send rapid requests to trigger rate limiting
            rapid_requests = 20
            response_codes = []
            
            start_time = time.time()
            for i in range(rapid_requests):
                response = requests.post(
                    f"{self.base_url}/chat",
                    headers=headers,
                    json={
                        "user_id": f"rate_test_{i}",
                        "message": f"Rate test message {i}"
                    },
                    timeout=5
                )
                response_codes.append(response.status_code)
            
            duration = time.time() - start_time
            
            # Check if rate limiting kicked in (429 status codes)
            rate_limited = any(code == 429 for code in response_codes)
            success_codes = sum(1 for code in response_codes if code == 200)
            
            result = {
                "test": "Rate Limiting",
                "total_requests": rapid_requests,
                "successful_requests": success_codes,
                "rate_limited": rate_limited,
                "total_duration": f"{duration:.2f}s",
                "requests_per_second": f"{rapid_requests/duration:.1f}",
                "response_codes": response_codes,
                "timestamp": datetime.now().isoformat()
            }
            
            self.results.append(result)
            
            if rate_limited:
                print(f"  ✅ Rate Limiting Active: {success_codes}/{rapid_requests} requests succeeded")
            else:
                print(f"  ⚠️  No Rate Limiting Detected: {success_codes}/{rapid_requests} requests succeeded")
            
        except Exception as e:
            result = {
                "test": "Rate Limiting",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(result)
            print(f"  ❌ Rate Limiting Test: Error - {str(e)}")
    
    def test_cors_and_security_headers(self):
        """Test CORS and security headers."""
        print("🔒 Testing CORS and Security Headers...")
        
        headers = {"X-API-Key": self.valid_api_key}
        
        try:
            # Test OPTIONS request (CORS preflight)
            options_response = requests.options(
                f"{self.base_url}/health/simple",
                headers=headers,
                timeout=10
            )
            
            # Test regular GET request for security headers
            get_response = requests.get(
                f"{self.base_url}/health/simple",
                headers=headers,
                timeout=10
            )
            
            # Check for important security headers
            security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options", 
                "X-XSS-Protection",
                "Strict-Transport-Security",
                "Content-Security-Policy"
            ]
            
            found_headers = []
            for header in security_headers:
                if header in get_response.headers:
                    found_headers.append(header)
            
            # Check CORS headers
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers"
            ]
            
            found_cors = []
            for header in cors_headers:
                if header in options_response.headers or header in get_response.headers:
                    found_cors.append(header)
            
            result = {
                "test": "Security Headers",
                "options_status": options_response.status_code,
                "get_status": get_response.status_code,
                "security_headers_found": found_headers,
                "cors_headers_found": found_cors,
                "total_security_headers": len(found_headers),
                "total_cors_headers": len(found_cors),
                "timestamp": datetime.now().isoformat()
            }
            
            self.results.append(result)
            
            print(f"  📋 Security Headers Found: {len(found_headers)}/{len(security_headers)}")
            print(f"  🌐 CORS Headers Found: {len(found_cors)}/{len(cors_headers)}")
            for header in found_headers:
                print(f"    ✅ {header}")
            
        except Exception as e:
            result = {
                "test": "Security Headers",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(result)
            print(f"  ❌ Security Headers Test: Error - {str(e)}")
    
    def test_error_information_disclosure(self):
        """Test that errors don't disclose sensitive information."""
        print("🕵️  Testing Error Information Disclosure...")
        
        error_scenarios = [
            ("Invalid JSON", "invalid json", "POST", "/chat"),
            ("Missing Fields", {}, "POST", "/chat"),
            ("Non-existent Endpoint", None, "GET", "/nonexistent"),
            ("Invalid Method", None, "DELETE", "/health"),
        ]
        
        headers = {"X-API-Key": self.valid_api_key, "Content-Type": "application/json"}
        
        for test_name, payload, method, endpoint in error_scenarios:
            try:
                if payload == "invalid json":
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        data="invalid json",
                        timeout=10
                    )
                elif payload is None:
                    response = requests.request(
                        method,
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        timeout=10
                    )
                else:
                    response = requests.request(
                        method,
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        json=payload,
                        timeout=10
                    )
                
                # Check for sensitive information in error responses
                sensitive_patterns = [
                    "traceback", "stack trace", "internal server error",
                    "database", "sql", "connection string", "password",
                    "secret", "token", "key", "file path", "/home/", "/etc/",
                    "exception", "error:", "failed to", "unable to"
                ]
                
                response_lower = response.text.lower()
                found_patterns = [p for p in sensitive_patterns if p in response_lower]
                
                result = {
                    "test": f"Error Disclosure - {test_name}",
                    "method": method,
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "sensitive_patterns_found": found_patterns,
                    "response_length": len(response.text),
                    "potential_disclosure": len(found_patterns) > 0,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.results.append(result)
                
                status = "⚠️" if found_patterns else "✅"
                print(f"  {status} {test_name}: {response.status_code}")
                if found_patterns:
                    print(f"    Found patterns: {', '.join(found_patterns[:3])}")
                
            except Exception as e:
                result = {
                    "test": f"Error Disclosure - {test_name}",
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                self.results.append(result)
                print(f"  ❌ {test_name}: Error - {str(e)}")
    
    def run_all_security_tests(self):
        """Run all security tests and generate report."""
        print("🔐 Starting Comprehensive Security & Authentication Tests")
        print("=" * 60)
        
        # Run all security test suites
        self.test_api_key_authentication()
        self.test_query_parameter_auth()
        self.test_input_validation()
        self.test_rate_limiting()
        self.test_cors_and_security_headers()
        self.test_error_information_disclosure()
        
        # Generate summary report
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.get("success", True))
        failed_tests = total_tests - passed_tests
        
        # Count warnings (potential security issues)
        warnings = sum(1 for r in self.results if "warning" in r or r.get("potential_disclosure", False))
        
        print("\n" + "=" * 60)
        print("🔐 SECURITY TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Security Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Warnings: {warnings}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        # Show failed tests and warnings
        issues = [r for r in self.results if not r.get("success", True) or "warning" in r or r.get("potential_disclosure", False)]
        if issues:
            print("\n⚠️  SECURITY ISSUES FOUND:")
            for result in issues:
                issue_type = "FAIL" if not result.get("success", True) else "WARNING"
                print(f"  - [{issue_type}] {result.get('test', 'Unknown test')}")
                if result.get("error"):
                    print(f"    Error: {result['error']}")
                if result.get("warning"):
                    print(f"    Warning: {result['warning']}")
                if result.get("potential_disclosure"):
                    print(f"    Potential info disclosure: {result.get('sensitive_patterns_found', [])}")
        
        # Save detailed report
        report_file = f"demo-test/security_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w') as f:
                json.dump({
                    "summary": {
                        "total_tests": total_tests,
                        "passed": passed_tests,
                        "failed": failed_tests,
                        "warnings": warnings,
                        "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
                    },
                    "results": self.results
                }, f, indent=2)
            print(f"\n📄 Detailed security test report saved: {report_file}")
        except Exception as e:
            print(f"\n⚠️  Could not save report: {e}")
        
        print("\n🏁 Security tests completed!")
        return failed_tests == 0 and warnings == 0


def main():
    """Run security tests."""
    suite = SecurityTestSuite()
    success = suite.run_all_security_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
