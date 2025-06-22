#!/usr/bin/env python3

import sys
import os
import traceback

# Add the current directory to sys.path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_minimal_search():
    """Minimal test to isolate the exact error location"""
    print("🔍 Minimal test to find the exact NumPy array error location...")
    
    try:
        # Import step by step to isolate the error
        print("Step 1: Importing basic modules...")
        from database import db_manager
        
        print("Step 2: Importing get_embedding...")
        from database import get_embedding
        
        print("Step 3: Importing retrieve_user_memory...")
        from database import retrieve_user_memory
        
        print("Step 4: Testing embedding generation...")
        embedding = get_embedding(db_manager, "test query")
        print(f"Embedding type: {type(embedding)}")
        print(f"Embedding shape: {getattr(embedding, 'shape', 'no shape')}")
        
        print("Step 5: Testing retrieve_user_memory with the embedding...")
        # This is where the error likely occurs
        results = retrieve_user_memory(db_manager, "test-user", embedding, 5)
        print(f"Results: {len(results)} items")
        
        print("✅ All steps completed successfully!")
        
    except Exception as e:
        print(f"❌ Error occurred: {type(e).__name__}: {e}")
        print(f"Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_minimal_search()
