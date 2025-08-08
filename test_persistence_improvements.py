#!/usr/bin/env python3
"""
Test Improved Memory Function
Validates the enhanced persistence features
"""

import requests
import json

def test_improved_retrieval():
    """Test the improved memory retrieval with better thresholds"""
    print("🔍 TESTING IMPROVED MEMORY RETRIEVAL")
    print("=" * 45)
    
    # Test with the improved configuration
    test_queries = [
        "Hello my name is J.P.",
        "I work at Swift",
        "what do you know about me"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        
        # Test with improved parameters
        payload = {
            "user_id": "global_user",
            "query": query,
            "limit": 10  # Increased from 3
        }
        
        try:
            response = requests.post("http://localhost:5001/api/memory/retrieve",
                                   json=payload, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                
                # Apply improved threshold filtering
                threshold = -0.3
                filtered_memories = [m for m in memories if m.get("similarity_score", -1) >= threshold]
                
                print(f"   📊 Total retrieved: {len(memories)}")
                print(f"   ✅ Above threshold ({threshold}): {len(filtered_memories)}")
                
                if filtered_memories:
                    print("   🎯 Best matches:")
                    for i, memory in enumerate(filtered_memories[:3]):
                        score = memory.get("similarity_score", 0)
                        content = memory.get("content", "")[:60]
                        print(f"      [{i+1}] {score:.3f}: {content}...")
                else:
                    print("   ❌ No memories above threshold")
                    
            else:
                print(f"   ❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def create_better_test_memories():
    """Create better test memories with enhanced context"""
    print("\n💾 CREATING ENHANCED TEST MEMORIES")
    print("=" * 40)
    
    enhanced_memories = [
        {
            "user_id": "global_user",
            "content": "J.P. works at Swift, a financial messaging company that provides banking services and interbank communication systems.",
            "context": json.dumps({
                "type": "user_profile",
                "name": "J.P.",
                "company": "Swift",
                "industry": "financial_messaging",
                "session_persistent": True
            }),
            "importance": 0.9,
            "source": "enhanced_profile_data"
        },
        {
            "user_id": "global_user", 
            "content": "J.P. is interested in Python programming and AI development, working on OpenWebUI integration projects.",
            "context": json.dumps({
                "type": "interests_skills",
                "skills": ["Python", "AI", "OpenWebUI"],
                "projects": ["memory_integration"],
                "session_persistent": True
            }),
            "importance": 0.8,
            "source": "enhanced_profile_data"
        },
        {
            "user_id": "global_user",
            "content": "User J.P. prefers detailed technical explanations and is working on advanced AI memory systems integration.",
            "context": json.dumps({
                "type": "preferences",
                "communication_style": "technical_detailed",
                "current_projects": ["AI_memory_systems"],
                "session_persistent": True
            }),
            "importance": 0.7,
            "source": "enhanced_profile_data"
        }
    ]
    
    stored_count = 0
    for memory in enhanced_memories:
        try:
            response = requests.post("http://localhost:5001/api/memory/store",
                                   json=memory, timeout=5)
            if response.status_code == 200:
                stored_count += 1
                print(f"✅ Stored: {memory['content'][:50]}...")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"📊 Successfully stored {stored_count}/{len(enhanced_memories)} enhanced memories")

def show_function_update_instructions():
    """Show how to update the function in OpenWebUI"""
    print("\n🔧 FUNCTION UPDATE INSTRUCTIONS")
    print("=" * 35)
    
    print("To update your memory function with the improvements:")
    print()
    print("1. 🌐 Go to OpenWebUI Admin Panel")
    print("   → http://localhost:8080/admin/functions")
    print()
    print("2. 📝 Edit the 'Enhanced Memory Function Filter'")
    print("   → Click the edit button")
    print()
    print("3. 🔄 Replace the entire function code with v4.0")
    print("   → Copy from: enhanced_memory_function_filter_v4.py")
    print()
    print("4. ⚙️ Update Configuration Valves:")
    print("   → MAX_MEMORIES: 10 (increased from 3)")
    print("   → SIMILARITY_THRESHOLD: -0.3 (new filtering)")
    print("   → ENHANCED_STORAGE: True (better context)")
    print()
    print("5. 💾 Save and test the improvements")
    print()
    
    print("🎯 KEY IMPROVEMENTS:")
    print("• Higher memory retrieval limit (3 → 10)")
    print("• Similarity threshold filtering (-0.3)")
    print("• Enhanced context storage with user details")
    print("• Better keyword extraction for searchability")
    print("• Improved memory persistence across sessions")

def main():
    """Run tests and show improvements"""
    print("🚀 MEMORY FUNCTION PERSISTENCE FIX")
    print("Testing improved configuration and features")
    print("=" * 50)
    
    # Create better test memories
    create_better_test_memories()
    
    # Test improved retrieval
    test_improved_retrieval()
    
    # Show update instructions
    show_function_update_instructions()
    
    print("\n" + "=" * 50)
    print("✅ PERSISTENCE IMPROVEMENTS READY")
    print("Follow the update instructions above to apply the fixes")
    print("=" * 50)

if __name__ == "__main__":
    main()
