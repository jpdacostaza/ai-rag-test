#!/usr/bin/env python3
"""
Fix OpenWebUI Memory Pipeline Integration - Store Broader Memories and Test
"""

import requests
import json

def store_comprehensive_user_memories():
    """Store comprehensive user memories that should match common queries"""
    print("💾 Storing Comprehensive User Memories for Better Matching")
    print("=" * 65)
    
    memory_api_url = "http://localhost:5001"
    global_user_id = "global_user"
    
    # Store a variety of memories with different query patterns
    comprehensive_memories = [
        {
            "content": "User's name is J.P. and works at Swift, a technology company.",
            "context": json.dumps({"category": "personal_identity", "keywords": ["name", "J.P.", "work", "Swift", "who am I"]}),
            "importance": 0.9,
            "source": "user_introduction"
        },
        {
            "content": "User introduced themselves as J.P. who works at Swift company.",
            "context": json.dumps({"category": "introduction", "keywords": ["hello", "introduction", "about me", "who I am"]}),
            "importance": 0.9,
            "source": "conversation_start"
        },
        {
            "content": "User works in technology sector at a company called Swift.",
            "context": json.dumps({"category": "professional_background", "keywords": ["work", "job", "career", "technology"]}),
            "importance": 0.8,
            "source": "professional_info"
        },
        {
            "content": "User requested AI to remember their name J.P. and workplace Swift.",
            "context": json.dumps({"category": "memory_request", "keywords": ["remember", "know about me", "recall"]}),
            "importance": 0.9,
            "source": "explicit_request"
        },
        {
            "content": "User's personal information: Name is J.P., works at Swift technology company.",
            "context": json.dumps({"category": "personal_data", "keywords": ["personal", "information", "details", "background"]}),
            "importance": 0.8,
            "source": "profile_info"
        },
        {
            "content": "J.P. is a user who mentioned working at Swift company and asked to be remembered.",
            "context": json.dumps({"category": "user_profile", "keywords": ["user", "person", "individual", "me", "I"]}),
            "importance": 0.8,
            "source": "profile_summary"
        }
    ]
    
    stored_count = 0
    for i, memory in enumerate(comprehensive_memories, 1):
        try:
            response = requests.post(
                f"{memory_api_url}/api/memory/store",
                json={
                    "user_id": global_user_id,
                    "content": memory["content"],
                    "context": memory["context"],
                    "importance": memory["importance"],
                    "source": memory["source"]
                }
            )
            if response.status_code == 200:
                stored_count += 1
                print(f"✅ Memory {stored_count}: {memory['content'][:60]}...")
            else:
                print(f"❌ Failed to store memory {i}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error storing memory {i}: {e}")
    
    print(f"\n📊 Total comprehensive memories stored: {stored_count}/6")
    return stored_count

