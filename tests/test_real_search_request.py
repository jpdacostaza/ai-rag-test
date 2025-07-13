"""
Real-World Web Search Test
=========================
Testing what happens when you actually ask the model to search the web.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utilities.web_search_tool import should_trigger_web_search, search_web, format_web_results_for_chat

def test_real_search_request():
    """Test what happens when you ask the model to search."""
    
    print("REAL-WORLD WEB SEARCH TEST")
    print("=" * 50)
    
    # Simulate a real conversation
    user_query = "Please search the web for the latest news about OpenAI"
    ai_response = "I'll search the web for the latest OpenAI news for you."
    
    print(f"User: {user_query}")
    print(f"AI: {ai_response}")
    print()
    
    # Check if search is triggered
    should_search = should_trigger_web_search(user_query, ai_response)
    print(f"Will trigger web search: {'✅ YES' if should_search else '❌ NO'}")
    
    if should_search:
        print("\nExecuting web search...")
        try:
            # Perform actual web search
            search_results = search_web("OpenAI latest news 2025")
            
            if search_results and 'results' in search_results:
                print(f"✅ Found {len(search_results['results'])} results")
                
                # Show first result
                if search_results['results']:
                    first_result = search_results['results'][0]
                    print(f"\nFirst result:")
                    print(f"  Title: {first_result.get('title', 'No title')}")
                    print(f"  URL: {first_result.get('url', 'No URL')}")
                    print(f"  Snippet: {first_result.get('snippet', 'No snippet')[:100]}...")
                
                # Format for chat response
                formatted = format_web_results_for_chat(search_results)
                print(f"\nFormatted response length: {len(formatted)} characters")
                print(f"Preview: {formatted[:150]}...")
                
                return True
            else:
                print("❌ No results returned")
                return False
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return False
    else:
        print("❌ Search would not be triggered by current system")
        return False

if __name__ == "__main__":
    success = test_real_search_request()
    
    print("\n" + "=" * 50)
    print("CONCLUSION")
    print("-" * 20)
    if success:
        print("✅ YES! When you ask the model to search the web:")
        print("   1. The system detects the search request")
        print("   2. Web search is triggered automatically") 
        print("   3. Real results are retrieved from the internet")
        print("   4. Results are formatted for the conversation")
        print("\n🎉 The web search integration is fully functional!")
    else:
        print("❌ The web search request was not processed successfully")
        print("   Check the trigger logic or search functionality")
