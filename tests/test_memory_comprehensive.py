#!/usr/bin/env python3
"""
Comprehensive Memory System Test
Test memory storage and retrieval with firewall disabled
"""

import asyncio
import json
import sys
import os
from datetime import datetime
import httpx

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.memory_service import get_memory_service, APIMemoryProvider, DatabaseMemoryProvider, PipelineMemoryProvider
from services.database_manager import db_manager

async def test_network_connectivity():
    """Test network connectivity to all services"""
    print("🌐 Testing Network Connectivity")
    print("=" * 60)
    
    services = {
        "Memory API": "http://localhost:5001/health",
        "ChromaDB": "http://localhost:8000/api/v1/heartbeat", 
        "Redis": "http://localhost:6379",
        "Ollama": "http://localhost:11434",
        "Backend": "http://localhost:3000/health",
        "OpenWebUI": "http://localhost:8080",
        "API Gateway": "http://localhost:8080/health"
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in services.items():
            try:
                response = await client.get(url)
                status = "✅ OK" if response.status_code == 200 else f"⚠️ {response.status_code}"
                print(f"  {name}: {status}")
            except Exception as e:
                print(f"  {name}: ❌ Failed - {str(e)}")

async def test_memory_storage_comprehensive():
    """Test comprehensive memory storage scenarios"""
    print("\n📝 Testing Comprehensive Memory Storage")
    print("=" * 60)
    
    # Configure for localhost access
    os.environ['MEMORY_API_URL'] = 'http://localhost:5001'
    os.environ['CHROMA_HOST'] = 'localhost'
    os.environ['CHROMA_PORT'] = '8000'
    os.environ['REDIS_HOST'] = 'localhost'
    os.environ['REDIS_PORT'] = '6379'
    os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'
    
    memory_service = get_memory_service()
    user_id = "4b00c25b-e55e-4931-a29e-07fc94deebfc"
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Regular Programming Memory",
            "content": "I prefer Python for data analysis and machine learning projects",
            "context": "Programming preferences discussion",
            "importance": 0.8,
            "explicit": False,
            "source": "conversation"
        },
        {
            "name": "Explicit Memory Command",
            "content": "Remember: I always use async/await patterns in Python code",
            "context": "Explicit memory instruction from user",
            "importance": 0.9,
            "explicit": True,
            "source": "explicit_command"
        },
        {
            "name": "Technical Preference",
            "content": "I prefer FastAPI over Flask for building REST APIs",
            "context": "Web framework discussion",
            "importance": 0.7,
            "explicit": False,
            "source": "conversation"
        },
        {
            "name": "Workflow Memory",
            "content": "I typically write tests before implementing features (TDD approach)",
            "context": "Development workflow discussion",
            "importance": 0.8,
            "explicit": False,
            "source": "conversation"
        },
        {
            "name": "Explicit Coding Style",
            "content": "Remember: I always add type hints to my Python functions",
            "context": "Explicit coding style instruction",
            "importance": 0.9,
            "explicit": True,
            "source": "explicit_command"
        }
    ]
    
    stored_memories = []
    
    for scenario in test_scenarios:
        print(f"\n🧠 Testing {scenario['name']}...")
        try:
            success = await memory_service.store_memory(
                user_id=user_id,
                content=scenario["content"],
                context=scenario["context"],
                importance=scenario["importance"],
                explicit=scenario["explicit"],
                source=scenario["source"]
            )
            
            if success:
                print(f"  ✅ Stored: {scenario['content'][:50]}...")
                stored_memories.append(scenario)
            else:
                print(f"  ❌ Failed to store: {scenario['content'][:50]}...")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print(f"\n📊 Storage Summary: {len(stored_memories)}/{len(test_scenarios)} memories stored")
    return stored_memories

async def test_memory_retrieval_comprehensive(stored_memories):
    """Test comprehensive memory retrieval scenarios"""
    print("\n🔍 Testing Comprehensive Memory Retrieval")
    print("=" * 60)
    
    # Configure for localhost access
    os.environ['MEMORY_API_URL'] = 'http://localhost:5001'
    
    memory_service = get_memory_service()
    user_id = "4b00c25b-e55e-4931-a29e-07fc94deebfc"
    
    # Test queries
    test_queries = [
        {
            "name": "Programming Language Query",
            "query": "What programming language do you prefer?",
            "expected_keywords": ["Python", "data analysis", "machine learning"]
        },
        {
            "name": "Web Framework Query", 
            "query": "Which web framework do you like?",
            "expected_keywords": ["FastAPI", "Flask", "REST API"]
        },
        {
            "name": "Coding Style Query",
            "query": "What are your coding preferences?",
            "expected_keywords": ["async/await", "type hints", "TDD"]
        },
        {
            "name": "Development Workflow Query",
            "query": "How do you approach development?",
            "expected_keywords": ["tests", "TDD", "features"]
        },
        {
            "name": "General Programming Query",
            "query": "Tell me about your programming style",
            "expected_keywords": ["Python", "async", "type hints", "tests"]
        }
    ]
    
    retrieval_results = []
    
    for query_test in test_queries:
        print(f"\n🔍 Testing {query_test['name']}...")
        try:
            memories = await memory_service.get_memories(
                user_id=user_id,
                query=query_test["query"],
                limit=5
            )
            
            print(f"  📊 Found {len(memories)} memories")
            
            if memories:
                for i, memory in enumerate(memories[:3]):  # Show top 3
                    print(f"    {i+1}. {memory.content[:60]}...")
                    if hasattr(memory, 'distance') and memory.distance:
                        print(f"       Distance: {memory.distance:.3f}")
                    if hasattr(memory, 'metadata') and memory.metadata:
                        print(f"       Source: {memory.metadata.source}")
                        print(f"       Explicit: {memory.metadata.explicit}")
                
                # Check for expected keywords
                all_content = " ".join([m.content for m in memories])
                found_keywords = [kw for kw in query_test["expected_keywords"] if kw.lower() in all_content.lower()]
                print(f"  🎯 Found keywords: {found_keywords}")
                
                retrieval_results.append({
                    "query": query_test["name"],
                    "memories_found": len(memories),
                    "keywords_found": found_keywords,
                    "success": len(memories) > 0
                })
            else:
                print("  ❌ No memories found")
                retrieval_results.append({
                    "query": query_test["name"],
                    "memories_found": 0,
                    "keywords_found": [],
                    "success": False
                })
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            retrieval_results.append({
                "query": query_test["name"],
                "memories_found": 0,
                "keywords_found": [],
                "success": False,
                "error": str(e)
            })
    
    return retrieval_results

