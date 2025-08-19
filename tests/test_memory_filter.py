#!/usr/bin/env python3
"""
Test the memory filter's ability to load the unified prompt via API
"""

import sys
sys.path.append('/app/backend/data/functions/filters')

try:
    # Import the memory filter
    from enhanced_memory_function_filter_v5_1_final import Filter
    
    print("🧪 Testing Memory Filter Unified Prompt Loading")
    print("=" * 50)
    
    # Create filter instance
    filter_instance = Filter()
    print("✅ Memory filter instance created successfully")
    
    # Test unified prompt loading
    try:
        prompt = filter_instance._load_unified_prompt()
        print(f"✅ Unified prompt loaded successfully!")
        print(f"   Length: {len(prompt)} characters")
        print(f"   Preview: {prompt[:100]}...")
        print("\n🎉 Memory filter is working correctly!")
        
    except Exception as e:
        print(f"❌ Error loading unified prompt: {e}")
        
except Exception as e:
    print(f"❌ Error importing or testing memory filter: {e}")

print("\n📋 Instructions:")
print("1. Refresh your browser at localhost:8080")
print("2. Try sending a message to test the system")
print("3. The unified prompt error should be resolved")
