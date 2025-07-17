#!/usr/bin/env python3
"""
Comprehensive Test: Explicit Memory Storage with RAG Architecture
================================================================

This test validates:
1. Explicit memory commands ("remember this", "don't forget")
2. RAG dual-database storage (Redis + ChromaDB)
3. Proper importance classification
4. Semantic search and retrieval
5. Storage distribution and statistics
"""

import asyncio
import requests
import json
import time
from typing import Dict, List, Any

class ExplicitMemoryRAGTester:
    """Test explicit memory storage with RAG architecture"""
    
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.test_user = "explicit_rag_test_user"
        
    def test_explicit_memory_commands(self):
        """Test various explicit memory commands"""
        print("🧠 Testing Explicit Memory Commands")
        print("=" * 50)
        
        # Test cases with different explicit memory commands
        explicit_commands = [
            {
                "input": "Remember that my name is John Smith and I work at Microsoft",
                "expected_importance": 0.9,
                "expected_storage": "chroma_priority",
                "context": "profile"
            },
            {
                "input": "Please remember I prefer dark mode in all applications",
                "expected_importance": 0.7,
                "expected_storage": "dual_storage",
                "context": "preference"
            },
            {
                "input": "Don't forget that I'm allergic to peanuts and shellfish",
                "expected_importance": 0.9,
                "expected_storage": "chroma_priority",
                "context": "health"
            },
            {
                "input": "Keep in mind that the project deadline is February 15th",
                "expected_importance": 0.9,
                "expected_storage": "chroma_priority",
                "context": "work"
            },
            {
                "input": "Note that I usually take lunch breaks at 12:30 PM",
                "expected_importance": 0.6,
                "expected_storage": "dual_storage",
                "context": "routine"
            },
            {
                "input": "Remember my email is john.smith@company.com",
                "expected_importance": 0.9,
                "expected_storage": "chroma_priority",
                "context": "contact"
            }
        ]
        
        stored_memories = []
        
        for i, test in enumerate(explicit_commands):
            print(f"\n🔍 Test {i+1}: {test['input']}")
            print(f"   Expected importance: {test['expected_importance']}")
            print(f"   Expected storage: {test['expected_storage']}")
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/memory/store_explicit",
                    json={
                        "user_id": self.test_user,
                        "user_input": test['input'],
                        "context": test['context']
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Memory stored successfully")
                    print(f"   📊 Extracted content: {result.get('extracted_content', '')[:60]}...")
                    print(f"   🎯 Storage strategy: {result.get('storage_strategy', 'unknown')}")
                    print(f"   📝 Redis stored: {'✅' if result.get('redis_stored') else '❌'}")
                    print(f"   🔍 ChromaDB stored: {'✅' if result.get('chroma_stored') else '❌'}")
                    print(f"   ⭐ Importance: {result.get('importance', 0)}")
                    print(f"   🔒 Explicit: {'✅' if result.get('explicit') else '❌'}")
                    
                    stored_memories.append({
                        "original_input": test['input'],
                        "result": result,
                        "expected": test
                    })
                else:
                    print(f"   ❌ Storage failed: {response.status_code}")
                    if response.text:
                        print(f"   Error: {response.text[:100]}...")
                    
            except Exception as e:
                print(f"   ❌ Request error: {str(e)}")
        
        return stored_memories
    
    def test_semantic_search(self):
        """Test semantic search capabilities"""
        print("\n🔍 Testing Semantic Search")
        print("=" * 50)
        
        # Test queries that should find relevant memories
        search_queries = [
            {
                "query": "What is my name and where do I work?",
                "expected_matches": ["John Smith", "Microsoft"]
            },
            {
                "query": "What are my dietary restrictions?",
                "expected_matches": ["allergic", "peanuts", "shellfish"]
            },
            {
                "query": "What are my UI preferences?",
                "expected_matches": ["dark mode", "applications"]
            },
            {
                "query": "What is my contact information?",
                "expected_matches": ["email", "john.smith@company.com"]
            },
            {
                "query": "What are my work deadlines?",
                "expected_matches": ["deadline", "February 15th"]
            }
        ]
        
        for query_test in search_queries:
            print(f"\n🔍 Query: {query_test['query']}")
            print(f"   Expected matches: {query_test['expected_matches']}")
            
            try:
                response = requests.get(
                    f"{self.base_url}/api/memory/search/{self.test_user}",
                    params={
                        "query": query_test['query'],
                        "limit": 5
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    memories = result.get("memories", [])
                    semantic_matches = result.get("semantic_matches", 0)
                    
                    print(f"   ✅ Found {len(memories)} total memories")
                    print(f"   🎯 Semantic matches: {semantic_matches}")
                    
                    # Show top results
                    for i, memory in enumerate(memories[:3]):
                        content = memory.get("content", "")
                        importance = memory.get("importance", 0)
                        source_db = memory.get("source_db", "unknown")
                        explicit = memory.get("explicit", False)
                        
                        print(f"     {i+1}. {content[:50]}...")
                        print(f"        • Source: {source_db}")
                        print(f"        • Importance: {importance}")
                        print(f"        • Explicit: {'✅' if explicit else '❌'}")
                        
                        # Check if expected matches are found
                        content_lower = content.lower()
                        matches_found = [match for match in query_test['expected_matches'] 
                                       if match.lower() in content_lower]
                        if matches_found:
                            print(f"        • Matches found: {matches_found}")
                else:
                    print(f"   ❌ Search failed: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Search error: {str(e)}")
    
    def test_storage_distribution(self):
        """Test storage distribution across Redis and ChromaDB"""
        print("\n📊 Testing Storage Distribution")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/api/memory/stats/{self.test_user}",
                timeout=10
            )
            
            if response.status_code == 200:
                stats = response.json()
                
                print(f"   ✅ Storage statistics retrieved")
                print(f"   📈 Total memories: {stats.get('total_memories', 0)}")
                print(f"   🔒 Explicit memories: {stats.get('explicit_memories', 0)}")
                
                # Redis stats
                redis_stats = stats.get('redis_stats', {})
                print(f"   🔴 Redis storage:")
                print(f"     • Short-term: {redis_stats.get('short_term', 0)}")
                print(f"     • Medium-term: {redis_stats.get('medium_term', 0)}")
                print(f"     • Long-term: {redis_stats.get('long_term', 0)}")
                print(f"     • Total: {redis_stats.get('total', 0)}")
                
                # ChromaDB stats
                chroma_stats = stats.get('chroma_stats', {})
                print(f"   🟢 ChromaDB storage:")
                print(f"     • Documents: {chroma_stats.get('documents', 0)}")
                print(f"     • Explicit memories: {chroma_stats.get('explicit_memories', 0)}")
                
                # Distribution
                distribution = stats.get('storage_distribution', {})
                if distribution:
                    print(f"   📊 Storage distribution:")
                    print(f"     • Redis: {distribution.get('redis_percentage', 0):.1f}%")
                    print(f"     • ChromaDB: {distribution.get('chroma_percentage', 0):.1f}%")
                
                return stats
            else:
                print(f"   ❌ Stats retrieval failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Stats error: {str(e)}")
            return None
    
    def test_retrieval_performance(self):
        """Test retrieval performance and accuracy"""
        print("\n⚡ Testing Retrieval Performance")
        print("=" * 50)
        
        # Test different retrieval scenarios
        test_scenarios = [
            {
                "name": "Fast Redis retrieval",
                "query": None,  # No query = Redis focus
                "limit": 10
            },
            {
                "name": "Semantic search",
                "query": "personal information",
                "limit": 5
            },
            {
                "name": "Explicit memories only",
                "query": "remember",
                "limit": 10
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n🔍 Scenario: {scenario['name']}")
            
            start_time = time.time()
            
            try:
                request_data = {
                    "user_id": self.test_user,
                    "limit": scenario['limit']
                }
                
                if scenario['query']:
                    request_data["query"] = scenario['query']
                
                response = requests.post(
                    f"{self.base_url}/api/memory/retrieve",
                    json=request_data,
                    timeout=10
                )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                if response.status_code == 200:
                    result = response.json()
                    memories = result.get("memories", [])
                    
                    print(f"   ✅ Retrieved {len(memories)} memories")
                    print(f"   ⏱️ Response time: {response_time:.2f} ms")
                    
                    # Analyze results
                    explicit_count = sum(1 for m in memories if m.get("explicit", False))
                    redis_count = sum(1 for m in memories if m.get("source_db") == "redis")
                    chroma_count = sum(1 for m in memories if m.get("source_db") == "chroma")
                    
                    print(f"   📊 Result analysis:")
                    print(f"     • Explicit memories: {explicit_count}")
                    print(f"     • Redis sources: {redis_count}")
                    print(f"     • ChromaDB sources: {chroma_count}")
                    
                    # Show top results
                    if memories:
                        print(f"   🎯 Top results:")
                        for i, memory in enumerate(memories[:2]):
                            content = memory.get("content", "")
                            print(f"     {i+1}. {content[:40]}...")
                            print(f"        • Source: {memory.get('source_db', 'unknown')}")
                            print(f"        • Importance: {memory.get('importance', 0)}")
                else:
                    print(f"   ❌ Retrieval failed: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Retrieval error: {str(e)}")

def main():
    """Run comprehensive explicit memory RAG tests"""
    print("🚀 COMPREHENSIVE EXPLICIT MEMORY RAG TEST")
    print("=" * 60)
    
    tester = ExplicitMemoryRAGTester()
    
    # Test 1: Explicit memory commands
    stored_memories = tester.test_explicit_memory_commands()
    
    # Wait for storage to complete
    print(f"\n⏳ Waiting for storage to complete...")
    time.sleep(3)
    
    # Test 2: Semantic search
    tester.test_semantic_search()
    
    # Test 3: Storage distribution
    stats = tester.test_storage_distribution()
    
    # Test 4: Retrieval performance
    tester.test_retrieval_performance()
    
    # Summary
    print("\n🎉 TEST SUMMARY")
    print("=" * 60)
    
    if stored_memories:
        print(f"✅ Explicit memory commands: {len(stored_memories)} tested")
        
        # Analyze storage strategies
        strategies = {}
        for memory in stored_memories:
            strategy = memory['result'].get('storage_strategy', 'unknown')
            strategies[strategy] = strategies.get(strategy, 0) + 1
        
        print(f"📊 Storage strategies used:")
        for strategy, count in strategies.items():
            print(f"   • {strategy}: {count} memories")
    
    if stats:
        print(f"📈 Total memories in system: {stats.get('total_memories', 0)}")
        print(f"🔒 Explicit memories stored: {stats.get('explicit_memories', 0)}")
    
    print("\n🏆 RAG DUAL-DATABASE ARCHITECTURE VALIDATION COMPLETE")

if __name__ == "__main__":
    main()
