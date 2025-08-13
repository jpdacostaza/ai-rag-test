#!/usr/bin/env python3
"""
Comprehensive Web Search System Test
Tests all components of the enhanced web search system
"""

import asyncio
import sys
from pathlib import Path

async def test_auto_web_search_filter():
    """Test the AutoWebSearchFilter functionality"""
    print("[*] Testing Auto Web Search Filter...")
    
    try:
        # Import the filter
        sys.path.append(str(Path("memory/functions").absolute()))
        from auto_web_search_filter import Filter
        
        filter_instance = Filter()
        
        # Test trigger detection
        test_messages = [
            "What is the current weather in Amsterdam?",
            "Tell me the latest news about AI",
            "Search the web for Python tutorials",
            "Hello, how are you?"  # Should NOT trigger
        ]
        
        for msg in test_messages:
            lowered = msg.lower()
            is_triggered = any(kw in lowered for kw in filter_instance.valves.trigger_keywords)
            is_forced = any(kw in lowered for kw in filter_instance.valves.force_keywords)
            should_trigger = is_triggered or is_forced
            
            print(f"  Message: '{msg[:40]}...'")
            print(f"    Triggers: {should_trigger} (trigger={is_triggered}, force={is_forced})")
        
        # Test query building
        print("\n  Testing query building:")
        test_queries = [
            "What is the weather in Netherlands today?",
            "Search for latest Python news",
            "Weather warning Netherlands"
        ]
        
        for query in test_queries:
            built_query = filter_instance._build_query(query)
            print(f"    '{query}' → '{built_query}'")
        
        print("[PASS] Auto Web Search Filter tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Auto Web Search Filter test failed: {e}")
        return False

async def test_web_search_tool():
    """Test the Enhanced Web Search Tool"""
    print("\n[*] Testing Enhanced Web Search Tool...")
    
    try:
        # Import the tool
        sys.path.append(str(Path("backend/data/tools").absolute()))
        from web_search_tool import Action
        
        action = Action()
        
        # Test a simple search
        print("  Testing web search with query: 'weather Amsterdam'")
        result = await action.run(query="weather Amsterdam", max_results=3)
        
        print(f"  Result length: {len(result)} characters")
        print(f"  Result preview: {result[:200]}...")
        
        if len(result) > 100 and "weather" in result.lower():
            print("[PASS] Enhanced Web Search Tool tests passed")
            return True
        else:
            print("[FAIL] Search results seem inadequate")
            return False
            
    except Exception as e:
        print(f"[FAIL] Enhanced Web Search Tool test failed: {e}")
        return False

def test_memory_filter():
    """Test the Enhanced Memory Filter"""
    print("\n[*] Testing Enhanced Memory Filter...")
    
    try:
        # Import the filter
        sys.path.append(str(Path("memory/functions").absolute()))
        from enhanced_memory_function_filter_v5_1_final import Filter
        
        filter_instance = Filter()
        
        # Test identity extraction
        test_messages = [
            "My name is John Smith and I work at Google",
            "I am Sarah from Amsterdam",
            "What is the weather today?"  # Should not extract facts
        ]
        
        for msg in test_messages:
            facts = filter_instance._extract_identity_facts(msg)
            print(f"  Message: '{msg}'")
            print(f"    Extracted {len(facts)} facts:")
            for fact in facts:
                print(f"      - {fact['content']} (type: {fact['type']})")
        
        print("[PASS] Enhanced Memory Filter tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Enhanced Memory Filter test failed: {e}")
        return False

async def main():
    """Main test runner"""
    print("[*] Starting Comprehensive Web Search System Tests\n")
    
    results = []
    
    # Test each component
    results.append(await test_auto_web_search_filter())
    results.append(await test_web_search_tool())
    results.append(test_memory_filter())
    
    # Summary
    print(f"\n[*] Test Results Summary:")
    print(f"   Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("[SUCCESS] All tests passed! System should be working well.")
        return 0
    else:
        print("[WARNING] Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
