#!/usr/bin/env python3
"""
Test Memory Filter Loading
=========================
"""

import sys
import os
import traceback

def test_filter_loading():
    """Test if the memory filter can be loaded properly"""
    
    try:
        # Add the memory functions directory to the path
        sys.path.insert(0, 'memory/functions')
        
        # Import the filter
        from memory_filter import Filter, Valves
        
        print("✅ Filter imports successfully")
        
        # Test creating the filter instance
        filter_instance = Filter()
        print("✅ Filter instance created successfully")
        
        # Test valves
        valves = filter_instance.valves
        print(f"✅ Valves configured: {valves.model_dump()}")
        
        # Test basic methods exist
        methods = ['inlet', 'outlet', 'store_memory', 'retrieve_memories']
        for method in methods:
            if hasattr(filter_instance, method):
                print(f"✅ Method '{method}' exists")
            else:
                print(f"❌ Method '{method}' missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading filter: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_filter_loading()
    if success:
        print("\n🎉 Filter loading test passed!")
    else:
        print("\n❌ Filter loading test failed!")
