#!/usr/bin/env python3
"""
Memory Persistence Diagnostic Tool
Analyzes memory retrieval thresholds and persistence issues
"""

import requests
import json
from datetime import datetime

def test_memory_retrieval_thresholds():
    """Test memory retrieval with different queries and analyze similarity scores"""
    print("🔍 MEMORY PERSISTENCE DIAGNOSTIC")
    print("=" * 50)
    
    # Test different queries that should match existing memories
    test_queries = [
        "what do you know about me",
        "J.P.",
        "Swift", 
        "work",
        "financial messaging",
        "banking",
        "Python programming",
        "AI development"
    ]
    
    print("📊 Testing memory retrieval for different queries:")
    print()
    
    all_memories_found = []
    
    for query in test_queries:
        try:
            payload = {
                "user_id": "global_user",
                "query": query,
                "limit": 5
            }
            
            response = requests.post("http://localhost:5001/api/memory/retrieve", 
                                   json=payload, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                
                print(f"🔍 Query: '{query}'")
                print(f"   Found: {len(memories)} memories")
                
                if memories:
                    # Show similarity scores
                    for i, memory in enumerate(memories):
                        similarity = memory.get("similarity_score", 0)
                        content_preview = memory.get("content", "")[:60]
                        print(f"   [{i+1}] Score: {similarity:.4f} - {content_preview}...")
                        
                        # Collect all unique memories
                        if memory not in all_memories_found:
                            all_memories_found.append(memory)
                else:
                    print("   ❌ No memories retrieved")
                print()
                
            else:
                print(f"❌ Query '{query}' failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error with query '{query}': {e}")
    
    return all_memories_found

def analyze_similarity_thresholds(memories):
    """Analyze similarity score distribution"""
    print("📈 SIMILARITY SCORE ANALYSIS")
    print("=" * 35)
    
    if not memories:
        print("❌ No memories to analyze")
        return
    
    # Extract all similarity scores
    scores = []
    for memory in memories:
        score = memory.get("similarity_score", 0)
        scores.append(score)
    
    if scores:
        min_score = min(scores)
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)
        
        print(f"📊 Similarity Score Statistics:")
        print(f"   Minimum score: {min_score:.4f}")
        print(f"   Maximum score: {max_score:.4f}")
        print(f"   Average score: {avg_score:.4f}")
        print(f"   Total memories: {len(scores)}")
        print()
        
        # Analyze score distribution
        high_scores = [s for s in scores if s > 0.5]
        medium_scores = [s for s in scores if 0.0 <= s <= 0.5]
        low_scores = [s for s in scores if s < 0.0]
        
        print(f"📈 Score Distribution:")
        print(f"   High relevance (>0.5): {len(high_scores)} memories")
        print(f"   Medium relevance (0.0-0.5): {len(medium_scores)} memories")
        print(f"   Low relevance (<0.0): {len(low_scores)} memories")
        print()
        
        # Check if threshold might be too high
        if max_score < 0.3:
            print("⚠️  POTENTIAL ISSUE: All similarity scores are below 0.3")
            print("   This suggests the retrieval threshold might be too high")
            print("   or the embedding model isn't finding good matches")
        
        if len(high_scores) == 0:
            print("⚠️  ISSUE: No high-confidence matches found")
            print("   Memory function may not be retrieving relevant context")
    
def check_memory_storage_pattern():
    """Check how memories are being stored"""
    print("💾 MEMORY STORAGE PATTERN ANALYSIS")
    print("=" * 40)
    
    try:
        # Get all memories for the user
        payload = {
            "user_id": "global_user",
            "query": "",  # Empty query to get all memories
            "limit": 20
        }
        
        response = requests.post("http://localhost:5001/api/memory/retrieve",
                               json=payload, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get("memories", [])
            
            print(f"📊 Total memories in database: {len(memories)}")
            
            # Analyze memory sources
            sources = {}
            types = {}
            
            for memory in memories:
                source = memory.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1
                
                # Try to extract context type
                context_str = memory.get("context", "{}")
                try:
                    context = json.loads(context_str) if isinstance(context_str, str) else context_str
                    mem_type = context.get("type", "unknown")
                    types[mem_type] = types.get(mem_type, 0) + 1
                except:
                    types["unknown"] = types.get("unknown", 0) + 1
            
            print(f"\n📈 Memory Sources:")
            for source, count in sources.items():
                print(f"   {source}: {count} memories")
                
            print(f"\n📈 Memory Types:")
            for mem_type, count in types.items():
                print(f"   {mem_type}: {count} memories")
                
            # Show recent memories
            print(f"\n📝 Recent Memory Samples:")
            for i, memory in enumerate(memories[:5]):
                content = memory.get("content", "")[:80]
                importance = memory.get("importance", 0)
                print(f"   [{i+1}] (imp: {importance}) {content}...")
                
        else:
            print(f"❌ Failed to get memories: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error analyzing storage: {e}")

def check_function_configuration():
    """Check current function configuration for threshold issues"""
    print("\n⚙️ FUNCTION CONFIGURATION CHECK")
    print("=" * 35)
    
    print("Current function settings:")
    print("   MEMORY_ENABLED: True")
    print("   MEMORY_API_URL: http://memory-api:5001")
    print("   MAX_MEMORIES: 3")
    print("   DEBUG_LOGGING: True")
    print("   USER_ID_SOURCE: global_user")
    print()
    
    print("🔧 POTENTIAL ISSUES & SOLUTIONS:")
    print("1. MAX_MEMORIES = 3 might be too low for diverse queries")
    print("   → Consider increasing to 5-10")
    print()
    print("2. No similarity threshold configured in function")
    print("   → Function takes whatever the API returns")
    print()
    print("3. User context might not be consistent between sessions")
    print("   → All memories stored under 'global_user' should persist")

def suggest_fixes():
    """Suggest specific fixes for persistence issues"""
    print("\n🔧 SUGGESTED FIXES FOR PERSISTENCE ISSUES")
    print("=" * 45)
    
    print("IMMEDIATE ACTIONS:")
    print("1. 📈 Increase MAX_MEMORIES from 3 to 10")
    print("2. 🎯 Add similarity threshold filtering in function")
    print("3. 🔍 Improve memory query processing")
    print("4. 💾 Enhance memory storage with better context")
    print()
    
    print("CONFIGURATION CHANGES:")
    print("- Update MAX_MEMORIES valve to 10")
    print("- Add minimum similarity threshold (e.g., -0.5)")
    print("- Store more detailed conversation context")
    print("- Include user identification in memory content")

def main():
    """Run complete diagnostic"""
    print("🧬 MEMORY PERSISTENCE DIAGNOSTIC TOOL")
    print("Analyzing memory retrieval and persistence issues")
    print("=" * 60)
    print()
    
    # Test memory retrieval with various queries
    memories = test_memory_retrieval_thresholds()
    
    # Analyze similarity scores
    analyze_similarity_thresholds(memories)
    
    # Check storage patterns
    check_memory_storage_pattern()
    
    # Check configuration
    check_function_configuration()
    
    # Suggest fixes
    suggest_fixes()
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSIS COMPLETE")
    print("Check the analysis above for specific issues and solutions")
    print("=" * 60)

if __name__ == "__main__":
    main()
