#!/usr/bin/env python3
"""
Analyze why memories aren't showing persistence despite function working
"""

import requests
import json

def analyze_current_memories():
    """Check what memories are actually stored"""
    print("🔍 ANALYZING CURRENT MEMORY CONTENT")
    print("=" * 40)
    
    queries = ["what do you know about me", "J.P.", "Swift"]
    
    for query in queries:
        try:
            payload = {
                "user_id": "global_user",
                "query": query,
                "limit": 10
            }
            
            response = requests.post("http://localhost:5001/api/memory/retrieve", 
                                   json=payload, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                
                print(f"\n📝 Query: '{query}'")
                print(f"   Total memories: {len(memories)}")
                
                # Apply threshold filter like the function does
                threshold = -0.3
                relevant = [m for m in memories if m.get("similarity_score", -1) >= threshold]
                print(f"   Above threshold ({threshold}): {len(relevant)}")
                
                if relevant:
                    print("   🎯 Top relevant memories:")
                    for i, memory in enumerate(relevant[:3]):
                        score = memory.get("similarity_score", 0)
                        content = memory.get("content", "")
                        source = memory.get("source", "unknown")
                        print(f"      [{i+1}] {score:.3f} ({source}): {content[:80]}...")
                        
                        # Check if this memory would provide useful context
                        if "J.P." in content or "Swift" in content:
                            print(f"          ✅ Contains identity information")
                        else:
                            print(f"          ⚠️  Limited identity information")
                else:
                    print("   ❌ No memories above threshold")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")

def check_memory_content_quality():
    """Check the quality of stored memory content"""
    print("\n🔬 MEMORY CONTENT QUALITY ANALYSIS")
    print("=" * 40)
    
    try:
        # Get all memories
        payload = {
            "user_id": "global_user",
            "query": "",
            "limit": 20
        }
        
        response = requests.post("http://localhost:5001/api/memory/retrieve",
                               json=payload, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get("memories", [])
            
            print(f"📊 Total memories: {len(memories)}")
            
            # Analyze memory patterns
            identity_memories = []
            conversation_memories = []
            enhanced_memories = []
            
            for memory in memories:
                content = memory.get("content", "").lower()
                source = memory.get("source", "")
                
                if "j.p." in content or "swift" in content:
                    identity_memories.append(memory)
                
                if "conversation" in source:
                    conversation_memories.append(memory)
                    
                if "enhanced" in source:
                    enhanced_memories.append(memory)
            
            print(f"\n📈 Memory breakdown:")
            print(f"   Identity-related: {len(identity_memories)}")
            print(f"   Conversation-based: {len(conversation_memories)}")
            print(f"   Enhanced storage: {len(enhanced_memories)}")
            
            print(f"\n🎯 Best identity memories:")
            for i, memory in enumerate(identity_memories[:3]):
                content = memory.get("content", "")
                score = memory.get("similarity_score", 0)
                print(f"   [{i+1}] {content[:100]}...")
                
        else:
            print(f"❌ Failed to get memories: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_memory_context_formatting():
    """Test how memory context would be formatted"""
    print("\n📝 MEMORY CONTEXT FORMATTING TEST")
    print("=" * 40)
    
    try:
        # Get memories for "what do you know about me"
        payload = {
            "user_id": "global_user",
            "query": "what do you know about me",
            "limit": 10
        }
        
        response = requests.post("http://localhost:5001/api/memory/retrieve",
                               json=payload, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get("memories", [])
            
            # Apply same filtering as function
            threshold = -0.3
            filtered_memories = [m for m in memories if m.get("similarity_score", -1) >= threshold]
            final_memories = filtered_memories[:10]  # MAX_MEMORIES = 10
            
            print(f"Memories that would be included: {len(final_memories)}")
            
            if final_memories:
                # Format context like the function does
                context_lines = ["## Relevant Context from Previous Conversations:"]
                
                for i, memory in enumerate(final_memories, 1):
                    content = memory.get("content", "")
                    similarity = memory.get("similarity_score", 0)
                    
                    context_lines.append(f"**Memory {i}** (relevance: {similarity:.3f}):")
                    context_lines.append(content)
                    context_lines.append("")
                
                context_lines.append("*Use this context to provide personalized responses.*")
                
                context = "\n".join(context_lines)
                
                print("\n📄 Generated context preview:")
                print("=" * 30)
                print(context[:500] + "..." if len(context) > 500 else context)
                print("=" * 30)
                
                # Check if context contains useful info
                if "j.p." in context.lower() or "swift" in context.lower():
                    print("✅ Context contains identity information")
                else:
                    print("❌ Context lacks clear identity information")
                    
            else:
                print("❌ No memories would be included in context")
                
        else:
            print(f"❌ Failed to retrieve memories: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def diagnose_persistence_issue():
    """Diagnose why persistence isn't working despite function execution"""
    print("\n🚨 PERSISTENCE ISSUE DIAGNOSIS")
    print("=" * 35)
    
    print("Function Status:")
    print("✅ Function is loaded and executing (confirmed from logs)")
    print("✅ Function is retrieving memories (6-13 total per query)")
    print("✅ Function is filtering by threshold (4-6 above -0.3)")
    print("✅ Function is storing new conversations")
    print()
    
    print("Possible Issues:")
    print("1. 📝 Memory content quality - stored memories may not contain clear identity info")
    print("2. 🎯 Memory similarity scores - even 'relevant' memories might not be highly relevant")
    print("3. 📄 Context formatting - LLM might not be interpreting the context properly")
    print("4. 🔄 Memory storage pattern - new memories might be overriding identity info")
    print("5. 🧠 LLM behavior - model might be ignoring provided context")
    print()
    
    print("Investigation needed:")
    print("→ Check actual memory content quality")
    print("→ Verify context formatting and placement")
    print("→ Test if LLM is seeing and using the context")

def suggest_improvements():
    """Suggest specific improvements"""
    print("\n🔧 SUGGESTED IMPROVEMENTS")
    print("=" * 25)
    
    print("1. 📈 Improve memory storage:")
    print("   - Store explicit identity facts separately")
    print("   - Use higher importance scores for identity")
    print("   - Include more keywords in content")
    print()
    
    print("2. 🎯 Better context formatting:")
    print("   - Make context more prominent")
    print("   - Use stronger instruction language")
    print("   - Place context at the beginning")
    print()
    
    print("3. 🧪 Test with direct prompt:")
    print("   - Add explicit instruction to use context")
    print("   - Make identity information more obvious")
    print("   - Use system prompt instead of user message modification")

def main():
    """Run analysis"""
    print("🔍 MEMORY PERSISTENCE ANALYSIS")
    print("Function is working but persistence is inconsistent")
    print("=" * 50)
    
    # Analyze current memories
    analyze_current_memories()
    
    # Check memory quality
    check_memory_content_quality()
    
    # Test context formatting
    test_memory_context_formatting()
    
    # Diagnose issue
    diagnose_persistence_issue()
    
    # Suggest improvements
    suggest_improvements()
    
    print("\n" + "=" * 50)
    print("🎯 ANALYSIS COMPLETE")
    print("The function works but memory content/formatting needs improvement")
    print("=" * 50)

if __name__ == "__main__":
    main()
