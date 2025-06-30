#!/usr/bin/env python3
"""
Test Memory Learning API
"""
import os
import requests
import json

BACKEND_URL = "http://localhost:8001"
API_KEY = os.getenv("API_KEY", "default_test_key")

def test_memory_learning_api():
    """Test the memory learning API with sample data"""

    print("📚 Memory Learning API Test")
    print("=" * 50)

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    # Sample data to learn
    user_id = "test_user_learn"
    document_content = "This is a test document about learning. The capital of France is Paris."
    
    learning_data = {
        "user_id": user_id,
        "document": {
            "content": document_content,
            "metadata": {"source": "test_learn_api"}
        }
    }

    print(f"\n📚 Testing memory learning for user: '{user_id}'")
    
    try:
        learning_response = requests.post(
            f"{BACKEND_URL}/api/memory/learn", json=learning_data, headers=headers, timeout=10
        )

        print(f"  Status: {learning_response.status_code}")

        if learning_response.status_code == 200:
            result = learning_response.json()
            print(f"  Response: {result}")
        else:
            print(f"  Error: {learning_response.text}")

    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Now, try to retrieve the learned memory
    print(f"\n🔍 Testing memory retrieval for learned data")
    retrieval_data = {"user_id": user_id, "query": "capital of France", "limit": 5, "threshold": 0.1}

    try:
        retrieval_response = requests.post(
            f"{BACKEND_URL}/api/memory/retrieve", json=retrieval_data, headers=headers, timeout=10
        )

        print(f"  Status: {retrieval_response.status_code}")

        if retrieval_response.status_code == 200:
            result = retrieval_response.json()
            count = result.get("count", 0)
            print(f"  Memories found: {count}")

            if count > 0:
                for i, memory in enumerate(result.get("memories", [])):
                    content = memory.get("content", "No content")
                    similarity = memory.get("similarity", "N/A")
                    metadata = memory.get("metadata", {})
                    print(f"    Memory {i+1}:")
                    print(f"      Content: {content[:100]}...")
                    print(f"      Similarity: {similarity}")
                    print(f"      Metadata: {metadata}")
        else:
            print(f"  Error: {retrieval_response.text}")

    except Exception as e:
        print(f"  ❌ Error: {e}")


if __name__ == "__main__":
    test_memory_learning_api()
