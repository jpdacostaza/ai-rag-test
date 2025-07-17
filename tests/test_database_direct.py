#!/usr/bin/env python3
"""
Direct Database Memory Test - Testing ChromaDB connection and memory operations
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_database_memory_direct():
    """Test database memory operations directly"""
    print("🔍 Testing Database Memory Operations Directly")
    print("=" * 50)
    
    # Test database manager import
    try:
        from services.database_manager import db_manager
        print("✅ Database manager imported successfully")
        
        # Test database manager initialization
        if not db_manager.is_initialized():
            print("📝 Initializing database manager...")
            await db_manager.ensure_initialized()
        
        if db_manager.is_initialized():
            print("✅ Database manager initialized successfully")
        else:
            print("❌ Database manager failed to initialize")
            return
            
    except Exception as e:
        print(f"❌ Database manager import failed: {str(e)}")
        return
    
    # Test vector storage
    print("\n📝 Testing Vector Storage...")
    try:
        from services.database_manager import store_vector_data
        
        test_data = {
            "user_id": "4b00c25b-e55e-4931-a29e-07fc94deebfc",
            "timestamp": datetime.now().isoformat(),
            "source": "direct_test",
            "importance": 0.8,
            "memory_type": "test",
            "explicit": True
        }
        
        result = await store_vector_data(
            text="I enjoy working with Python and testing memory systems",
            metadata=test_data
        )
        
        if result:
            print("✅ Vector storage successful")
        else:
            print("❌ Vector storage failed")
            
    except Exception as e:
        print(f"❌ Vector storage error: {str(e)}")
    
    # Test memory retrieval
    print("\n🔍 Testing Memory Retrieval...")
    try:
        from services.database_manager import retrieve_user_memory
        
        memories = await retrieve_user_memory(
            user_id="4b00c25b-e55e-4931-a29e-07fc94deebfc",
            query="Python testing",
            n_results=5
        )
        
        print(f"📊 Retrieved {len(memories)} memories")
        for i, memory in enumerate(memories[:3]):
            print(f"  {i+1}. {memory.get('document', 'No content')[:50]}...")
            if 'distance' in memory:
                print(f"     Distance: {memory['distance']:.3f}")
        
    except Exception as e:
        print(f"❌ Memory retrieval error: {str(e)}")
    
    # Test ChromaDB connection directly
    print("\n🔗 Testing ChromaDB Connection...")
    try:
        chroma_client = db_manager.get_chroma_client()
        if chroma_client:
            print("✅ ChromaDB client available")
            
            # Test collection access
            collection = db_manager.get_collection()
            if collection:
                print("✅ Collection access successful")
                
                # Get collection info
                count = collection.count()
                print(f"📊 Collection has {count} items")
            else:
                print("❌ Collection access failed")
        else:
            print("❌ ChromaDB client unavailable")
            
    except Exception as e:
        print(f"❌ ChromaDB connection error: {str(e)}")

async def test_localhost_connectivity():
    """Test connectivity to services via localhost"""
    print("\n🌐 Testing Localhost Connectivity...")
    print("=" * 50)
    
    import httpx
    
    services = {
        "Memory API": "http://localhost:5001/health",
        "ChromaDB": "http://localhost:8000/api/v2/heartbeat",
        "Backend": "http://localhost:3000/health",
        "OpenWebUI": "http://localhost:8080/health",
        "Pipelines": "http://localhost:9099/health",
        "Ollama": "http://localhost:11434/api/tags"
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service, url in services.items():
            try:
                response = await client.get(url)
                status = "✅ OK" if response.status_code == 200 else f"⚠️ {response.status_code}"
                print(f"  {service}: {status}")
            except Exception as e:
                print(f"  {service}: ❌ Failed ({str(e)})")

async def main():
    """Main test function"""
    print("🚀 Direct Database Memory Test")
    print("Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 50)
    
    await test_localhost_connectivity()
    await test_database_memory_direct()
    
    print("\n✅ Direct Database Memory Test Completed")

if __name__ == "__main__":
    asyncio.run(main())
