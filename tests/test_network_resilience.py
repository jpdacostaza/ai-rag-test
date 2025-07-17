import asyncio
import requests
import json
from services.robust_memory_service import RobustMemoryService

async def test_network_resilience():
    """Test the network resilience of the memory system"""
    print("🔬 Testing Network Resilience for Memory System")
    print("=" * 60)
    
    # Test RobustMemoryService directly
    print("\n🧠 Testing RobustMemoryService Network Resilience...")
    
    try:
        memory_service = RobustMemoryService()
        
        # Test store with network resilience
        test_memory = {
            "user_id": "test_user_123",
            "content": "This is a test memory to verify network resilience",
            "explicit": False,
            "timestamp": "2025-07-17T19:35:00Z"
        }
        
        print(f"📝 Testing memory storage with network resilience...")
        result = await memory_service.store_memory(test_memory)
        print(f"  ✅ Storage result: {result}")
        
        # Test retrieve with network resilience
        print(f"🔍 Testing memory retrieval with network resilience...")
        memories = await memory_service.retrieve_memories("test_user_123", "test memory")
        print(f"  ✅ Retrieved {len(memories)} memories")
        
        # Test network configuration
        print(f"\n🌐 Testing network configuration...")
        print(f"  Redis hosts: ['backend-redis:6379', 'localhost:6379', '127.0.0.1:6379']")
        print(f"  ChromaDB hosts: ['chroma:8000', 'localhost:8000', '127.0.0.1:8000']")
        print(f"  Ollama hosts: ['ollama:11434', 'localhost:11434', '127.0.0.1:11434']")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test direct API endpoints with different hosts
    print(f"\n🔌 Testing API endpoints with fallback hosts...")
    
    test_endpoints = [
        "http://localhost:5001/health",
        "http://127.0.0.1:5001/health",
        "http://backend-memory-api:5001/health"
    ]
    
    for endpoint in test_endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {endpoint} - OK")
            else:
                print(f"  ⚠️ {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {endpoint} - Failed: {str(e)[:50]}...")
    
    # Test memory API with different connection strategies
    print(f"\n📋 Testing memory API with different connection strategies...")
    
    memory_test = {
        "user_id": "resilience_test_user",
        "content": "Testing network resilience for memory API",
        "explicit": False
    }
    
    api_hosts = [
        "http://localhost:5001",
        "http://127.0.0.1:5001",
        "http://backend-memory-api:5001"
    ]
    
    for host in api_hosts:
        try:
            # Test store
            store_url = f"{host}/api/memory/store"
            response = requests.post(store_url, json=memory_test, timeout=10)
            if response.status_code == 200:
                print(f"  ✅ Store via {host} - OK")
            else:
                print(f"  ⚠️ Store via {host} - Status: {response.status_code}")
            
            # Test retrieve
            retrieve_url = f"{host}/api/memory/retrieve"
            retrieve_params = {"user_id": "resilience_test_user", "query": "network resilience"}
            response = requests.get(retrieve_url, params=retrieve_params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Retrieve via {host} - Found {len(data.get('memories', []))} memories")
            else:
                print(f"  ⚠️ Retrieve via {host} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ {host} - Failed: {str(e)[:50]}...")
    
    print(f"\n🎯 Network Resilience Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_network_resilience())
