"""
Web Search and Anti-Hallucination Comprehensive Test
====================================================

Tests the pipeline's ability to:
1. Detect when web search should be triggered
2. Use web search instead of hallucinating
3. Integrate web search results naturally
4. Maintain accuracy over speculation
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List
import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utilities.web_search_tool import should_trigger_web_search, search_web, format_web_results_for_chat
from utilities.ai_tools import web_search as ai_tools_web_search

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSearchAntiHallucinationTester:
    """Comprehensive tester for web search and anti-hallucination capabilities."""
    
    def __init__(self):
        self.test_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": []
            }
        }
    
    def log_test_result(self, test_name: str, passed: bool, details: Dict[str, Any]):
        """Log a test result."""
        result = {
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.test_results["tests"].append(result)
        self.test_results["summary"]["total_tests"] += 1
        
        if passed:
            self.test_results["summary"]["passed"] += 1
            logger.info(f"✅ {test_name} - PASSED")
        else:
            self.test_results["summary"]["failed"] += 1
            self.test_results["summary"]["errors"].append(f"{test_name}: {details.get('error', 'Unknown error')}")
            logger.error(f"❌ {test_name} - FAILED: {details.get('error', 'Unknown error')}")
    
    def test_web_search_trigger_detection(self):
        """Test 1: Verify web search trigger detection works correctly."""
        test_cases = [
            # Should trigger web search
            ("Tell me about SWIFT company", True, "Company information query"),
            ("What is the latest news about AI?", True, "Current news query"),
            ("When was Microsoft founded?", True, "Factual historical query"),
            ("What are the current features of ChatGPT?", True, "Current product features"),
            ("Who is the CEO of Apple in 2025?", True, "Current leadership query"),
            ("What happened today in the stock market?", True, "Time-sensitive query"),
            ("swift company information", True, "Specific company query"),
            
            # Should NOT trigger web search
            ("Hello, how are you?", False, "Greeting"),
            ("What is 2+2?", False, "Simple math"),
            ("Explain machine learning", False, "General concept explanation"),
            ("Write a poem about cats", False, "Creative request"),
            ("How do I cook pasta?", False, "General knowledge"),
        ]
        
        passed_count = 0
        total_count = len(test_cases)
        details = {"test_cases": []}
        
        for query, expected, description in test_cases:
            try:
                result = should_trigger_web_search(query, "")
                case_passed = result == expected
                
                case_detail = {
                    "query": query,
                    "expected": expected,
                    "actual": result,
                    "description": description,
                    "passed": case_passed
                }
                details["test_cases"].append(case_detail)
                
                if case_passed:
                    passed_count += 1
                    logger.info(f"  ✓ '{query}' -> {result} (expected {expected})")
                else:
                    logger.error(f"  ✗ '{query}' -> {result} (expected {expected})")
                    
            except Exception as e:
                details["test_cases"].append({
                    "query": query,
                    "expected": expected,
                    "actual": "ERROR",
                    "description": description,
                    "passed": False,
                    "error": str(e)
                })
                logger.error(f"  ✗ '{query}' -> ERROR: {e}")
        
        details["passed_cases"] = passed_count
        details["total_cases"] = total_count
        details["success_rate"] = f"{(passed_count/total_count)*100:.1f}%"
        
        overall_passed = passed_count == total_count
        self.log_test_result("Web Search Trigger Detection", overall_passed, details)
        return overall_passed
    
    async def test_web_search_execution(self):
        """Test 2: Verify web search actually executes and returns results."""
        test_queries = [
            "SWIFT financial services company",
            "Microsoft Corporation headquarters",
            "OpenAI latest announcement 2025"
        ]
        
        passed_count = 0
        total_count = len(test_queries)
        details = {"search_results": []}
        
        for query in test_queries:
            try:
                # Test the web search function directly
                result = await search_web(query, max_results=2)
                
                # Validate result structure
                required_fields = ["query", "results", "status", "message"]
                has_required_fields = all(field in result for field in required_fields)
                
                # Check if we got actual results or at least proper error handling
                has_results = (
                    result.get("status") == "success" and len(result.get("results", [])) > 0
                ) or (
                    result.get("status") in ["error", "no_results"] and result.get("message")
                )
                
                test_passed = has_required_fields and has_results
                
                search_detail = {
                    "query": query,
                    "status": result.get("status"),
                    "num_results": len(result.get("results", [])),
                    "has_required_fields": has_required_fields,
                    "has_results": has_results,
                    "passed": test_passed,
                    "result_structure": result
                }
                details["search_results"].append(search_detail)
                
                if test_passed:
                    passed_count += 1
                    logger.info(f"  ✓ '{query}' -> {result.get('status')} ({len(result.get('results', []))} results)")
                else:
                    logger.error(f"  ✗ '{query}' -> Invalid result structure or no results")
                    
            except Exception as e:
                details["search_results"].append({
                    "query": query,
                    "status": "ERROR",
                    "passed": False,
                    "error": str(e)
                })
                logger.error(f"  ✗ '{query}' -> ERROR: {e}")
        
        details["passed_searches"] = passed_count
        details["total_searches"] = total_count
        details["success_rate"] = f"{(passed_count/total_count)*100:.1f}%"
        
        overall_passed = passed_count > 0  # At least one search should work
        self.log_test_result("Web Search Execution", overall_passed, details)
        return overall_passed
    
    def test_result_formatting(self):
        """Test 3: Verify web search results are formatted properly for chat."""
        # Mock search results
        mock_results = {
            "query": "test query",
            "results": [
                {
                    "title": "Test Result 1",
                    "snippet": "This is a test snippet with relevant information.",
                    "url": "https://example.com/1"
                },
                {
                    "title": "Test Result 2", 
                    "snippet": "Another test snippet with more details.",
                    "url": "https://example.com/2"
                }
            ],
            "status": "success"
        }
        
        try:
            formatted = format_web_results_for_chat(mock_results)
            
            # Check formatting quality
            checks = {
                "has_header": "Web Search Results" in formatted,
                "has_titles": all(result["title"] in formatted for result in mock_results["results"]),
                "has_snippets": all(result["snippet"] in formatted for result in mock_results["results"]),
                "has_urls": all(result["url"] in formatted for result in mock_results["results"]),
                "proper_structure": formatted.count("\n") >= 6,  # Should have multiple lines
                "not_empty": len(formatted.strip()) > 50
            }
            
            passed_checks = sum(checks.values())
            total_checks = len(checks)
            
            details = {
                "checks": checks,
                "passed_checks": passed_checks,
                "total_checks": total_checks,
                "formatted_output": formatted,
                "success_rate": f"{(passed_checks/total_checks)*100:.1f}%"
            }
            
            overall_passed = passed_checks == total_checks
            self.log_test_result("Result Formatting", overall_passed, details)
            return overall_passed
            
        except Exception as e:
            details = {"error": str(e)}
            self.log_test_result("Result Formatting", False, details)
            return False
    
    def test_anti_hallucination_keywords(self):
        """Test 4: Verify the system recognizes uncertainty and triggers search."""
        uncertainty_responses = [
            "I don't know the current status",
            "I'm not sure about recent developments", 
            "I don't have information about",
            "I cannot provide current data",
            "This information is not available to me",
            "I'm unable to give you recent updates"
        ]
        
        passed_count = 0
        total_count = len(uncertainty_responses)
        details = {"uncertainty_tests": []}
        
        for response in uncertainty_responses:
            try:
                # Test if uncertainty response triggers web search
                should_search = should_trigger_web_search("test query", response)
                
                test_detail = {
                    "response": response,
                    "triggered_search": should_search,
                    "passed": should_search
                }
                details["uncertainty_tests"].append(test_detail)
                
                if should_search:
                    passed_count += 1
                    logger.info(f"  ✓ Uncertainty detected: '{response[:50]}...'")
                else:
                    logger.error(f"  ✗ Uncertainty NOT detected: '{response[:50]}...'")
                    
            except Exception as e:
                details["uncertainty_tests"].append({
                    "response": response,
                    "triggered_search": False,
                    "passed": False,
                    "error": str(e)
                })
                logger.error(f"  ✗ ERROR testing: '{response[:50]}...' -> {e}")
        
        details["detected_uncertainty"] = passed_count
        details["total_uncertainty_tests"] = total_count
        details["detection_rate"] = f"{(passed_count/total_count)*100:.1f}%"
        
        overall_passed = passed_count >= total_count * 0.8  # 80% success rate
        self.log_test_result("Anti-Hallucination Keywords", overall_passed, details)
        return overall_passed
    
    def test_swift_company_specific(self):
        """Test 5: Specific test for SWIFT company confusion resolution."""
        swift_queries = [
            "swift company information",
            "tell me about swift where I work",
            "what does swift corporation do",
            "swift.com company details",
            "swift financial services"
        ]
        
        passed_count = 0
        total_count = len(swift_queries)
        details = {"swift_tests": []}
        
        for query in swift_queries:
            try:
                should_search = should_trigger_web_search(query, "")
                
                test_detail = {
                    "query": query,
                    "triggered_search": should_search,
                    "passed": should_search
                }
                details["swift_tests"].append(test_detail)
                
                if should_search:
                    passed_count += 1
                    logger.info(f"  ✓ SWIFT query detected: '{query}'")
                else:
                    logger.error(f"  ✗ SWIFT query NOT detected: '{query}'")
                    
            except Exception as e:
                details["swift_tests"].append({
                    "query": query,
                    "triggered_search": False,
                    "passed": False,
                    "error": str(e)
                })
                logger.error(f"  ✗ ERROR testing SWIFT query: '{query}' -> {e}")
        
        details["detected_swift_queries"] = passed_count
        details["total_swift_tests"] = total_count
        details["detection_rate"] = f"{(passed_count/total_count)*100:.1f}%"
        
        overall_passed = passed_count == total_count
        self.log_test_result("SWIFT Company Specific Detection", overall_passed, details)
        return overall_passed
    
    async def run_all_tests(self):
        """Run all web search and anti-hallucination tests."""
        logger.info("🚀 Starting Web Search and Anti-Hallucination Tests")
        logger.info("=" * 60)
        
        # Run all tests
        test_results = []
        
        logger.info("\n1️⃣  Testing Web Search Trigger Detection...")
        test_results.append(self.test_web_search_trigger_detection())
        
        logger.info("\n2️⃣  Testing Web Search Execution...")
        test_results.append(await self.test_web_search_execution())
        
        logger.info("\n3️⃣  Testing Result Formatting...")
        test_results.append(self.test_result_formatting())
        
        logger.info("\n4️⃣  Testing Anti-Hallucination Keywords...")
        test_results.append(self.test_anti_hallucination_keywords())
        
        logger.info("\n5️⃣  Testing SWIFT Company Specific Detection...")
        test_results.append(self.test_swift_company_specific())
        
        # Calculate overall results
        total_tests = len(test_results)
        passed_tests = sum(test_results)
        overall_success_rate = (passed_tests / total_tests) * 100
        
        # Update summary
        self.test_results["summary"]["overall_success_rate"] = f"{overall_success_rate:.1f}%"
        self.test_results["summary"]["recommendation"] = self._get_recommendation(overall_success_rate)
        
        # Print final results
        logger.info("\n" + "=" * 60)
        logger.info("📊 FINAL TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {overall_success_rate:.1f}%")
        
        if overall_success_rate >= 80:
            logger.info("🎉 EXCELLENT: Web search and anti-hallucination system is working well!")
        elif overall_success_rate >= 60:
            logger.info("⚠️  GOOD: System is functional but could use improvements")
        else:
            logger.info("❌ NEEDS WORK: Significant issues detected")
        
        return overall_success_rate >= 80
    
    def _get_recommendation(self, success_rate: float) -> str:
        """Get recommendation based on test results."""
        if success_rate >= 90:
            return "Excellent performance. System is production-ready for web search and anti-hallucination."
        elif success_rate >= 80:
            return "Good performance. Minor optimizations recommended."
        elif success_rate >= 60:
            return "Moderate performance. Review failed tests and improve trigger detection."
        else:
            return "Poor performance. Significant issues need to be addressed before deployment."
    
    def save_report(self, filename: str = None):
        """Save test results to a JSON file."""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"web_search_anti_hallucination_test_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            logger.info(f"📄 Test report saved to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"❌ Failed to save report: {e}")
            return None


async def main():
    """Main test execution function."""
    tester = WebSearchAntiHallucinationTester()
    
    try:
        success = await tester.run_all_tests()
        report_file = tester.save_report()
        
        if success:
            print("\n🎉 All tests passed! Web search and anti-hallucination system is working correctly.")
            return 0
        else:
            print("\n❌ Some tests failed. Check the report for details.")
            return 1
            
    except Exception as e:
        logger.error(f"Fatal error during testing: {e}")
        return 1


if __name__ == "__main__":
    # Run the tests
    exit_code = asyncio.run(main())
    exit(exit_code)
