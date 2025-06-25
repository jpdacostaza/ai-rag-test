#!/usr/bin/env python3
"""
Final Web Search Integration Validation Test
Tests the complete web search integration in the chat endpoint.
"""

import asyncio
import sys
import time
import requests
import json

BASE_URL = "http://localhost:9099"

def test_backend_startup():
    """Test if backend starts successfully with web search integration"""
    print("🚀 Testing Backend Startup with Web Search Integration")
    print("=" * 60)
    
    try:
        # Test health endpoint
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend health check passed")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not responding: {e}")
        return False

def test_web_search_triggers():
    """Test various web search trigger scenarios"""
    print("\n🔍 Testing Web Search Trigger Scenarios")
    print("=" * 60)
    
    test_scenarios = [
        {
            "message": "What's the current weather in Tokyo?",
            "description": "Current information query",
            "should_trigger": True
        },
        {
            "message": "Who is the president of Brazil?", 
            "description": "Factual lookup query",
            "should_trigger": True
        },
        {
            "message": "Hello, how are you?",
            "description": "Casual greeting",
            "should_trigger": False
        },
        {
            "message": "What's happening in AI news today?",
            "description": "Current events query", 
            "should_trigger": True
        },
        {
            "message": "Calculate 15 * 23",
            "description": "Math calculation",
            "should_trigger": False
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. Testing: {scenario['description']}")
        print(f"   Query: '{scenario['message']}'")
        
        try:
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/chat", json={
                "user_id": f"web_test_user_{i}",
                "message": scenario["message"],
                "model": "llama3.2:3b"
            }, timeout=45)
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                response_text = response.json().get("response", "")
                
                # Check for web search indicators
                has_web_info = any(indicator in response_text.lower() for indicator in [
                    "i found", "recent information", "source:", "search", "web"
                ])
                
                print(f"   ✅ Response received in {duration:.1f}s")
                print(f"   📝 Response length: {len(response_text)} chars")
                print(f"   🔍 Web search indicators: {'Yes' if has_web_info else 'No'}")
                
                if scenario["should_trigger"] and has_web_info:
                    print(f"   ✅ Correctly triggered web search")
                    results.append("pass")
                elif not scenario["should_trigger"] and not has_web_info:
                    print(f"   ✅ Correctly did not trigger web search")
                    results.append("pass")
                else:
                    print(f"   ⚠️  Unexpected web search behavior")
                    results.append("partial")
                    
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                results.append("fail")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}...")
            results.append("error")
        
        # Brief pause between requests
        time.sleep(2)
    
    # Analyze results
    success_count = results.count("pass")
    total_count = len(results)
    
    print(f"\n📊 Web Search Trigger Test Results:")
    print(f"   Passed: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    return success_count >= total_count * 0.8  # 80% success rate

def test_uncertainty_handling():
    """Test how the system handles uncertain responses"""
    print("\n🤔 Testing Uncertainty Handling")
    print("=" * 60)
    
    # Use a very specific query that might trigger uncertainty
    uncertainty_query = "What happened in the news today regarding quantum computing breakthroughs?"
    
    try:
        response = requests.post(f"{BASE_URL}/chat", json={
            "user_id": "uncertainty_test_user",
            "message": uncertainty_query,
            "model": "llama3.2:3b"
        }, timeout=60)
        
        if response.status_code == 200:
            response_text = response.json().get("response", "")
            
            # Check for uncertainty indicators or web search enhancement
            has_uncertainty = any(phrase in response_text.lower() for phrase in [
                "i don't know", "i'm not sure", "i don't have", "not aware"
            ])
            
            has_web_enhancement = any(phrase in response_text.lower() for phrase in [
                "i found", "recent information", "search results", "source:"
            ])
            
            print(f"✅ Uncertainty query processed")
            print(f"📝 Response length: {len(response_text)} chars")
            print(f"🤔 Uncertainty detected: {'Yes' if has_uncertainty else 'No'}")
            print(f"🔍 Web enhancement: {'Yes' if has_web_enhancement else 'No'}")
            
            if has_web_enhancement:
                print("✅ System successfully enhanced uncertain response with web search")
                return True
            elif not has_uncertainty:
                print("✅ System provided confident response without uncertainty")
                return True
            else:
                print("⚠️  System showed uncertainty but didn't enhance with web search")
                return False
                
        else:
            print(f"❌ Uncertainty test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Uncertainty test error: {e}")
        return False

def generate_final_report():
    """Generate final validation report"""
    print("\n📋 Final Integration Validation Report")
    print("=" * 60)
    
    # Run all tests
    backend_ok = test_backend_startup()
    triggers_ok = test_web_search_triggers()
    uncertainty_ok = test_uncertainty_handling()
    
    # Calculate overall score
    total_tests = 3
    passed_tests = sum([backend_ok, triggers_ok, uncertainty_ok])
    success_rate = passed_tests / total_tests * 100
    
    print(f"\n🎯 FINAL VALIDATION RESULTS")
    print(f"=" * 30)
    print(f"Backend Startup: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"Web Search Triggers: {'✅ PASS' if triggers_ok else '❌ FAIL'}")
    print(f"Uncertainty Handling: {'✅ PASS' if uncertainty_ok else '❌ FAIL'}")
    print(f"\nOverall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    
    if success_rate >= 80:
        print("🎉 WEB SEARCH INTEGRATION: SUCCESSFULLY VALIDATED ✅")
        status = "SUCCESS"
    else:
        print("⚠️  WEB SEARCH INTEGRATION: NEEDS ATTENTION")
        status = "NEEDS_WORK"
    
    # Save results
    report_data = {
        "timestamp": time.time(),
        "validation_results": {
            "backend_startup": backend_ok,
            "web_search_triggers": triggers_ok,
            "uncertainty_handling": uncertainty_ok
        },
        "overall_success_rate": success_rate,
        "status": status,
        "recommendations": []
    }
    
    if not backend_ok:
        report_data["recommendations"].append("Backend startup issues need investigation")
    if not triggers_ok:
        report_data["recommendations"].append("Web search trigger logic needs refinement")
    if not uncertainty_ok:
        report_data["recommendations"].append("Uncertainty detection and handling needs improvement")
    
    with open("web_search_integration_validation.json", "w") as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n📁 Detailed report saved to: web_search_integration_validation.json")
    
    return success_rate >= 80

if __name__ == "__main__":
    print("🔍 Web Search Integration Final Validation")
    print("=" * 70)
    print("Testing the complete web search integration in production setup")
    print()
    
    is_validated = generate_final_report()
    
    if is_validated:
        print("\n🚀 WEB SEARCH INTEGRATION VALIDATION: COMPLETE ✅")
        print("🎯 System is ready for production deployment with web search capabilities")
    else:
        print("\n🔧 WEB SEARCH INTEGRATION VALIDATION: INCOMPLETE ⚠️")
        print("🔍 Review the test results and address any issues before deployment")
    
    sys.exit(0 if is_validated else 1)
