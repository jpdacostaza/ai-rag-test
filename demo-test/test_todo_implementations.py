#!/usr/bin/env python3
"""
Test script to verify our TODO implementations are working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_manager import (
    store_chat_history, 
    get_chat_history, 
    index_user_document, 
    retrieve_user_memory
)

def test_chat_history():
    """Test chat history storage and retrieval."""
    print("\n🔍 Testing Chat History Functions...")
    
    user_id = "test_user_123"
    message = "What is Python programming?"
    response = "Python is a high-level, interpreted programming language..."
    
    # Test storing chat history
    print("📝 Storing chat history...")
    success = store_chat_history(user_id, message, response)
    if success:
        print("✅ Chat history stored successfully")
    else:
        print("❌ Failed to store chat history")
        return False
    
    # Test retrieving chat history
    print("📖 Retrieving chat history...")
    history = get_chat_history(user_id, limit=5)
    
    if history and len(history) > 0:
        print(f"✅ Retrieved {len(history)} chat history entries")
        for i, entry in enumerate(history):
            print(f"   Entry {i+1}: {entry.get('message', 'No message')[:50]}...")
    else:
        print("❌ No chat history retrieved")
        return False
    
    return True

def test_document_indexing():
    """Test document indexing and memory retrieval."""
    print("\n🔍 Testing Document Indexing & Memory Retrieval...")
    
    user_id = "test_user_456"
    content = "Python is an excellent language for data science and machine learning."
    metadata = {"topic": "programming", "category": "python"}
    
    # Test indexing document
    print("📝 Indexing user document...")
    success = index_user_document(user_id, content, metadata)
    if success:
        print("✅ Document indexed successfully")
    else:
        print("❌ Failed to index document")
        return False
    
    # Test retrieving memories
    print("🔍 Retrieving user memories...")
    query = "What do you know about Python?"
    memories = retrieve_user_memory(user_id, query, limit=3)
    
    if memories and len(memories) > 0:
        print(f"✅ Retrieved {len(memories)} memory entries")
        for i, memory in enumerate(memories):
            print(f"   Memory {i+1}: {memory.get('content', 'No content')[:50]}...")
            print(f"   Similarity: {memory.get('similarity', 0):.3f}")
    else:
        print("❌ No memories retrieved")
        return False
    
    return True

def main():
    """Run all TODO implementation tests."""
    print("🚀 Testing TODO Implementation Functions")
    print("=" * 50)
    
    success_count = 0
    total_tests = 2
    
    try:
        # Test chat history functions
        if test_chat_history():
            success_count += 1
        
        # Test document indexing functions  
        if test_document_indexing():
            success_count += 1
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All TODO implementations are working correctly!")
        return True
    else:
        print("⚠️ Some TODO implementations need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
