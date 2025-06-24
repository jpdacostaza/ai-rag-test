#!/usr/bin/env python3
"""
Tool Integration Test Suite
===========================

Focused testing for all AI tools in the backend system:
- Weather tool with different cities and error cases
- Time tool with various timezones and formats
- Math calculator with complex expressions
- Unit conversion with different units
- Web search with various queries
- Wikipedia search and content extraction
- Python code execution safety and security
- System information gathering

This module tests each tool individually and in combination.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests


class ToolTestSuite:
    """Comprehensive tool testing suite."""
    
    def __init__(self, base_url: str = "http://localhost:8001", 
                 api_key: str = "f2b985dd-219f-45b1-a90e-170962cc7082"):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        })
        self.results = []
    
    def test_tool(self, tool_name: str, test_message: str, expected_keywords: Optional[List[str]] = None) -> Dict:
        """Test individual tool with message."""
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{self.base_url}/chat",
                json={
                    "user_id": f"tool_test_{tool_name.lower()}",
                    "message": test_message
                },
                timeout=30
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")
                
                # Check for expected keywords if provided
                keyword_matches = []
                if expected_keywords:
                    for keyword in expected_keywords:
                        if keyword.lower() in response_text.lower():
                            keyword_matches.append(keyword)
                
                result = {
                    "tool": tool_name,
                    "message": test_message,
                    "success": True,
                    "response_length": len(response_text),
                    "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text,
                    "duration": f"{duration:.2f}s",
                    "keyword_matches": keyword_matches,
                    "expected_keywords": expected_keywords or [],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                result = {
                    "tool": tool_name,
                    "message": test_message,
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "duration": f"{duration:.2f}s",
                    "timestamp": datetime.now().isoformat()
                }
        
        except Exception as e:
            duration = time.time() - start_time
            result = {
                "tool": tool_name,
                "message": test_message,
                "success": False,
                "error": str(e),
                "duration": f"{duration:.2f}s",
                "timestamp": datetime.now().isoformat()
            }
        
        self.results.append(result)
        return result
    
    def test_weather_tool(self):
        """Test weather tool with various scenarios."""
        print("🌤️  Testing Weather Tool...")
        
        weather_tests = [
            ("London weather", "weather in London", ["London", "temperature", "humidity"]),
            ("New York weather", "What's the weather in New York?", ["New York", "temperature"]),
            ("Tokyo weather", "weather Tokyo", ["Tokyo"]),
            ("Multiple cities", "weather in Paris and Berlin", ["weather"]),
            ("Invalid city", "weather in Atlantis123", ["weather", "error", "not found"])
        ]
        
        for test_name, message, keywords in weather_tests:
            result = self.test_tool(f"Weather - {test_name}", message, keywords)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {test_name}: {result.get('duration', 'N/A')}")
    
    def test_time_tool(self):
        """Test time tool with various scenarios."""
        print("⏰ Testing Time Tool...")
        
        time_tests = [
            ("Current time", "What time is it?", ["time", ":"]),
            ("Tokyo time", "time in Tokyo", ["Tokyo", "time"]),
            ("London time", "What's the time in London?", ["London", "time"]),
            ("Amsterdam time", "time in Netherlands", ["Amsterdam", "time"]),
            ("Multiple timezones", "time in New York and Paris", ["time"]),
            ("Invalid timezone", "time in Middle Earth", ["time"])
        ]
        
        for test_name, message, keywords in time_tests:
            result = self.test_tool(f"Time - {test_name}", message, keywords)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {test_name}: {result.get('duration', 'N/A')}")
    
    def test_math_tool(self):
        """Test mathematical calculator."""
        print("🧮 Testing Math Tool...")
        
        math_tests = [
            ("Basic addition", "What is 2 + 2?", ["4"]),
            ("Complex calculation", "Calculate 15 + 25 * 3 - 10", ["80"]),
            ("Division", "What is 100 divided by 4?", ["25"]),
            ("Square root", "What is the square root of 144?", ["12"]),
            ("Percentage", "What is 25% of 200?", ["50"]),
            ("Scientific notation", "Calculate 2.5e3 + 1000", ["3500"]),
            ("Invalid expression", "Calculate abc + xyz", ["error", "invalid"])
        ]
        
        for test_name, message, keywords in math_tests:
            result = self.test_tool(f"Math - {test_name}", message, keywords)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {test_name}: {result.get('duration', 'N/A')}")
    
    def test_conversion_tool(self):
        """Test unit conversion tool."""
        print("🔄 Testing Unit Conversion Tool...")
        
        conversion_tests = [
            ("Distance km to miles", "Convert 100 km to miles", ["62", "miles"]),
            ("Temperature C to F", "Convert 25 celsius to fahrenheit", ["77", "fahrenheit"]),
            ("Weight kg to lbs", "Convert 10 kg to pounds", ["22", "pounds"]),
            ("Volume liters to gallons", "Convert 5 liters to gallons", ["gallon"]),
            ("Invalid units", "Convert 10 dragons to unicorns", ["error", "invalid"])
        ]
        
        for test_name, message, keywords in conversion_tests:
            result = self.test_tool(f"Conversion - {test_name}", message, keywords)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {test_name}: {result.get('duration', 'N/A')}")
    
    def test_web_search_tool(self):
        """Test web search functionality."""
        print("🔍 Testing Web Search Tool...")
        
        search_tests = [
            ("Tech search", "Search for artificial intelligence", ["AI", "artificial", "intelligence"]),
            ("News search", "Search for recent technology news", ["technology", "news"]),
            ("Specific query", "Search Python programming tutorial", ["Python", "programming"]),
            ("Empty query", "Search for", ["search"])
        ]
        
        for test_name, message, keywords in search_tests:
            result = self.test_tool(f"Search - {test_name}", message, keywords)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {test_name}: {result.get('duration', 'N/A')}")
    
    def test_wikipedia_tool(self):
        """Test Wikipedia search and content extraction."""
        print("📚 Testing Wikipedia Tool...")
        
        wiki_tests = [
            ("AI article", "Tell me about artificial intelligence on Wikipedia", ["artificial intelligence", "AI"]),
            ("Science topic", "Wikipedia machine learning", ["machine learning", "algorithm"]),
            ("Historical topic", "Tell me about World War 2 from Wikipedia", ["World War", "1939", "1945"]),
            ("Invalid topic", "Wikipedia about xyz123nonexistent", ["Wikipedia"])
        ]
        
        for test_name, message, keywords in wiki_tests:
            result = self.test_tool(f"Wikipedia - {test_name}", message, keywords)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {test_name}: {result.get('duration', 'N/A')}")
    
    def test_python_execution_tool(self):
        """Test Python code execution with safety checks."""
        print("🐍 Testing Python Execution Tool...")
        
        python_tests = [
            ("Simple print", "Run Python: print('Hello World')", ["Hello World"]),
            ("Math calculation", "Python: result = 10 * 5; print(result)", ["50"]),
            ("List operations", "Python: numbers = [1,2,3]; print(sum(numbers))", ["6"]),
            ("String manipulation", "Python: text = 'hello'; print(text.upper())", ["HELLO"]),
            ("Dangerous code", "Python: import os; os.system('rm -rf /')", ["error", "restricted"])
        ]
        
        for test_name, message, keywords in python_tests:
            result = self.test_tool(f"Python - {test_name}", message, keywords)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {test_name}: {result.get('duration', 'N/A')}")
    
    def test_system_info_tool(self):
        """Test system information gathering."""
        print("💻 Testing System Info Tool...")
        
        system_tests = [
            ("Basic system info", "Show me system info", ["system", "CPU", "memory"]),
            ("Server status", "What's the server status?", ["server", "status"])
        ]
        
        for test_name, message, keywords in system_tests:
            result = self.test_tool(f"System - {test_name}", message, keywords)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {test_name}: {result.get('duration', 'N/A')}")
    
    def run_all_tool_tests(self):
        """Run all tool tests and generate report."""
        print("🔧 Starting Comprehensive Tool Integration Tests")
        print("=" * 50)
        
        # Run all tool test suites
        self.test_weather_tool()
        self.test_time_tool()
        self.test_math_tool()
        self.test_conversion_tool()
        self.test_web_search_tool()
        self.test_wikipedia_tool()
        self.test_python_execution_tool()
        self.test_system_info_tool()
        
        # Generate summary report
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 50)
        print("🔧 TOOL TEST RESULTS SUMMARY")
        print("=" * 50)
        print(f"Total Tool Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        # Show failed tests
        failed_results = [r for r in self.results if not r["success"]]
        if failed_results:
            print("\n❌ FAILED TOOL TESTS:")
            for result in failed_results:
                print(f"  - {result['tool']}: {result.get('error', 'Unknown error')}")
        
        # Save detailed report
        report_file = f"demo-test/tool_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w') as f:
                json.dump({
                    "summary": {
                        "total_tests": total_tests,
                        "passed": passed_tests,
                        "failed": failed_tests,
                        "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
                    },
                    "results": self.results
                }, f, indent=2)
            print(f"\n📄 Detailed tool test report saved: {report_file}")
        except Exception as e:
            print(f"\n⚠️  Could not save report: {e}")
        
        print("\n🏁 Tool integration tests completed!")
        return failed_tests == 0


def main():
    """Run tool integration tests."""
    suite = ToolTestSuite()
    success = suite.run_all_tool_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
