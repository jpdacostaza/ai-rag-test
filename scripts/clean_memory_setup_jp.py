#!/usr/bin/env python3
"""
Clean Memory Database and Re-establish J.P./Swift User Profile
"""

import requests
import json

def clean_and_setup_memory():
    """Clean old memories and set up proper J.P./Swift profile"""
    print("🧹 CLEANING MEMORY DATABASE & SETTING UP J.P. PROFILE")
    print("=" * 65)
    
    memory_api_url = "http://localhost:5001"
    global_user_id = "global_user"
    
    # Step 1: Check current memory state
    print("📊 Current Memory State:")
    try:
        response = requests.get(f"{memory_api_url}/api/memory/{global_user_id}")
        if response.status_code == 200:
            current_memories = response.json().get("memories", [])
            print(f"   Total memories: {len(current_memories)}")
            for i, memory in enumerate(current_memories[:3], 1):
                content = memory.get("content", "")[:60]
                print(f"   {i}. {content}...")
        else:
            print(f"   Error: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Step 2: Clear all memories for clean start
    print("\n🗑️ Clearing All Memories for Clean Start:")
    try:
        response = requests.delete(f"{memory_api_url}/api/memory/{global_user_id}")
        if response.status_code == 200:
            print("   ✅ All memories cleared successfully")
        else:
            print(f"   ⚠️ Clear response: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error clearing memories: {e}")
    
    # Step 3: Store clean J.P./Swift memories
    print("\n💾 Storing Clean J.P./Swift Profile:")
    
    jp_memories = [
        {
            "content": "User's name is J.P. and they work at Swift technology company.",
            "context": json.dumps({
                "type": "personal_identity",
                "keywords": ["name", "J.P.", "Swift", "work", "who am I", "about me", "know about me"],
                "importance": "high"
            }),
            "importance": 0.95,
            "source": "user_profile"
        },
        {
            "content": "J.P. introduced themselves and mentioned working at Swift company.",
            "context": json.dumps({
                "type": "introduction", 
                "keywords": ["hello", "introduction", "remember me", "who I am", "recall"],
                "importance": "high"
            }),
            "importance": 0.9,
            "source": "introduction"
        },
        {
            "content": "User J.P. works at Swift, a technology company.",
            "context": json.dumps({
                "type": "professional_info",
                "keywords": ["work", "job", "workplace", "company", "Swift", "technology"],
                "importance": "medium"
            }),
            "importance": 0.8,
            "source": "work_info"
        }
    ]
    
    stored_count = 0
    for i, memory in enumerate(jp_memories, 1):
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
                print(f"   ✅ Memory {i}: {memory['content'][:50]}...")
            else:
                print(f"   ❌ Failed {i}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error {i}: {e}")
    
    print(f"\n📊 Clean J.P. profile stored: {stored_count}/3 memories")
    
    # Step 4: Test memory retrieval with common queries
    print("\n🔍 Testing Memory Retrieval:")
    test_queries = [
        "What do you know about me?",
        "Who am I?", 
        "What's my name?",
        "Where do I work?",
        "Do you remember me?"
    ]
    
    successful_queries = 0
    for i, query in enumerate(test_queries, 1):
        try:
            response = requests.post(
                f"{memory_api_url}/api/memory/retrieve",
                json={
                    "user_id": global_user_id,
                    "query": query,
                    "limit": 2
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                
                if memories and any("J.P." in mem.get("content", "") or "Swift" in mem.get("content", "") for mem in memories):
                    print(f"   ✅ '{query}' → Found J.P./Swift info")
                    successful_queries += 1
                elif memories:
                    print(f"   ⚠️ '{query}' → Found memories but not J.P./Swift")
                else:
                    print(f"   ❌ '{query}' → No memories found")
            else:
                print(f"   ❌ '{query}' → API error {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ '{query}' → Error: {e}")
    
    success_rate = (successful_queries / len(test_queries)) * 100
    print(f"\n📊 Memory retrieval success: {successful_queries}/{len(test_queries)} ({success_rate:.1f}%)")
    
    return stored_count == 3 and successful_queries >= 3

def test_pipeline_after_cleanup():
    """Test pipeline functionality after memory cleanup"""
    print("\n🔧 Testing Pipeline After Memory Cleanup:")
    print("=" * 50)
    
    pipeline_url = "http://localhost:9099"
    
    test_message = {
        "user": {
            "id": "jp_user",
            "name": "J.P.",
            "role": "user"
        },
        "messages": [
            {
                "role": "user",
                "content": "Hello, what do you know about me?"
            }
        ],
        "body": {
            "model": "qwen2.5:3b",
            "messages": [
                {
                    "role": "user", 
                    "content": "Hello, what do you know about me?"
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
                print("✅ Pipeline enhancement: WORKING")
                
                if "J.P." in enhanced_content and "Swift" in enhanced_content:
                    print("🎯 J.P./Swift context: FOUND")
                    print(f"📝 Enhanced response preview:")
                    lines = enhanced_content.split('\n')[:3]
                    for line in lines:
                        if line.strip():
                            print(f"    {line.strip()}")
                    return True
                else:
                    print("⚠️ J.P./Swift context: MISSING")
                    return False
            else:
                print("❌ Pipeline enhancement: NOT WORKING")
                print(f"   Response: {enhanced_content[:100]}...")
                return False
                
        else:
            print(f"❌ Pipeline error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline test error: {e}")
        return False

def main():
    """Main cleanup and setup function"""
    print("🧹 MEMORY DATABASE CLEANUP & J.P. PROFILE SETUP")
    print("=" * 70)
    
    # Clean and setup memory
    memory_setup_success = clean_and_setup_memory()
    
    if memory_setup_success:
        # Test pipeline
        pipeline_success = test_pipeline_after_cleanup()
        
        if pipeline_success:
            print("\n🎉 SUCCESS: Memory system fully operational!")
            print("   - Clean J.P./Swift profile established")
            print("   - Memory retrieval working correctly") 
            print("   - Pipeline enhancement active")
            print("\n📋 NEXT STEPS:")
            print("   1. Go to OpenWebUI Settings > Pipelines")
            print("   2. Ensure 'Enhanced Memory Pipeline' is enabled")
            print("   3. Test with: 'Hello, what do you know about me?'")
        else:
            print("\n⚡ PARTIAL SUCCESS: Memory backend working, pipeline needs attention")
    else:
        print("\n⚠️ Memory setup incomplete - check API connectivity")

if __name__ == "__main__":
    main()
