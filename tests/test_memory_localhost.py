#!/usr/bin/env python3
"""
Memory System Test - Localhost Version
Test memory functionality using localhost ports (Windows host compatible)
"""

import asyncio
import json
import sys
import os
from datetime import datetime
import httpx

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_memory_endpoints_directly():
    """Test memory endpoints directly via localhost"""
    print("🧠 Testing Memory Endpoints via Localhost")
    print("=" * 60)
    
    user_id = "4b00c25b-e55e-4931-a29e-07fc94deebfc"
    
    # Test regular memory storage
    print("📝 Testing /api/memory/store (Regular Memory)...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:5001/api/memory/store",
                json={
                    "user_id": user_id,
                    "content": "I prefer Python for data analysis projects",
                    "context": "Programming preferences",
                    "importance": 0.8,
                    "source": "test_regular"
                }
            )
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.json()}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    # Test explicit memory storage
    print("\n📝 Testing /api/memory/store_explicit (Explicit Memory)...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:5001/api/memory/store_explicit",
                json={
                    "user_id": user_id,
                    "content": "Remember: I always use async/await patterns",
                    "context": "Explicit memory command",
                    "importance": 0.9,
                    "forced": True,
                    "source": "test_explicit"
                }
            )
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.json()}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    # Test memory retrieval
    print("\n🔍 Testing /api/memory/retrieve...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:5001/api/memory/retrieve",
                json={
                    "user_id": user_id,
                    "query": "Python programming",
                    "limit": 5
                }
            )
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.json()}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")

async def test_memory_service_with_localhost():
    """Test memory service configured for localhost"""
    print("\n🔧 Testing Memory Service with Localhost Configuration")
    print("=" * 60)
    
    # Override the service URLs to use localhost
    os.environ['MEMORY_API_URL'] = 'http://localhost:5001'
    os.environ['CHROMA_HOST'] = 'localhost'
    os.environ['CHROMA_PORT'] = '8000'
    os.environ['REDIS_HOST'] = 'localhost'
    os.environ['REDIS_PORT'] = '6379'
    os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'
    
    from services.memory_service import get_memory_service
    
    memory_service = get_memory_service()
    user_id = "4b00c25b-e55e-4931-a29e-07fc94deebfc"
    
    # Test regular memory storage
    print("📝 Testing Regular Memory Storage...")
    try:
        success = await memory_service.store_memory(
            user_id=user_id,
            content="I prefer working with FastAPI for web APIs",
            context="Web development preferences",
            importance=0.7,
            explicit=False,
            source="localhost_test"
        )
        if success:
            print("  ✅ Regular memory stored successfully")
        else:
            print("  ❌ Regular memory storage failed")
    except Exception as e:
        print(f"  ❌ Error storing regular memory: {str(e)}")
    
    # Test explicit memory storage  
    print("\n📝 Testing Explicit Memory Storage...")
    try:
        success = await memory_service.store_memory(
            user_id=user_id,
            content="Remember: I always write comprehensive tests",
            context="Explicit memory command",
            importance=0.9,
            explicit=True,
            source="localhost_test"
        )
        if success:
            print("  ✅ Explicit memory stored successfully")
        else:
            print("  ❌ Explicit memory storage failed")
    except Exception as e:
        print(f"  ❌ Error storing explicit memory: {str(e)}")
    
    # Test memory retrieval
    print("\n🔍 Testing Memory Retrieval...")
    try:
        memories = await memory_service.get_memories(
            user_id=user_id,
            query="FastAPI web development",
            limit=5
        )
        print(f"  📊 Retrieved {len(memories)} memories")
        for i, memory in enumerate(memories[:3]):
            print(f"    {i+1}. {memory.content[:60]}...")
    except Exception as e:
        print(f"  ❌ Error retrieving memories: {str(e)}")

async def test_container_connectivity():
    """Test if containers can communicate internally"""
    print("\n🔗 Testing Container-to-Container Connectivity")
    print("=" * 60)
    
    print("📝 Testing Redis connectivity from backend-main...")
    try:
        result = await asyncio.create_subprocess_exec(
            "docker", "exec", "-it", "backend-main", "python", "-c", 
            "import redis; r = redis.Redis(host='backend-redis', port=6379); print('Redis ping:', r.ping())",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        print(f"  Redis test: {stdout.decode()}")
        if stderr:
            print(f"  Error: {stderr.decode()}")
    except Exception as e:
        print(f"  ❌ Redis test error: {str(e)}")
    
    print("\n📝 Testing Ollama connectivity from backend-main...")
    try:
        result = await asyncio.create_subprocess_exec(
            "docker", "exec", "-it", "backend-main", "python", "-c", 
            "import requests; r = requests.get('http://ollama:11434'); print('Ollama status:', r.status_code)",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        print(f"  Ollama test: {stdout.decode()}")
        if stderr:
            print(f"  Error: {stderr.decode()}")
    except Exception as e:
        print(f"  ❌ Ollama test error: {str(e)}")

async def main():
    """Main test function"""
    print("🚀 Memory System Localhost Test")
    print("Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    try:
        # Test endpoints directly
        await test_memory_endpoints_directly()
        
        # Test memory service with localhost
        await test_memory_service_with_localhost()
        
        # Test container connectivity
        await test_container_connectivity()
        
        print("\n✅ Memory System Localhost Test Completed")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
