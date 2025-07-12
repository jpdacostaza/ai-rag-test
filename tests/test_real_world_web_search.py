#!/usr/bin/env python3
"""
Real-World Web Search Test
==========================

This script simulates the exact conditions that would occur in OpenWebUI
to test if web search is actually working in production.
"""

import sys
import asyncio
import json
from datetime import datetime

# Add paths for imports
sys.path.insert(0, '.')
sys.path.insert(0, 'pipelines')

def test_real_world_pipeline():
    """Test the pipeline exactly as OpenWebUI would use it"""
    print("=" * 70)
    print("REAL-WORLD OPENWEBUI PIPELINE TEST")
    print("=" * 70)
    print(f"Testing at: {datetime.now()}")
    print()
    
    try:
        # Import the actual pipeline class
        from enhanced_memory_pipeline import Pipeline
        
        # Create pipeline instance
        pipeline = Pipeline()
        print("✅ Pipeline instance created")
        
        # Test the valves (configuration)
        valves = pipeline.valves
        print(f"✅ Pipeline valves accessible")
        print(f"   Debug mode: {valves.debug_mode}")
        print(f"   Memory enabled: {valves.enable_memory}")
        
        # Simulate real OpenWebUI request body
        test_body = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user", 
                    "content": "search the web for current weather in the netherlands"
                }
            ],
            "model": "llama3.2:3b",
            "stream": False
        }
        
        print("\n" + "=" * 50)
        print("TESTING INLET (REQUEST PROCESSING)")
        print("=" * 50)
        
        # Test inlet method (this is where web search happens)
        async def test_inlet():
            try:
                print("Calling pipeline.inlet() with real request...")
                result = await pipeline.inlet(body=test_body.copy(), __user__={"id": "test-user"})
                
                print("✅ Inlet completed successfully")
                print(f"Result type: {type(result)}")
                
                if isinstance(result, dict) and "messages" in result:
                    print(f"Number of messages: {len(result['messages'])}")
                    
                    # Check if web search results were added
                    for i, msg in enumerate(result["messages"]):
                        if msg.get("role") == "system":
                            content = msg.get("content", "")
                            if "web search results" in content.lower():
                                print(f"✅ WEB SEARCH RESULTS FOUND in system message!")
                                print(f"   System message length: {len(content)} characters")
                                # Show a snippet of the web search results
                                if len(content) > 500:
                                    print(f"   Preview: ...{content[-200:]}")
                                else:
                                    print(f"   Full content: {content}")
                                return True
                            else:
                                print(f"❌ No web search results in system message")
                                print(f"   System message: {content[:200]}...")
                    
                    print(f"❌ No web search results found in any message")
                else:
                    print(f"❌ Invalid result format")
                
                return False
                
            except Exception as e:
                print(f"❌ Error in inlet: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # Run the async test
        web_search_worked = asyncio.run(test_inlet())
        
        print("\n" + "=" * 50)
        print("TESTING DIRECT FUNCTIONS")
        print("=" * 50)
        
        # Also test the functions directly
        from enhanced_memory_pipeline import should_trigger_web_search, search_web, web_search_available
        
        print(f"Web search available: {web_search_available}")
        
        test_query = "search the web for current weather in the netherlands"
        trigger_result = should_trigger_web_search(test_query, "")
        print(f"Direct trigger test: {trigger_result}")
        
        if trigger_result:
            async def test_direct_search():
                results = await search_web(test_query, 3)
                print(f"Direct search results: {type(results)}")
                if isinstance(results, dict):
                    print(f"Direct search keys: {list(results.keys())}")
                    if "results" in results and results["results"]:
                        print(f"Direct search found {len(results['results'])} results")
                        return True
                return False
            
            direct_search_worked = asyncio.run(test_direct_search())
        else:
            direct_search_worked = False
            print("❌ Direct trigger failed")
        
        print("\n" + "=" * 50)
        print("REAL-WORLD TEST SUMMARY")
        print("=" * 50)
        
        print(f"✅ Pipeline creation: SUCCESS")
        print(f"✅ Pipeline configuration: SUCCESS")
        print(f"{'✅' if web_search_worked else '❌'} Pipeline web search integration: {'SUCCESS' if web_search_worked else 'FAILED'}")
        print(f"{'✅' if trigger_result else '❌'} Direct trigger function: {'SUCCESS' if trigger_result else 'FAILED'}")
        print(f"{'✅' if direct_search_worked else '❌'} Direct search function: {'SUCCESS' if direct_search_worked else 'FAILED'}")
        
        if web_search_worked:
            print(f"\n🎉 REAL-WORLD TEST: WEB SEARCH IS WORKING!")
            print(f"   The pipeline should work correctly in OpenWebUI")
        else:
            print(f"\n❌ REAL-WORLD TEST: WEB SEARCH IS NOT WORKING")
            print(f"   The pipeline is not adding web search results to messages")
            
            if direct_search_worked:
                print(f"   → Direct functions work, but pipeline integration is broken")
            else:
                print(f"   → Both direct functions and pipeline integration are broken")
        
        return web_search_worked
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_openwebui_simulation():
    """Simulate exactly what OpenWebUI does"""
    print("\n" + "=" * 70)
    print("OPENWEBUI EXACT SIMULATION TEST")
    print("=" * 70)
    
    try:
        from enhanced_memory_pipeline import Pipeline
        
        pipeline = Pipeline()
        
        # Exact simulation of OpenWebUI request
        user_data = {
            "id": "user-12345",
            "name": "Test User",
            "email": "test@example.com"
        }
        
        request_body = {
            "messages": [
                {
                    "id": "msg-1",
                    "role": "user",
                    "content": "search the web for current weather in the netherlands"
                }
            ],
            "model": "llama3.2:3b",
            "stream": False,
            "chat_id": "chat-12345"
        }
        
        print("Simulating OpenWebUI request processing...")
        
        async def simulate_openwebui():
            # This is exactly what OpenWebUI calls
            processed_body = await pipeline.inlet(body=request_body.copy(), __user__=user_data)
            
            print("Request processed by pipeline")
            print(f"Original messages: {len(request_body['messages'])}")
            print(f"Processed messages: {len(processed_body['messages'])}")
            
            # Check for modifications
            for i, msg in enumerate(processed_body["messages"]):
                if msg.get("role") == "system":
                    print(f"✅ System message added by pipeline")
                    content = msg.get("content", "")
                    if "web search" in content.lower():
                        print(f"✅ Web search content detected!")
                        return True
                elif msg.get("role") == "user":
                    original_content = request_body["messages"][0]["content"]
                    new_content = msg.get("content", "")
                    if new_content != original_content:
                        print(f"✅ User message modified by pipeline")
                        if "web search" in new_content.lower():
                            print(f"✅ Web search context added to user message!")
                            return True
            
            return False
        
        found_web_search = asyncio.run(simulate_openwebui())
        
        if found_web_search:
            print(f"\n🎉 OPENWEBUI SIMULATION: SUCCESS!")
            print(f"Web search integration is working correctly")
        else:
            print(f"\n❌ OPENWEBUI SIMULATION: FAILED!")
            print(f"Web search is not being integrated into the chat")
        
        return found_web_search
        
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🌍 REAL-WORLD WEB SEARCH TEST")
    print(f"Testing web search integration in production-like conditions")
    print(f"Time: {datetime.now()}")
    print()
    
    # Test 1: Real-world pipeline test
    test1_success = test_real_world_pipeline()
    
    # Test 2: OpenWebUI exact simulation
    test2_success = test_openwebui_simulation()
    
    print("\n" + "=" * 70)
    print("FINAL REAL-WORLD TEST RESULTS")
    print("=" * 70)
    
    if test1_success and test2_success:
        print("🎉 BOTH TESTS PASSED - WEB SEARCH IS WORKING IN PRODUCTION!")
        print("   Your OpenWebUI should perform actual web searches")
    elif test1_success or test2_success:
        print("⚠️ PARTIAL SUCCESS - Some functionality working")
        print("   Check the specific test results above")
    else:
        print("❌ BOTH TESTS FAILED - WEB SEARCH IS NOT WORKING")
        print("   Web search will not work in OpenWebUI")
    
    print(f"\nTest completed at: {datetime.now()}")
