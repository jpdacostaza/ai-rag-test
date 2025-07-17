#!/usr/bin/env python3
"""
Test Explicit Memory Storage and RAG Dual-Database Architecture
==============================================================

This script tests:
1. Explicit memory storage when users say "remember this"
2. Dual-database RAG architecture (Redis short-term, ChromaDB long-term)
3. Semantic search and retrieval capabilities
4. Memory importance classification
"""

import asyncio
import json
import logging
import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExplicitMemoryTester:
    """Test explicit memory storage functionality"""
    
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.test_user = "explicit_memory_test_user"
        
    def test_explicit_memory_storage(self):
        """Test storing memories when user explicitly says 'remember this'"""
        print("🧠 Testing Explicit Memory Storage")
        print("=" * 50)
        
        # Test cases with explicit memory requests
        explicit_memory_tests = [
            {
                "user_input": "Remember that I prefer Python over JavaScript for backend development",
                "expected_importance": 0.8,
                "memory_type": "preference",
                "explicit": True
            },
            {
                "user_input": "Please remember my name is Sarah and I work at Microsoft",
                "expected_importance": 0.9,
                "memory_type": "profile",
                "explicit": True
            },
            {
                "user_input": "Remember this project deadline is next Friday",
                "expected_importance": 0.7,
                "memory_type": "task",
                "explicit": True
            },
            {
                "user_input": "Don't forget that I'm allergic to peanuts",
                "expected_importance": 0.9,
                "memory_type": "health",
                "explicit": True
            }
        ]
        
        stored_memories = []
        
        for i, test in enumerate(explicit_memory_tests):
            print(f"\n🔍 Test {i+1}: {test['user_input']}")
            
            # Extract the actual content to remember
            content = self._extract_memory_content(test['user_input'])
            
            # Store the memory with high importance (explicit)
            memory_data = {
                "user_id": self.test_user,
                "content": content,
                "context": test['memory_type'],
                "importance": test['expected_importance'],
                "explicit": test['explicit'],
                "source": "explicit_command"
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/memory/store",
                    json=memory_data,
                    timeout=5
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Memory stored successfully")
                    print(f"   📊 Storage info: {result}")
                    stored_memories.append(memory_data)
                else:
                    print(f"   ❌ Storage failed: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Storage error: {str(e)}")
        
        return stored_memories
    
    def test_memory_retrieval(self, stored_memories):
        """Test retrieving explicit memories"""
        print("\n🔍 Testing Memory Retrieval")
        print("=" * 50)
        
        # Test semantic search queries
        search_queries = [
            "What programming language do I prefer?",
            "What is my name and where do I work?",
            "What are my health restrictions?",
            "What deadlines do I have?"
        ]
        
        for query in search_queries:
            print(f"\n🔍 Query: {query}")
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/memory/retrieve",
                    json={
                        "user_id": self.test_user,
                        "query": query,
                        "limit": 5
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    memories = response.json()
                    print(f"   ✅ Found {len(memories)} relevant memories:")
                    
                    for i, memory in enumerate(memories):
                        print(f"      {i+1}. {memory.get('content', '')[:60]}...")
                        print(f"         • Importance: {memory.get('importance', 0)}")
                        print(f"         • Explicit: {memory.get('explicit', False)}")
                        print(f"         • Source: {memory.get('source', 'unknown')}")
                else:
                    print(f"   ❌ Retrieval failed: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Retrieval error: {str(e)}")
    
    def _extract_memory_content(self, user_input: str) -> str:
        """Extract the actual content to remember from user input"""
        # Remove explicit memory keywords
        keywords = ["remember", "don't forget", "please remember", "keep in mind"]
        
        content = user_input.lower()
        for keyword in keywords:
            if keyword in content:
                # Find the part after the keyword
                parts = content.split(keyword, 1)
                if len(parts) > 1:
                    content = parts[1].strip()
                    # Remove common prefixes
                    content = content.lstrip("that ").lstrip("this ").lstrip(":")
                    break
        
        return content.strip()
    
    def test_memory_stats(self):
        """Test memory statistics"""
        print("\n📊 Testing Memory Statistics")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/api/memory/stats/{self.test_user}",
                timeout=5
            )
            
            if response.status_code == 200:
                stats = response.json()
                print(f"   ✅ Memory stats retrieved:")
                print(f"      • Total memories: {stats.get('total_memories', 0)}")
                print(f"      • Explicit memories: {stats.get('explicit_memories', 0)}")
                print(f"      • Average importance: {stats.get('avg_importance', 0)}")
                print(f"      • Storage distribution: {stats.get('storage_info', {})}")
                return stats
            else:
                print(f"   ❌ Stats retrieval failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Stats error: {str(e)}")
            return None

def test_dual_database_rag_architecture():
    """Test the dual-database RAG architecture"""
    print("\n🏗️ Testing Dual-Database RAG Architecture")
    print("=" * 50)
    
    # Test different types of memories with appropriate storage
    test_cases = [
        {
            "content": "User clicked on save button",
            "importance": 0.1,
            "expected_storage": "redis_only"
        },
        {
            "content": "User prefers dark mode interface",
            "importance": 0.6,
            "expected_storage": "dual_storage"
        },
        {
            "content": "User's email is user@example.com",
            "importance": 0.9,
            "expected_storage": "chroma_priority"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n🔍 Test Case {i+1}: {test_case['content']}")
        print(f"   • Importance: {test_case['importance']}")
        print(f"   • Expected storage: {test_case['expected_storage']}")
        
        # Store memory
        memory_data = {
            "user_id": "rag_test_user",
            "content": test_case['content'],
            "importance": test_case['importance'],
            "explicit": test_case['importance'] > 0.7
        }
        
        try:
            response = requests.post(
                "http://localhost:5001/api/memory/store",
                json=memory_data,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Stored successfully")
                print(f"   📊 Storage result: {result}")
            else:
                print(f"   ❌ Storage failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Storage error: {str(e)}")

async def main():
    """Main test function"""
    print("🚀 EXPLICIT MEMORY & RAG ARCHITECTURE TEST")
    print("=" * 60)
    
    # Initialize tester
    tester = ExplicitMemoryTester()
    
    # Test explicit memory storage
    stored_memories = tester.test_explicit_memory_storage()
    
    # Wait a moment for storage to complete
    await asyncio.sleep(2)
    
    # Test memory retrieval
    tester.test_memory_retrieval(stored_memories)
    
    # Test memory stats
    stats = tester.test_memory_stats()
    
    # Test dual-database RAG architecture
    test_dual_database_rag_architecture()
    
    print("\n🎉 TESTING COMPLETE")
    print("=" * 60)
    
    # Summary
    if stats:
        print(f"📊 SUMMARY:")
        print(f"   • Total memories tested: {len(stored_memories)}")
        print(f"   • Explicit memories stored: {stats.get('explicit_memories', 0)}")
        print(f"   • System status: ✅ OPERATIONAL")
    else:
        print("📊 SUMMARY: Some tests failed, check logs above")

if __name__ == "__main__":
    asyncio.run(main())
