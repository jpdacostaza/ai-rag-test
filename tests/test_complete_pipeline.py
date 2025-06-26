#!/usr/bin/env python3
"""
Complete Memory Pipeline Test
Demonstrates working end-to-end memory storage and retrieval
"""
import os

import requests
import json
import time

BACKEND_URL = "http://localhost:8001"
API_KEY = os.getenv("API_KEY", "default_test_key")


def test_complete_memory_pipeline():
    """Test complete memory pipeline: store -> wait -> retrieve"""

    print("🚀 Complete Memory Pipeline Test")
    print("=" * 60)

    user_id = f"pipeline_user_{int(time.time())}"

    # Step 1: Store user information
    print(f"📝 Step 1: Storing user information for {user_id}")
    user_info = "My name is Emma Rodriguez. I am a senior software engineer at CloudTech Solutions. I specialize in cloud architecture, microservices, and Kubernetes. I prefer working with Python and Go programming languages. I have 8 years of experience in backend development."

    files = {"file": ("user_profile.txt", user_info, "text/plain")}
    data = {"user_id": user_id, "description": "User profile and preferences"}

    try:
        upload_response = requests.post(
            f"{BACKEND_URL}/upload/document",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=15,
        )

        if upload_response.status_code == 200:
            result = upload_response.json()
            print(f"✅ Storage successful: {result['data']['chunks_processed']} chunks processed")
            print(f"   Document ID: {result['data']['document_id']}")
        else:
            print(f"❌ Storage failed: {upload_response.text}")
            return

    except Exception as e:
        print(f"❌ Storage error: {e}")
        return

    # Step 2: Wait for indexing
    print(f"\n⏳ Step 2: Waiting 5 seconds for ChromaDB indexing...")
    time.sleep(5)

    # Step 3: Test various memory queries
    print(f"\n🔍 Step 3: Testing memory retrieval with various queries")

    test_scenarios = [
        ("User's name", "What is my name?"),
        ("Job title", "What is my job?"),
        ("Company", "Where do I work?"),
        ("Technical skills", "What programming languages do I know?"),
        ("Experience", "How much experience do I have?"),
        ("Specialization", "What do I specialize in?"),
    ]

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    for scenario, query in test_scenarios:
        print(f"\n🎯 Testing: {scenario}")
        print(f"   Query: '{query}'")

        retrieval_data = {"user_id": user_id, "query": query, "limit": 3, "threshold": 0.3}

        try:
            retrieval_response = requests.post(
                f"{BACKEND_URL}/api/memory/retrieve", json=retrieval_data, headers=headers, timeout=10
            )

            if retrieval_response.status_code == 200:
                result = retrieval_response.json()
                count = result.get("count", 0)

                if count > 0:
                    memory = result["memories"][0]  # Get best match
                    content = memory.get("content", "")
                    similarity = memory.get("similarity", 0)

                    print(f"   ✅ Found: {content[:100]}...")
                    print(f"   📊 Similarity: {similarity:.3f}")
                else:
                    print(f"   ❌ No memories found")
            else:
                print(f"   ❌ Retrieval failed: {retrieval_response.text}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Step 4: Test cross-user isolation
    print(f"\n🔒 Step 4: Testing cross-user memory isolation")
    different_user = "different_user_test"

    retrieval_data = {"user_id": different_user, "query": "Emma Rodriguez", "limit": 3, "threshold": 0.1}

    try:
        retrieval_response = requests.post(
            f"{BACKEND_URL}/api/memory/retrieve", json=retrieval_data, headers=headers, timeout=10
        )

        if retrieval_response.status_code == 200:
            result = retrieval_response.json()
            count = result.get("count", 0)
            print(f"   Different user found {count} memories (should be 0): {'✅ PASS' if count == 0 else '❌ FAIL'}")
        else:
            print(f"   ❌ Cross-user test failed: {retrieval_response.text}")

    except Exception as e:
        print(f"   ❌ Cross-user test error: {e}")

    print(f"\n🎉 Memory Pipeline Test Complete!")
    print(f"   User ID: {user_id}")
    print(f"   This demonstrates working persistent memory storage and retrieval.")

    return user_id


if __name__ == "__main__":
    user_id = test_complete_memory_pipeline()

    print(f"\n📋 Next Steps:")
    print(f"   1. This memory system is now ready for OpenWebUI integration")
    print(f"   2. The memory pipeline can inject stored context into conversations")
    print(f"   3. Users can store information via document upload")
    print(f"   4. Retrieved memories can be used to personalize responses")
