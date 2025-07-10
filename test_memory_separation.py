#!/usr/bin/env python3
"""
Test Memory User Separation
===========================

Test script to verify that memory is properly separated by user_id.
This script will:
1. Store different memories for different users
2. Retrieve memories for each user 
3. Verify that users only see their own memories
"""

import asyncio
import httpx
import json
import time

# Memory API base URL
MEMORY_API_URL = "http://localhost:8001"

async def test_memory_separation():
    """Test that memory is properly separated by user_id."""
    
    print("🧪 Testing Memory User Separation")
    print("=" * 50)
    
    # Test users
    user1 = "alice@example.com"
    user2 = "bob@example.com"
    user3 = "charlie@example.com"
    
    # Test memories for each user
    memories = {
        user1: [
            "Alice works as a software engineer at TechCorp",
            "Alice loves Python programming and machine learning",
            "Alice has 5 years of experience in backend development"
        ],
        user2: [
            "Bob is a data scientist at DataInc",
            "Bob specializes in R and statistical analysis",
            "Bob has a PhD in Statistics from MIT"
        ],
        user3: [
            "Charlie is a product manager at StartupXYZ",
            "Charlie focuses on user experience and product strategy",
            "Charlie previously worked at Google for 3 years"
        ]
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Step 1: Store memories for each user
            print("\n📝 Step 1: Storing memories for each user")
            print("-" * 40)
            
            for user_id, user_memories in memories.items():
                print(f"\n👤 Storing memories for {user_id}:")
                
                for memory_content in user_memories:
                    save_request = {
                        "user_id": user_id,
                        "content": memory_content,
                        "metadata": {"category": "personal", "test": True},
                        "category": "explicit"
                    }
                    
                    response = await client.post(
                        f"{MEMORY_API_URL}/api/memory/save",
                        json=save_request
                    )
                    
                    if response.status_code == 200:
                        print(f"  ✅ Saved: {memory_content[:50]}...")
                    else:
                        print(f"  ❌ Failed to save: {memory_content[:50]}...")
                        print(f"     Status: {response.status_code}, Response: {response.text}")
            
            # Wait a moment for storage to complete
            await asyncio.sleep(2)
            
            # Step 2: Retrieve memories for each user and verify separation
            print("\n🔍 Step 2: Testing memory retrieval and separation")
            print("-" * 50)
            
            for user_id in memories.keys():
                print(f"\n👤 Retrieving memories for {user_id}:")
                
                # Test with a general query that might match multiple users
                retrieve_request = {
                    "user_id": user_id,
                    "query": "professional background work experience",
                    "limit": 10,
                    "threshold": 0.01
                }
                
                response = await client.post(
                    f"{MEMORY_API_URL}/api/memory/retrieve",
                    json=retrieve_request
                )
                
                if response.status_code == 200:
                    data = response.json()
                    retrieved_memories = data.get("memories", [])
                    
                    print(f"  📚 Found {len(retrieved_memories)} memories:")
                    
                    # Verify all memories belong to this user
                    user_specific_count = 0
                    other_user_count = 0
                    
                    for memory in retrieved_memories:
                        memory_user_id = memory.get("user_id", "unknown")
                        content = memory.get("content", "")
                        
                        print(f"    - User: {memory_user_id}, Content: {content[:60]}...")
                        
                        if memory_user_id == user_id:
                            user_specific_count += 1
                        else:
                            other_user_count += 1
                            print(f"      ⚠️  WARNING: Found memory from different user!")
                    
                    print(f"  📊 User-specific: {user_specific_count}, Other users: {other_user_count}")
                    
                    if other_user_count == 0:
                        print(f"  ✅ Memory separation successful for {user_id}")
                    else:
                        print(f"  ❌ Memory separation FAILED for {user_id}")
                        
                else:
                    print(f"  ❌ Failed to retrieve memories for {user_id}")
                    print(f"     Status: {response.status_code}, Response: {response.text}")
            
            # Step 3: Cross-user query test - query one user with another user's specific info
            print("\n🔀 Step 3: Cross-user query test")
            print("-" * 40)
            
            # Query Alice's account for Bob-specific information
            alice_query_for_bob = {
                "user_id": user1,  # Alice
                "query": "data scientist DataInc R statistics PhD MIT",  # Bob's info
                "limit": 10,
                "threshold": 0.01
            }
            
            response = await client.post(
                f"{MEMORY_API_URL}/api/memory/retrieve",
                json=alice_query_for_bob
            )
            
            if response.status_code == 200:
                data = response.json()
                cross_memories = data.get("memories", [])
                
                print(f"👤 Querying Alice's memories for Bob's information:")
                print(f"  📚 Found {len(cross_memories)} memories")
                
                if len(cross_memories) == 0:
                    print("  ✅ Excellent! No cross-user information leaked")
                else:
                    print("  ⚠️  Found some memories - checking content:")
                    for memory in cross_memories:
                        content = memory.get("content", "")
                        user_id = memory.get("user_id", "unknown")
                        print(f"    - User: {user_id}, Content: {content[:60]}...")
                        
                        # Check if this actually contains Bob's info
                        bob_keywords = ["DataInc", "data scientist", "PhD", "MIT", "statistics"]
                        contains_bob_info = any(keyword.lower() in content.lower() for keyword in bob_keywords)
                        
                        if contains_bob_info and user_id == user1:
                            print("      ❌ CRITICAL: Bob's information found in Alice's memories!")
                        elif user_id != user1:
                            print("      ❌ CRITICAL: Memory from different user returned!")
            
            # Step 4: Test with empty user_id (should return no memories or error)
            print("\n🚫 Step 4: Testing with empty user_id")
            print("-" * 40)
            
            empty_user_query = {
                "user_id": "",
                "query": "any information",
                "limit": 10,
                "threshold": 0.01
            }
            
            response = await client.post(
                f"{MEMORY_API_URL}/api/memory/retrieve",
                json=empty_user_query
            )
            
            print(f"Query with empty user_id: Status {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                memories = data.get("memories", [])
                print(f"  📚 Found {len(memories)} memories (should be 0)")
                if len(memories) == 0:
                    print("  ✅ Good: No memories returned for empty user_id")
                else:
                    print("  ⚠️  WARNING: Memories returned for empty user_id")
            
            print("\n" + "=" * 50)
            print("🎯 Memory separation test completed!")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

async def cleanup_test_memories():
    """Clean up test memories after testing."""
    print("\n🧹 Cleaning up test memories...")
    
    test_users = ["alice@example.com", "bob@example.com", "charlie@example.com"]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for user_id in test_users:
            try:
                # Clear all memories for test users
                clear_request = {
                    "user_id": user_id,
                    "confirm": True
                }
                
                response = await client.post(
                    f"{MEMORY_API_URL}/api/memory/clear",
                    json=clear_request
                )
                
                if response.status_code == 200:
                    print(f"  ✅ Cleared memories for {user_id}")
                else:
                    print(f"  ⚠️  Could not clear memories for {user_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Error clearing memories for {user_id}: {e}")

if __name__ == "__main__":
    print("🚀 Starting Memory Separation Test")
    asyncio.run(test_memory_separation())
    
    # Ask if user wants to clean up
    cleanup = input("\n🧹 Clean up test memories? (y/N): ").strip().lower()
    if cleanup in ['y', 'yes']:
        asyncio.run(cleanup_test_memories())
    
    print("✅ Test completed!")
