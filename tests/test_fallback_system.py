#!/usr/bin/env python3
"""
Test fallback system behavior
"""

import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'pipelines')

print("=== TESTING FALLBACK SYSTEM ===")
print()

try:
    # Import and test pipeline
    print("Importing pipeline...")
    from enhanced_memory_pipeline import (
        web_search_available, 
        memory_system_available,
        should_trigger_web_search
    )
    
    print(f"✅ Pipeline imported successfully")
    print(f"Web search available: {web_search_available}")
    print(f"Memory system available: {memory_system_available}")
    print()
    
    if web_search_available:
        print("✅ PRIMARY web search system is active")
    else:
        print("⚠️ FALLBACK web search system is active")
    
    if memory_system_available:
        print("✅ PRIMARY memory system is active")
    else:
        print("⚠️ FALLBACK memory system is active")
    
    print()
    print("Testing web search trigger...")
    test_query = "search the web for current weather"
    result = should_trigger_web_search(test_query, "")
    print(f"Query: {test_query}")
    print(f"Trigger result: {result}")
    
    print("\n=== TEST COMPLETE ===")
    
except Exception as e:
    print(f"❌ Error during test: {e}")
    import traceback
    traceback.print_exc()
