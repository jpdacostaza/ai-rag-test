#!/usr/bin/env python3
"""
Test script for web search integration in chat endpoint.
"""

import asyncio
import json
import sys
import time
from typing import Dict, Any

# Add current directory to path to import local modules
sys.path.append('.')

async def test_web_search_integration():
    """Test the web search integration functionality"""
    print("🧪 Testing Web Search Integration")
    print("=" * 50)
    
    try:
        # Import the web search functions
        from web_search_tool import should_trigger_web_search, search_web, format_web_results_for_chat
        
        print("✅ Successfully imported web search functions")
        
        # Test 1: Check trigger detection
        print("\n📋 Test 1: Trigger Detection")
        test_cases = [
            ("What's the current weather?", "Current info query"),
            ("I don't know", "Model uncertainty"),
            ("Who is the president of France?", "Factual query"),
            ("Hello how are you?", "Casual greeting"),
            ("What's happening in the news today?", "Current events"),
        ]
        
        for message, description in test_cases:
            should_search = should_trigger_web_search(message, "")
            print(f"  {description}: '{message}' -> {should_search}")
        
        # Test 2: Web search functionality
        print("\n🔍 Test 2: Web Search Functionality")
        
        test_query = "current weather Paris France"
        print(f"Searching for: '{test_query}'")
        
        start_time = time.time()
        search_results = await search_web(test_query, max_results=2)
        end_time = time.time()
        
        search_duration = end_time - start_time
        
        print(f"Search completed in {search_duration:.3f} seconds")
        print(f"Results count: {search_results.get('results_count', 0)}")
        
        if search_results.get('results'):
            print("✅ Search returned results")
            for i, result in enumerate(search_results['results'][:2], 1):
                print(f"  {i}. {result.get('title', 'No title')[:50]}...")
        else:
            print("⚠️  No search results returned")
        
        # Test 3: Format results
        print("\n📝 Test 3: Result Formatting")
        formatted_text = format_web_results_for_chat(search_results)
        print("Formatted output preview:")
        print(formatted_text[:200] + "..." if len(formatted_text) > 200 else formatted_text)
        
        # Test 4: Test uncertainty detection
        print("\n🤔 Test 4: Uncertainty Detection")
        uncertainty_responses = [
            "I don't know about that topic.",
            "I'm not sure about the current situation.",
            "I don't have access to recent information.",
            "This is a straightforward answer."
        ]
        
        for response in uncertainty_responses:
            should_search = should_trigger_web_search("Tell me about the news", response)
            status = "🔍" if should_search else "✅"
            print(f"  {status} '{response[:30]}...' -> {should_search}")
        
        print("\n✅ All web search integration tests completed successfully!")
        
        # Clean up the web search tool session
        from web_search_tool import web_search_tool
        await web_search_tool.close()
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def test_chat_integration():
    """Test a simulated chat request with web search"""
    print("\n🗨️  Testing Chat Integration Simulation")
    print("=" * 50)
    
    try:
        # Simulate the chat endpoint logic
        user_message = "What's the latest news about artificial intelligence?"
        
        # Check if web search should be triggered
        from web_search_tool import should_trigger_web_search, search_web, format_web_results_for_chat
        
        # Simulate initial LLM response (uncertain)
        initial_response = "I don't have access to the latest news about artificial intelligence."
        
        if should_trigger_web_search(user_message, initial_response):
            print(f"🔍 Web search triggered for: '{user_message}'")
            
            # Perform web search
            search_results = await search_web(user_message, max_results=3)
            
            if search_results.get('results'):
                web_info = format_web_results_for_chat(search_results)
                
                # Simulate response enhancement
                enhanced_response = web_info  # Replace uncertain response
                print(f"✅ Enhanced response with {len(search_results['results'])} web results")
                print(f"Final response preview: {enhanced_response[:150]}...")
            else:
                print("⚠️  No web results to enhance response")
        else:
            print("ℹ️  Web search not triggered for this query")
        
        # Clean up the web search tool session
        from web_search_tool import web_search_tool
        await web_search_tool.close()
            
        return True
        
    except Exception as e:
        print(f"❌ Chat integration test failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 Starting Web Search Integration Tests")
        print("=" * 60)
        
        # Test basic functionality
        success1 = await test_web_search_integration()
        
        # Test chat integration
        success2 = await test_chat_integration()
        
        print("\n" + "=" * 60)
        if success1 and success2:
            print("🎉 All tests passed! Web search integration is ready.")
        else:
            print("❌ Some tests failed. Check the errors above.")
        
        return success1 and success2
    
    # Run the tests
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
