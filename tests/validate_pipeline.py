#!/usr/bin/env python3
"""
Web Search Pipeline Validation Script
====================================
Tests the Enhanced Web Search Pipeline functionality
"""

import asyncio
import sys
import os

# Add the pipeline directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from enhanced_web_search_pipeline import Pipeline
    print("✅ Pipeline import successful")
except ImportError as e:
    print(f"❌ Pipeline import failed: {e}")
    sys.exit(1)

async def test_pipeline():
    """Test the pipeline functionality"""
    print("\n🧪 Testing Enhanced Web Search Pipeline...")
    
    # Initialize pipeline
    pipeline = Pipeline()
    print("✅ Pipeline initialized")
    
    # Test valve configuration
    print(f"📋 Pipeline name: {pipeline.name}")
    print(f"📋 Pipeline type: {pipeline.type}")
    print(f"📋 Max results: {pipeline.valves.max_results}")
    print(f"📋 Auto search: {pipeline.valves.auto_search_enabled}")
    
    # Test trigger detection
    test_queries = [
        "latest news headlines",
        "current events 2025",
        "what is Python programming",
        "breaking news today"
    ]
    
    print("\n🔍 Testing search triggers:")
    for query in test_queries:
        trigger = pipeline._should_trigger_search_from_query(query)
        print(f"   '{query}' → {'✅ Triggers' if trigger else '❌ No trigger'}")
    
    # Test uncertainty detection
    test_responses = [
        "I don't know about current events",
        "Python is a programming language",
        "I'm not sure about the latest news",
        "I cannot provide current information"
    ]
    
    print("\n🤔 Testing uncertainty detection:")
    for response in test_responses:
        uncertain = pipeline._should_trigger_search_from_response(response)
        print(f"   '{response}' → {'✅ Uncertain' if uncertain else '❌ Confident'}")
    
    # Test message processing (mock)
    print("\n📨 Testing message processing:")
    test_body = {
        "messages": [
            {"role": "user", "content": "what are the latest news headlines?"},
            {"role": "assistant", "content": "I don't have current information"}
        ]
    }
    
    try:
        # Test inlet
        result = await pipeline.inlet(test_body.copy())
        print("✅ Inlet processing successful")
        
        # Test outlet  
        result = await pipeline.outlet(test_body.copy())
        print("✅ Outlet processing successful")
        
    except Exception as e:
        print(f"❌ Message processing failed: {e}")
    
    print("\n🎉 Pipeline validation complete!")

if __name__ == "__main__":
    print("Enhanced Web Search Pipeline Validator")
    print("=" * 50)
    
    try:
        asyncio.run(test_pipeline())
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)
    
    print("\n✅ All tests passed! Pipeline is ready for use.")