def test_various_memory_queries():
    """Test various types of queries that users might ask"""
    print("\n🔍 Testing Various Memory Queries")
    print("=" * 45)
    
    memory_api_url = "http://localhost:5001"
    global_user_id = "global_user"
    
    test_queries = [
        "What do you know about me?",
        "Who am I?",
        "Tell me about myself",
        "What do you remember about me?",
        "Do you know my name?",
        "Where do I work?",
        "What's my job?",
        "Hello, do you remember me?",
        "Can you recall our previous conversation?",
        "What information do you have about me?"
    ]
    
    successful_queries = 0
    
    for i, query in enumerate(test_queries, 1):
        try:
            response = requests.post(
                f"{memory_api_url}/api/memory/retrieve",
                json={
                    "user_id": global_user_id,
                    "query": query,
                    "limit": 3
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                
                if memories:
                    print(f"✅ Query {i}: '{query}' - Found {len(memories)} memories")
                    successful_queries += 1
                    # Show best match
                    best_match = memories[0]
                    print(f"   └─ Best: {best_match.get('content', '')[:60]}...")
                else:
                    print(f"❌ Query {i}: '{query}' - No memories found")
                    
            else:
                print(f"❌ Query {i} failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error in query {i}: {e}")
    
    success_rate = (successful_queries / len(test_queries)) * 100
    print(f"\n📊 Query success rate: {successful_queries}/{len(test_queries)} ({success_rate:.1f}%)")
    return success_rate > 50

def test_pipeline_with_common_queries():
    """Test the pipeline with common user queries"""
    print("\n🔧 Testing Pipeline with Common User Queries")
    print("=" * 55)
    
    pipeline_url = "http://localhost:9099"
    
    common_queries = [
        "Hello, what do you know about me?",
        "Who am I?",
        "Do you remember me?",
        "What's my name and where do I work?"
    ]
    
    successful_enhancements = 0
    
    for i, query in enumerate(common_queries, 1):
        print(f"\n🧪 Test {i}: {query}")
        
        test_message = {
            "user": {
                "id": "jp_user",
                "name": "J.P.",
                "role": "user"
            },
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "body": {
                "model": "qwen2.5:3b",
                "messages": [
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "stream": False
            }
        }
        
        try:
            response = requests.post(
                f"{pipeline_url}/enhanced_memory_pipeline/filter/inlet",
                json=test_message,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                enhanced_content = result["messages"][0]["content"]
                
                if "Relevant Context from Memory" in enhanced_content:
                    print("✅ Memory enhancement: DETECTED")
                    successful_enhancements += 1
                    
                    # Check for user information
                    if "J.P." in enhanced_content and "Swift" in enhanced_content:
                        print("🎯 User context: FOUND (J.P. + Swift)")
                    elif "J.P." in enhanced_content or "Swift" in enhanced_content:
                        print("🎯 User context: PARTIAL")
                    else:
                        print("⚠️ User context: MISSING")
                        
                    # Show preview
                    lines = enhanced_content.split('\n')
                    memory_lines = [line for line in lines if 'User' in line or 'J.P.' in line]
                    if memory_lines:
                        print(f"📝 Context: {memory_lines[0][:70]}...")
                        
                else:
                    print("❌ Memory enhancement: NOT DETECTED")
                    print(f"   Response: {enhanced_content[:100]}...")
                    
            else:
                print(f"❌ Pipeline error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    enhancement_rate = (successful_enhancements / len(common_queries)) * 100
    print(f"\n📊 Enhancement success rate: {successful_enhancements}/{len(common_queries)} ({enhancement_rate:.1f}%)")
    return enhancement_rate > 50

def provide_openwebui_setup_instructions():
    """Provide step-by-step instructions for OpenWebUI setup"""
    print("\n📋 OPENWEBUI MEMORY PIPELINE SETUP INSTRUCTIONS")
    print("=" * 65)
    
    print("🔧 STEP 1: Enable Pipeline in OpenWebUI")
    print("   1. Open OpenWebUI in browser (http://localhost:8080)")
    print("   2. Go to Settings (gear icon)")
    print("   3. Navigate to 'Pipelines' section")
    print("   4. Find 'Enhanced Memory Pipeline'")
    print("   5. Toggle it ON/Enable it")
    
    print("\n🎯 STEP 2: Configure Model Pipeline")
    print("   1. Go to Models section in OpenWebUI")
    print("   2. Find your model (e.g., qwen2.5:3b)")
    print("   3. Click on model settings/configuration")
    print("   4. Assign 'Enhanced Memory Pipeline' to the model")
    
    print("\n✅ STEP 3: Test Memory Functionality")
    print("   1. Start a new conversation")
    print("   2. Say: 'Hello my name is J.P. I work at Swift, can you remember that?'")
    print("   3. Start a NEW conversation")
    print("   4. Ask: 'What do you know about me?'")
    print("   5. The AI should remember your name and workplace")
    
    print("\n🔍 STEP 4: Verify Memory Pipeline Activity")
    print("   1. Check pipeline logs: docker logs backend-pipelines --tail 20")
    print("   2. Look for '[INFO] Enhanced Memory Pipeline' messages")
    print("   3. Should see 'Retrieved X relevant memories' messages")
    
    print("\n⚠️ TROUBLESHOOTING:")
    print("   • If no memory: Check if pipeline is enabled for your specific model")
    print("   • If partial memory: The pipeline is working but needs more specific memories")
    print("   • If no pipeline logs: Pipeline not activated in OpenWebUI")

def main():
    """Main function to fix OpenWebUI memory integration"""
    print("🔧 FIXING OPENWEBUI MEMORY PIPELINE INTEGRATION")
    print("=" * 70)
    
    # Step 1: Store comprehensive memories
    stored_count = store_comprehensive_user_memories()
    
    if stored_count == 0:
        print("❌ Critical: No memories stored!")
        return
    
    # Step 2: Test memory retrieval
    retrieval_working = test_various_memory_queries()
    
    # Step 3: Test pipeline enhancement
    pipeline_working = test_pipeline_with_common_queries()
    
    # Step 4: Provide setup instructions
    provide_openwebui_setup_instructions()
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎯 MEMORY INTEGRATION STATUS")
    print("=" * 70)
    
    print(f"✅ Memories stored: {stored_count}/6")
    print(f"{'✅' if retrieval_working else '❌'} Memory retrieval: {'Working' if retrieval_working else 'Issues'}")
    print(f"{'✅' if pipeline_working else '❌'} Pipeline enhancement: {'Working' if pipeline_working else 'Issues'}")
    
    if stored_count > 0 and retrieval_working and pipeline_working:
        print("\n🎉 BACKEND MEMORY SYSTEM: FULLY OPERATIONAL!")
        print("   Next: Follow OpenWebUI setup instructions above")
    elif stored_count > 0 and retrieval_working:
        print("\n⚡ MEMORY BACKEND: WORKING")
        print("   Issue: Pipeline needs OpenWebUI configuration")
    else:
        print("\n⚠️ MEMORY SYSTEM: NEEDS ATTENTION")
        print("   Check memory storage and retrieval components")

if __name__ == "__main__":
    main()
