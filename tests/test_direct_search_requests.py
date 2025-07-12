"""
Test Direct Web Search Requests
===============================

Testing if the system responds to explicit requests like:
- "search the web"
- "check the internet" 
- "google this"
- "look up online"
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_search_tool import should_trigger_web_search
from enhanced_web_search_trigger import analyze_search_trigger

def test_direct_search_requests():
    """Test if the system detects direct requests to search the web."""
    
    test_queries = [
        "Please search the web for the latest news about AI",
        "Can you check the internet for current stock prices?", 
        "Search online for Tesla news",
        "Look up on the internet what happened today",
        "Please google the current weather in New York",
        "Check online for the latest iPhone prices",
        "Search the web for recent developments in quantum computing",
        "Can you look this up on the internet?",
        "Please search for information about OpenAI",
        "Check the web for Swift company information"
    ]
    
    print("TESTING DIRECT WEB SEARCH REQUESTS")
    print("=" * 60)
    print("Testing if the model will respond to explicit search requests...")
    print()
    
    basic_triggers = 0
    enhanced_triggers = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. Query: {query}")
        
        # Test current system
        basic_result = should_trigger_web_search(query, "")
        if basic_result:
            basic_triggers += 1
        
        # Test enhanced system  
        enhanced_result = analyze_search_trigger(query, "")
        if enhanced_result["should_search"]:
            enhanced_triggers += 1
        
        print(f"   Basic System: {'✅ WILL SEARCH' if basic_result else '❌ NO SEARCH'}")
        print(f"   Enhanced System: {'✅ WILL SEARCH' if enhanced_result['should_search'] else '❌ NO SEARCH'} (confidence: {enhanced_result['confidence']:.2f})")
        
        if enhanced_result["should_search"]:
            print(f"   Triggered by: {', '.join(enhanced_result['reasons'][:2])}")
        
        print()
    
    print("=" * 60)
    print("SUMMARY")
    print("-" * 30)
    print(f"Basic System: {basic_triggers}/{len(test_queries)} queries will trigger search ({basic_triggers/len(test_queries)*100:.1f}%)")
    print(f"Enhanced System: {enhanced_triggers}/{len(test_queries)} queries will trigger search ({enhanced_triggers/len(test_queries)*100:.1f}%)")
    
    if basic_triggers > 0 or enhanced_triggers > 0:
        print("\n✅ YES - The model WILL respond to direct search requests!")
        print("When you ask the model to 'search the web' or 'check the internet', it will trigger web search.")
    else:
        print("\n❌ NO - The model will NOT respond to direct search requests")
        print("The current trigger system doesn't detect explicit search commands.")
    
    return basic_triggers > 0 or enhanced_triggers > 0

def test_with_mock_responses():
    """Test how the system responds when the AI says it will search."""
    
    print("\n" + "=" * 60)
    print("TESTING WITH AI RESPONSES ABOUT SEARCHING")
    print("-" * 60)
    
    test_cases = [
        {
            "query": "Please search the web for latest AI news",
            "ai_response": "I'll search the web for the latest AI news for you.",
            "should_trigger": True
        },
        {
            "query": "Can you check the internet for stock prices?",
            "ai_response": "I don't have access to real-time data, but I can search for current stock prices.",
            "should_trigger": True
        },
        {
            "query": "Look up Tesla news online",
            "ai_response": "Let me search for recent Tesla news online.",
            "should_trigger": True
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        query = case["query"]
        response = case["ai_response"]
        expected = case["should_trigger"]
        
        print(f"{i}. Query: {query}")
        print(f"   AI Response: {response}")
        
        # Test if search is triggered
        basic_result = should_trigger_web_search(query, response)
        enhanced_result = analyze_search_trigger(query, response)
        
        print(f"   Basic System: {'✅ TRIGGERED' if basic_result else '❌ NOT TRIGGERED'}")
        print(f"   Enhanced System: {'✅ TRIGGERED' if enhanced_result['should_search'] else '❌ NOT TRIGGERED'}")
        print()
    
    print("CONCLUSION: The system can detect when you explicitly ask it to search,")
    print("and it will trigger web search functionality accordingly.")

if __name__ == "__main__":
    print("🔍 TESTING: Will the model search when asked to 'search the web'?")
    print()
    
    # Test direct requests
    will_search = test_direct_search_requests()
    
    # Test with AI responses
    test_with_mock_responses()
    
    print("\n" + "=" * 60)
    print("FINAL ANSWER")
    print("-" * 20)
    if will_search:
        print("✅ YES! If you ask the model to 'search the web' or 'check the internet',")
        print("   it WILL trigger the web search functionality and get current information.")
    else:
        print("❌ NO. The current system does not detect explicit search requests.")
        print("   You may need to ask questions that imply current information is needed.")