async def test_memory_endpoints_direct():
    """Test memory endpoints directly via HTTP"""
    print("\n🔗 Testing Memory Endpoints Directly")
    print("=" * 60)
    
    user_id = "4b00c25b-e55e-4931-a29e-07fc94deebfc"
    
    # Test regular store endpoint
    print("📝 Testing /api/memory/store...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                "http://localhost:5001/api/memory/store",
                json={
                    "user_id": user_id,
                    "content": "I enjoy working with Docker containers for deployment",
                    "context": "DevOps preferences",
                    "importance": 0.8,
                    "source": "direct_test"
                }
            )
            print(f"  Status: {response.status_code}")
            result = response.json()
            print(f"  Success: {result.get('success', False)}")
            print(f"  Memory ID: {result.get('memory_id', 'N/A')}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    # Test explicit store endpoint
    print("\n📝 Testing /api/memory/store_explicit...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                "http://localhost:5001/api/memory/store_explicit",
                json={
                    "user_id": user_id,
                    "content": "Remember: I always use environment variables for configuration",
                    "context": "Explicit configuration instruction",
                    "importance": 0.9,
                    "forced": True,
                    "source": "direct_test"
                }
            )
            print(f"  Status: {response.status_code}")
            result = response.json()
            print(f"  Success: {result.get('success', False)}")
            print(f"  Memory ID: {result.get('memory_id', 'N/A')}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    # Test retrieve endpoint
    print("\n🔍 Testing /api/memory/retrieve...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                "http://localhost:5001/api/memory/retrieve",
                json={
                    "user_id": user_id,
                    "query": "Docker containers deployment",
                    "limit": 5
                }
            )
            print(f"  Status: {response.status_code}")
            result = response.json()
            print(f"  Memories found: {result.get('count', 0)}")
            
            memories = result.get('memories', [])
            for i, memory in enumerate(memories[:3]):
                print(f"    {i+1}. {memory.get('content', '')[:60]}...")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")

async def test_provider_comparison():
    """Test different memory providers"""
    print("\n🔄 Testing Memory Provider Comparison")
    print("=" * 60)
    
    # Configure for localhost access
    os.environ['MEMORY_API_URL'] = 'http://localhost:5001'
    os.environ['CHROMA_HOST'] = 'localhost'
    os.environ['CHROMA_PORT'] = '8000'
    os.environ['REDIS_HOST'] = 'localhost'
    os.environ['REDIS_PORT'] = '6379'
    os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'
    
    user_id = "4b00c25b-e55e-4931-a29e-07fc94deebfc"
    
    providers = {
        "API": APIMemoryProvider(),
        "Database": DatabaseMemoryProvider(),
        "Pipeline": PipelineMemoryProvider()
    }
    
    for name, provider in providers.items():
        print(f"\n🔍 Testing {name} Provider...")
        try:
            # Test health
            health = await provider.health_check()
            print(f"  Health: {'✅ OK' if health else '❌ Failed'}")
            
            if health:
                # Test retrieval
                from services.memory_service import MemoryQuery
                query = MemoryQuery(user_id=user_id, query="Python programming", limit=3)
                memories = await provider.get_memories(query)
                print(f"  Memories found: {len(memories)}")
                
                # Test stats
                stats = await provider.get_stats(user_id)
                print(f"  Total memories: {stats.total_memories}")
                
        except Exception as e:
            print(f"  ❌ Error testing {name} provider: {str(e)}")

async def main():
    """Main comprehensive test function"""
    print("🚀 Comprehensive Memory System Test")
    print("Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("Windows Firewall: Disabled")
    print("=" * 60)
    
    try:
        # Test network connectivity
        await test_network_connectivity()
        
        # Test memory storage
        stored_memories = await test_memory_storage_comprehensive()
        
        # Test memory retrieval
        retrieval_results = await test_memory_retrieval_comprehensive(stored_memories)
        
        # Test endpoints directly
        await test_memory_endpoints_direct()
        
        # Test provider comparison
        await test_provider_comparison()
        
        # Summary
        print("\n📊 Test Summary")
        print("=" * 60)
        print(f"Memories stored: {len(stored_memories)}")
        
        successful_retrievals = sum(1 for r in retrieval_results if r['success'])
        print(f"Successful retrievals: {successful_retrievals}/{len(retrieval_results)}")
        
        print("\n✅ Comprehensive Memory System Test Completed")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
