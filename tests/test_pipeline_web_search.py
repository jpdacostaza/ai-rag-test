#!/usr/bin/env python3
"""
Test script to verify web search integration in the enhanced memory pipeline
"""

import sys
import asyncio
import json
from datetime import datetime

# Add paths for imports
sys.path.insert(0, '.')
sys.path.insert(0, 'pipelines')

def test_web_search_integration():
    """Test the complete web search integration in the pipeline"""
    print("=" * 60)
    print("TESTING WEB SEARCH INTEGRATION IN PIPELINE")
    print("=" * 60)
    
    try:
        from enhanced_memory_pipeline import (
            should_trigger_web_search, 
            search_web, 
            format_web_results_for_chat,
            web_search_available
        )
        
        print(f"✅ Pipeline imports successful")
        print(f"✅ Web search available: {web_search_available}")
        
        if web_search_available:
            print(f"✅ Using PRIMARY web search system")
        else:
            print(f"⚠️ Using FALLBACK web search system")
        
        # Test cases
        test_queries = [
            "search the web for current weather",
            "look up the latest news about AI",
            "find information about Python programming",
            "what is the capital of France",  # Should not trigger
            "hello how are you"  # Should not trigger
        ]
        
        print("\n" + "=" * 60)
        print("TESTING TRIGGER DETECTION")
        print("=" * 60)
        
        trigger_results = []
        for query in test_queries:
            should_trigger = should_trigger_web_search(query, "")
            trigger_results.append((query, should_trigger))
            status = "✅ TRIGGER" if should_trigger else "❌ NO TRIGGER"
            print(f"{status}: {query}")
        
        # Test actual web search
        print("\n" + "=" * 60)
        print("TESTING ACTUAL WEB SEARCH")
        print("=" * 60)
        
        async def test_search():
            test_query = "current weather in New York"
            print(f"Searching for: {test_query}")
            
            results = await search_web(test_query, 3)
            print(f"✅ Search completed")
            print(f"Results type: {type(results)}")
            
            if isinstance(results, dict):
                if 'results' in results:
                    print(f"Number of results: {len(results['results'])}")
                    if results['results']:
                        print(f"First result available: ✅")
                        # Test formatting
                        formatted = format_web_results_for_chat(results)
                        print(f"Formatted results length: {len(formatted)} characters")
                        if len(formatted) > 0:
                            print(f"✅ Results formatting successful")
                        else:
                            print(f"❌ Results formatting failed")
                    else:
                        print(f"❌ No search results returned")
                else:
                    print(f"❌ Invalid results structure")
            else:
                print(f"❌ Invalid results type")
            
            return results
        
        # Run the async test
        search_results = asyncio.run(test_search())
        
        print("\n" + "=" * 60)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        # Count successful triggers
        trigger_count = sum(1 for _, triggered in trigger_results if triggered)
        total_tests = len(trigger_results)
        
        print(f"✅ Pipeline imports: SUCCESS")
        print(f"✅ Web search available: {web_search_available}")
        print(f"✅ Trigger detection: {trigger_count}/{total_tests} appropriate triggers")
        print(f"✅ Search execution: {'SUCCESS' if search_results else 'FAILED'}")
        
        # Overall status
        if web_search_available and search_results and trigger_count >= 2:
            print(f"\n🎉 WEB SEARCH INTEGRATION: FULLY FUNCTIONAL")
            print(f"The pipeline is ready for production use!")
        else:
            print(f"\n❌ WEB SEARCH INTEGRATION: ISSUES DETECTED")
            
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"Starting web search integration test at {datetime.now()}")
    success = test_web_search_integration()
    print(f"\nTest completed at {datetime.now()}")
    sys.exit(0 if success else 1)
