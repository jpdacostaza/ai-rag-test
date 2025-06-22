#!/usr/bin/env python3

import sys
import os
import traceback

# Add the current directory to sys.path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the functions we want to test
try:
    from database import db_manager, get_embedding
    from rag import rag_processor
    print("✅ Successfully imported modules")
except Exception as e:
    print(f"❌ Failed to import modules: {e}")
    traceback.print_exc()
    sys.exit(1)

def test_get_embedding():
    """Test the get_embedding function directly"""
    print("\n🧪 Testing get_embedding function...")
    
    try:
        result = get_embedding(db_manager, "test document")
        print(f"✅ get_embedding returned: {type(result)}")
        if result is not None:
            if hasattr(result, 'shape'):
                print(f"   Shape: {result.shape}")
            if hasattr(result, 'size'):
                print(f"   Size: {result.size}")
        return result
    except Exception as e:
        print(f"❌ get_embedding failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None

def test_semantic_search():
    """Test the semantic_search function directly"""
    print("\n🧪 Testing semantic_search function...")
    
    try:
        # This should trigger the same code path as the API endpoint
        import asyncio
        result = asyncio.run(rag_processor.semantic_search("test document", "test-user-123", 5))
        print(f"✅ semantic_search returned: {len(result)} results")
        return result
    except Exception as e:
        print(f"❌ semantic_search failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None

def main():
    print("🔍 Direct function testing to isolate the NumPy array error...")
    print("=" * 60)
    
    # Test embedding generation first
    embedding = test_get_embedding()
    
    # Test semantic search
    results = test_semantic_search()
    
    print("\n" + "=" * 60)
    print("🔍 Test Summary:")
    print(f"Embedding generation: {'✅ Success' if embedding is not None else '❌ Failed'}")
    print(f"Semantic search: {'✅ Success' if results is not None else '❌ Failed'}")

if __name__ == "__main__":
    main()
