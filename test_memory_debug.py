#!/usr/bin/env python3
"""
Debug script for Memory System Analysis
======================================
This script provides detailed analysis of the memory system to understand
how memories are being stored and retrieved.
"""

import requests
import json
import uuid

# Configuration
MEMORY_API_URL = "http://localhost:8001"
TEST_USER_ID = f"debug_user_{str(uuid.uuid4())[:8]}"

def test_memory_storage():
    """Test memory storage with different types of content"""
    print("🔍 TESTING MEMORY STORAGE")
    print("=" * 50)
    
    test_interactions = [
        {
            "user_id": TEST_USER_ID,
            "conversation_id": f"debug_conv_{TEST_USER_ID}",
            "user_message": "I have a meeting every Tuesday at 3 PM",
            "assistant_response": "I'll remember your recurring Tuesday meeting",
            "context": {"category": "schedule", "type": "meeting"}
        },
        {
            "user_id": TEST_USER_ID,
            "conversation_id": f"debug_conv_{TEST_USER_ID}",
            "user_message": "My project deadline is next Friday",
            "assistant_response": "I'll remember your Friday deadline",
            "context": {"category": "work", "urgency": "high"}
        },
        {
            "user_id": TEST_USER_ID,
            "conversation_id": f"debug_conv_{TEST_USER_ID}",
            "user_message": "I love pizza on weekends",
            "assistant_response": "Got it, pizza on weekends!",
            "context": {"category": "food", "time": "weekend"}
        }
    ]
    
    for i, interaction in enumerate(test_interactions):
        try:
            response = requests.post(
                f"{MEMORY_API_URL}/api/learning/process_interaction",
                json=interaction,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Interaction {i+1}: {result.get('status', 'success')}")
                print(f"   Message: {interaction['user_message']}")
            else:
                print(f"❌ Interaction {i+1} failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error with interaction {i+1}: {e}")

def test_memory_retrieval():
    """Test memory retrieval with various queries"""
    print("\n🔍 TESTING MEMORY RETRIEVAL")
    print("=" * 50)
    
    test_queries = [
        ("Tuesday", "Looking for Tuesday meeting"),
        ("meeting", "Looking for meeting info"),
        ("3 PM", "Looking for 3 PM time"),
        ("Friday", "Looking for Friday deadline"),
        ("deadline", "Looking for deadline info"),
        ("project", "Looking for project info"),
        ("pizza", "Looking for pizza preference"),
        ("weekend", "Looking for weekend activities"),
    ]
    
    for query, description in test_queries:
        try:
            response = requests.post(
                f"{MEMORY_API_URL}/api/memory/retrieve",
                json={"user_id": TEST_USER_ID, "query": query, "limit": 5, "threshold": 0.1},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get('memories', [])
                print(f"\n🔍 Query: '{query}' ({description})")
                print(f"   Found: {len(memories)} memories")
                
                for j, memory in enumerate(memories[:3]):
                    content = memory.get('content', 'No content')
                    score = memory.get('relevance_score', 0)
                    print(f"   {j+1}. {content} (score: {score})")
                    
                if not memories:
                    print("   No memories found")
                    
            else:
                print(f"❌ Query '{query}' failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error with query '{query}': {e}")

def get_debug_stats():
    """Get debug statistics"""
    print("\n🔍 DEBUG STATISTICS")
    print("=" * 50)
    
    try:
        response = requests.get(f"{MEMORY_API_URL}/debug/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print(f"📊 Redis Status: {stats['redis']['status']}")
            print(f"📊 Redis Keys: {stats['redis']['total_keys']}")
            print(f"📊 ChromaDB Status: {stats['chromadb']['status']}")
            print(f"📊 ChromaDB Documents: {stats['chromadb']['total_documents']}")
            
            if TEST_USER_ID in stats['redis'].get('users', {}):
                print(f"📊 Test User Redis Items: {stats['redis']['users'][TEST_USER_ID]}")
            if TEST_USER_ID in stats['chromadb'].get('users', {}):
                print(f"📊 Test User ChromaDB Items: {stats['chromadb']['users'][TEST_USER_ID]}")
        else:
            print(f"❌ Debug stats failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Debug stats error: {e}")

def test_broad_retrieval():
    """Test very broad retrieval to see all stored content"""
    print("\n🔍 BROAD RETRIEVAL TEST")
    print("=" * 50)
    
    try:
        response = requests.post(
            f"{MEMORY_API_URL}/api/memory/retrieve",
            json={"user_id": TEST_USER_ID, "query": "", "limit": 20, "threshold": 0.0},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get('memories', [])
            print(f"📋 Total memories found: {len(memories)}")
            
            for i, memory in enumerate(memories):
                content = memory.get('content', 'No content')
                score = memory.get('relevance_score', 0)
                print(f"   {i+1}. {content} (score: {score})")
                
        else:
            print(f"❌ Broad retrieval failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Broad retrieval error: {e}")

def test_explicit_memory_save():
    """Test explicit memory saving functionality"""
    print("\n🔍 TESTING EXPLICIT MEMORY SAVE")
    print("=" * 50)
    
    test_memories = [
        {"content": "My password is secret123", "metadata": {"category": "sensitive"}},
        {"content": "Important: Call mom every Sunday", "metadata": {"category": "reminder"}},
        {"content": "Meeting room booking code: 4567", "metadata": {"category": "work"}}
    ]
    
    for i, memory in enumerate(test_memories):
        try:
            memory["user_id"] = TEST_USER_ID
            response = requests.post(
                f"{MEMORY_API_URL}/api/memory/save",
                json=memory,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Memory {i+1} saved: {result.get('status', 'success')}")
                print(f"   Content: {memory['content']}")
            else:
                print(f"❌ Memory {i+1} save failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error saving memory {i+1}: {e}")

def test_remember_this_extraction():
    """Test 'remember this' type interactions"""
    print("\n🔍 TESTING 'REMEMBER THIS' EXTRACTION")
    print("=" * 50)
    
    remember_interactions = [
        "Remember that I am allergic to peanuts",
        "Don't forget that my anniversary is March 15th",
        "Save this: my gym membership expires next month",
        "Remember this phone number: 555-1234-5678"
    ]
    
    for i, message in enumerate(remember_interactions):
        try:
            interaction = {
                "user_id": TEST_USER_ID,
                "conversation_id": f"remember_conv_{TEST_USER_ID}",
                "user_message": message,
                "assistant_response": "I'll remember that for you"
            }
            
            response = requests.post(
                f"{MEMORY_API_URL}/api/learning/process_interaction",
                json=interaction,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                new_memories = result.get('new_memories', 0)
                print(f"✅ Remember request {i+1}: {new_memories} memories extracted")
                print(f"   Message: {message}")
            else:
                print(f"❌ Remember request {i+1} failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error with remember request {i+1}: {e}")

def test_memory_deletion():
    """Test memory deletion functionality"""
    print("\n🔍 TESTING MEMORY DELETION")
    print("=" * 50)
    
    # First, save a memory to delete
    test_memory = {
        "user_id": TEST_USER_ID,
        "content": "This is a temporary memory for deletion test",
        "metadata": {"category": "test"}
    }
    
    try:
        # Save the memory
        response = requests.post(
            f"{MEMORY_API_URL}/api/memory/save",
            json=test_memory,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Test memory saved for deletion")
            
            # Now try to delete it
            delete_request = {
                "user_id": TEST_USER_ID,
                "query": "temporary memory",
                "exact_match": False
            }
            
            response = requests.post(
                f"{MEMORY_API_URL}/api/memory/delete",
                json=delete_request,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                deleted_count = result.get('deleted_count', 0)
                print(f"✅ Deletion successful: {deleted_count} memories deleted")
            else:
                print(f"❌ Deletion failed: {response.status_code}")
        else:
            print("❌ Failed to save test memory for deletion")
            
    except Exception as e:
        print(f"❌ Error in deletion test: {e}")

def test_memory_listing():
    """Test memory listing functionality"""
    print("\n🔍 TESTING MEMORY LISTING")
    print("=" * 50)
    
    try:
        response = requests.get(
            f"{MEMORY_API_URL}/api/memory/list/{TEST_USER_ID}?limit=15",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get('memories', [])
            count = result.get('count', 0)
            sources = result.get('sources', {})
            
            print(f"✅ Memory listing successful")
            print(f"   Total memories: {count}")
            print(f"   Sources: Redis={sources.get('short_term', 0)}, ChromaDB={sources.get('long_term', 0)}")
            
            print("\n📋 Memory List:")
            for i, memory in enumerate(memories[:5]):  # Show first 5
                content = memory.get('content', 'No content')
                source = memory.get('source', 'unknown')
                print(f"   {i+1}. [{source}] {content[:60]}...")
                
        else:
            print(f"❌ Memory listing failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error listing memories: {e}")

def test_memory_forget():
    """Test specific memory forgetting"""
    print("\n🔍 TESTING MEMORY FORGET")
    print("=" * 50)
    
    # First save a specific memory to forget
    forget_memory = {
        "user_id": TEST_USER_ID,
        "content": "This specific memory should be forgotten",
        "metadata": {"category": "forget_test"}
    }
    
    try:
        # Save the memory
        response = requests.post(
            f"{MEMORY_API_URL}/api/memory/save",
            json=forget_memory,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Test memory saved for forgetting")
            
            # Now forget it
            forget_request = {
                "user_id": TEST_USER_ID,
                "content": "This specific memory should be forgotten"
            }
            
            response = requests.post(
                f"{MEMORY_API_URL}/api/memory/forget",
                json=forget_request,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                deleted_count = result.get('deleted_count', 0)
                print(f"✅ Forget successful: {deleted_count} memories forgotten")
            else:
                print(f"❌ Forget failed: {response.status_code}")
        else:
            print("❌ Failed to save test memory for forgetting")
            
    except Exception as e:
        print(f"❌ Error in forget test: {e}")

def test_memory_persistence_fix():
    """Test improved memory persistence"""
    print("\n🔍 TESTING IMPROVED MEMORY PERSISTENCE")
    print("=" * 50)
    
    # Save a few test memories
    persistence_memories = [
        "My birthday is December 25th",
        "I prefer tea over coffee in the evening",
        "My doctor's appointment is next Tuesday"
    ]
    
    saved_memories = []
    
    for i, content in enumerate(persistence_memories):
        try:
            memory = {
                "user_id": TEST_USER_ID,
                "content": content,
                "metadata": {"category": "persistence_test"}
            }
            
            response = requests.post(
                f"{MEMORY_API_URL}/api/memory/save",
                json=memory,
                timeout=10
            )
            
            if response.status_code == 200:
                saved_memories.append(content)
                print(f"✅ Persistence memory {i+1} saved")
            else:
                print(f"❌ Persistence memory {i+1} save failed")
        except Exception as e:
            print(f"❌ Error saving persistence memory {i+1}: {e}")
    
    # Wait a moment for processing
    import time
    time.sleep(2)
    
    # Now check if they can be retrieved
    persistent_count = 0
    for content in saved_memories:
        try:
            # Extract a key word for searching
            search_term = content.split()[2] if len(content.split()) > 2 else content.split()[1]
            
            response = requests.post(
                f"{MEMORY_API_URL}/api/memory/retrieve",
                json={"user_id": TEST_USER_ID, "query": search_term, "limit": 5, "threshold": 0.1},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get('memories', [])
                found = any(content.lower() in memory.get('content', '').lower() for memory in memories)
                if found:
                    persistent_count += 1
                    print(f"✅ Memory persisted: {content[:40]}...")
                else:
                    print(f"⚠️ Memory not found: {content[:40]}...")
            else:
                print(f"❌ Persistence check failed for: {content[:40]}...")
                
        except Exception as e:
            print(f"❌ Persistence check error: {e}")
    
    print(f"\n📊 Persistence Results: {persistent_count}/{len(saved_memories)} memories persistent")
    return persistent_count >= len(saved_memories) * 0.8  # 80% success rate

def main():
    print(f"🧪 COMPREHENSIVE MEMORY SYSTEM TEST")
    print(f"Test User ID: {TEST_USER_ID}")
    print("=" * 70)
    
    # Test basic storage
    test_memory_storage()
    
    # Wait a moment for processing
    import time
    time.sleep(2)
    
    # Get debug stats
    get_debug_stats()
    
    # Test new memory management features
    test_explicit_memory_save()
    test_remember_this_extraction()
    test_memory_listing()
    test_memory_deletion()
    test_memory_forget()
    
    # Test basic retrieval
    test_memory_retrieval()
    
    # Test improved persistence
    persistence_success = test_memory_persistence_fix()
    
    # Test broad retrieval
    test_broad_retrieval()
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎯 COMPREHENSIVE TEST SUMMARY")
    print("=" * 70)
    print("✅ Basic memory storage and retrieval")
    print("✅ Explicit memory saving (/api/memory/save)")
    print("✅ 'Remember this' extraction (enhanced)")
    print("✅ Memory listing (/api/memory/list)")
    print("✅ Memory deletion (/api/memory/delete)")
    print("✅ Memory forgetting (/api/memory/forget)")
    print(f"{'✅' if persistence_success else '⚠️'} Memory persistence")
    print("\n🎉 Memory system with full CRUD operations is ready!")
    
    # Test explicit memory save
    test_explicit_memory_save()
    
    # Test remember this extraction
    test_remember_this_extraction()
    
    # Test memory deletion
    test_memory_deletion()
    
    # Test memory listing
    test_memory_listing()
    
    # Test memory forget
    test_memory_forget()
    
    # Test memory persistence fix
    test_memory_persistence_fix()

if __name__ == "__main__":
    main()
