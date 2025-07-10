#!/usr/bin/env python3
"""
Test End-to-End Memory with Multiple Users
==========================================

Test script to verify that the chat endpoint properly separates memory by user_id
through the full OpenWebUI-compatible API flow.
"""

import asyncio
import httpx
import json
import time

# Backend API base URL
BACKEND_API_URL = "http://localhost:3000"

async def test_e2e_memory_separation():
    """Test end-to-end memory separation through chat API."""
    
    print("🧪 Testing End-to-End Memory Separation via Chat API")
    print("=" * 60)
    
    # Test users with different backgrounds
    users = [
        {
            "user_id": "alice.developer",
            "intro_message": "Hi! My name is Alice and I'm a Python developer at TechCorp. I specialize in backend APIs and machine learning.",
            "test_message": "What do you know about my professional background?"
        },
        {
            "user_id": "bob.scientist", 
            "intro_message": "Hello! I'm Bob, a data scientist at DataInc. I work with R and statistical modeling, and I have a PhD from MIT.",
            "test_message": "What can you tell me about my work experience?"
        },
        {
            "user_id": "carol.manager",
            "intro_message": "Hi there! I'm Carol, a product manager at StartupXYZ. I focus on UX design and previously worked at Google.",
            "test_message": "What do you remember about my career background?"
        }
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Step 1: Have each user introduce themselves (store memories)
            print("\n📝 Step 1: Users introducing themselves")
            print("-" * 50)
            
            for user in users:
                print(f"\n👤 {user['user_id']} introducing themselves:")
                
                chat_request = {
                    "model": "llama3.2:3b",
                    "messages": [
                        {
                            "role": "user", 
                            "content": user["intro_message"]
                        }
                    ],
                    "stream": False,
                    "user": user["user_id"]  # OpenAI standard user field
                }
                
                response = await client.post(
                    f"{BACKEND_API_URL}/v1/chat/completions",
                    json=chat_request
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    print(f"  ✅ Response: {content[:100]}...")
                else:
                    print(f"  ❌ Failed: {response.status_code} - {response.text}")
            
            # Wait for memory processing
            await asyncio.sleep(3)
            
            # Step 2: Test memory recall for each user
            print("\n🔍 Step 2: Testing memory recall for each user")
            print("-" * 50)
            
            for user in users:
                print(f"\n👤 {user['user_id']} asking about their background:")
                
                chat_request = {
                    "model": "llama3.2:3b",
                    "messages": [
                        {
                            "role": "user",
                            "content": user["test_message"]
                        }
                    ],
                    "stream": False,
                    "user": user["user_id"]
                }
                
                response = await client.post(
                    f"{BACKEND_API_URL}/v1/chat/completions",
                    json=chat_request
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"].lower()
                    print(f"  📋 Response: {content[:200]}...")
                    
                    # Check if the response contains their own information
                    if user["user_id"] == "alice.developer":
                        contains_own_info = any(keyword in content for keyword in ["alice", "python", "techcorp", "backend", "api"])
                        contains_other_info = any(keyword in content for keyword in ["bob", "carol", "datainc", "startupxyz", "phd", "mit", "google"])
                    elif user["user_id"] == "bob.scientist":
                        contains_own_info = any(keyword in content for keyword in ["bob", "data scientist", "datainc", "statistics", "phd", "mit"])
                        contains_other_info = any(keyword in content for keyword in ["alice", "carol", "techcorp", "startupxyz", "python", "google"])
                    else:  # carol.manager
                        contains_own_info = any(keyword in content for keyword in ["carol", "product manager", "startupxyz", "google", "ux"])
                        contains_other_info = any(keyword in content for keyword in ["alice", "bob", "techcorp", "datainc", "python", "phd", "mit"])
                    
                    print(f"  📊 Contains own info: {contains_own_info}")
                    print(f"  📊 Contains other users' info: {contains_other_info}")
                    
                    if contains_own_info and not contains_other_info:
                        print(f"  ✅ Perfect memory separation for {user['user_id']}")
                    elif contains_own_info and contains_other_info:
                        print(f"  ⚠️  Memory leak detected for {user['user_id']} - knows others' info")
                    elif not contains_own_info and not contains_other_info:
                        print(f"  ⚠️  No memory recall for {user['user_id']} - might need time or different query")
                    else:
                        print(f"  ❌ Critical error: {user['user_id']} only knows others' info!")
                        
                else:
                    print(f"  ❌ Failed: {response.status_code} - {response.text}")
            
            # Step 3: Cross-user information test
            print("\n🔀 Step 3: Cross-user information test")
            print("-" * 50)
            
            # Have Alice ask about Bob's information specifically
            print(f"\n👤 Alice asking about Bob's information:")
            
            cross_user_request = {
                "model": "llama3.2:3b", 
                "messages": [
                    {
                        "role": "user",
                        "content": "What do you know about Bob the data scientist at DataInc who has a PhD from MIT?"
                    }
                ],
                "stream": False,
                "user": "alice.developer"
            }
            
            response = await client.post(
                f"{BACKEND_API_URL}/v1/chat/completions",
                json=cross_user_request
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"].lower()
                print(f"  📋 Alice's response about Bob: {content[:200]}...")
                
                # Check if Alice's response contains Bob's specific information
                bob_specific_info = any(keyword in content for keyword in ["datainc", "phd", "mit", "statistical modeling"])
                
                if not bob_specific_info:
                    print("  ✅ Excellent! Alice doesn't have access to Bob's specific information")
                else:
                    print("  ❌ CRITICAL: Alice has access to Bob's private information!")
                    
            print("\n" + "=" * 60)
            print("🎯 End-to-end memory separation test completed!")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting End-to-End Memory Separation Test")
    asyncio.run(test_e2e_memory_separation())
    print("✅ Test completed!")
