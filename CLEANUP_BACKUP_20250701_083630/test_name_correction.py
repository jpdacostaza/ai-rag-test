#!/usr/bin/env python3
"""
Test script to verify memory system is working correctly with name corrections
"""
import requests
import json
import time

MEMORY_API_URL = "http://localhost:8001"

def test_memory_system():
    print("🧪 Testing Memory System with Name Corrections")
    
    # Test 1: Query current memories
    print("\n1. Checking current memories...")
    response = requests.post(
        f"{MEMORY_API_URL}/api/memory/retrieve",
        json={
            "user_id": "anonymous",
            "query": "what is my name",
            "threshold": 0.05,
            "limit": 10
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        memories = result.get("memories", [])
        print(f"   Found {len(memories)} memories:")
        for i, memory in enumerate(memories, 1):
            content = memory.get("content", "")
            score = memory.get("relevance_score", 0)
            print(f"   {i}. {content[:60]}... (score: {score:.3f})")
    else:
        print(f"   ❌ Error: {response.status_code}")
        return
    
    # Test 2: Store a new interaction with name correction
    print("\n2. Testing name correction...")
    test_interaction = {
        "user_id": "anonymous",
        "conversation_id": "test-correction-2",
        "user_message": "Just to be clear, my name is J.P., not TestUser or any other variant",
        "assistant_response": "Got it! I'll remember that your name is J.P. and not TestUser. Thanks for the clarification!",
        "context": {},
        "source": "test_correction"
    }
    
    response = requests.post(
        f"{MEMORY_API_URL}/api/learning/process_interaction",
        json=test_interaction
    )
    
    if response.status_code == 200:
        print("   ✅ Correction interaction stored")
    else:
        print(f"   ❌ Storage error: {response.status_code}")
        return
    
    # Wait a moment for processing
    time.sleep(1)
    
    # Test 3: Query again to see if correction worked
    print("\n3. Checking memories after correction...")
    response = requests.post(
        f"{MEMORY_API_URL}/api/memory/retrieve",
        json={
            "user_id": "anonymous",
            "query": "what is my name",
            "threshold": 0.05,
            "limit": 10
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        memories = result.get("memories", [])
        print(f"   Found {len(memories)} memories:")
        
        correct_name_count = 0
        incorrect_name_count = 0
        
        for i, memory in enumerate(memories, 1):
            content = memory.get("content", "")
            score = memory.get("relevance_score", 0)
            print(f"   {i}. {content[:60]}... (score: {score:.3f})")
            
            if "j.p." in content.lower():
                correct_name_count += 1
            elif "testuser" in content.lower() and not content.startswith("CORRECTION:"):
                incorrect_name_count += 1
        
        print(f"\n📊 Analysis:")
        print(f"   ✅ Correct name (J.P.) memories: {correct_name_count}")
        print(f"   ❌ Incorrect name (TestUser) memories: {incorrect_name_count}")
        
        if correct_name_count > 0 and incorrect_name_count == 0:
            print("   🎉 SUCCESS: Name correction is working!")
        elif incorrect_name_count > 0:
            print("   ⚠️  WARNING: Still returning incorrect names")
        else:
            print("   ❓ UNCLEAR: No name memories found")
    else:
        print(f"   ❌ Query error: {response.status_code}")

if __name__ == "__main__":
    test_memory_system()
