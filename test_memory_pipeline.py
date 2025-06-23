"""
Simple Memory Pipeline Test Script
==================================

This script tests the advanced memory pipeline endpoints to ensure they work correctly.
Run this script to verify the pipeline integration is working.
"""

import asyncio
import httpx
import json
from datetime import datetime

class PipelineTestClient:
    def __init__(self, backend_url="http://localhost:8080", api_key="development"):
        self.backend_url = backend_url.rstrip("/")
        self.api_key = api_key
        self.client = None
        
    async def get_client(self):
        if not self.client:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client
    
    async def test_pipeline_status(self):
        """Test the pipeline status endpoint"""
        print("🔍 Testing pipeline status endpoint...")
        try:
            client = await self.get_client()
            response = await client.get(f"{self.backend_url}/api/pipeline/status")
            response.raise_for_status()
            
            status = response.json()
            print("✅ Pipeline status endpoint working!")
            print(f"   Status: {status.get('status', 'unknown')}")
            print(f"   Services: {status.get('services', {})}")
            return True
            
        except Exception as e:
            print(f"❌ Pipeline status test failed: {e}")
            return False
    
    async def test_memory_retrieval(self, user_id="test_user", query="test query"):
        """Test memory retrieval endpoint"""
        print(f"🧠 Testing memory retrieval for user '{user_id}'...")
        try:
            client = await self.get_client()
            headers = {"Content-Type": "application/json"}
            data = {
                "user_id": user_id,
                "query": query,
                "limit": 3,
                "threshold": 0.7
            }
            
            response = await client.post(
                f"{self.backend_url}/api/memory/retrieve",
                json=data,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            print("✅ Memory retrieval endpoint working!")
            print(f"   Retrieved {result.get('count', 0)} memories")
            print(f"   User ID: {result.get('user_id', 'unknown')}")
            return True
            
        except Exception as e:
            print(f"❌ Memory retrieval test failed: {e}")
            return False
    
    async def test_learning_storage(self, user_id="test_user"):
        """Test learning interaction storage"""
        print(f"📚 Testing learning storage for user '{user_id}'...")
        try:
            client = await self.get_client()
            headers = {"Content-Type": "application/json"}
            data = {
                "user_id": user_id,
                "conversation_id": f"test_conv_{int(datetime.now().timestamp())}",
                "user_message": "This is a test user message for the pipeline",
                "assistant_response": "This is a test assistant response for the pipeline",
                "response_time": 1.5,
                "tools_used": ["test_tool"],
                "source": "pipeline_test"
            }
            
            response = await client.post(
                f"{self.backend_url}/api/learning/process_interaction",
                json=data,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            print("✅ Learning storage endpoint working!")
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   User ID: {result.get('user_id', 'unknown')}")
            return True
            
        except Exception as e:
            print(f"❌ Learning storage test failed: {e}")
            return False
    
    async def run_full_test(self):
        """Run all pipeline tests"""
        print("🚀 Starting Advanced Memory Pipeline Tests\n")
        
        tests = [
            ("Pipeline Status", self.test_pipeline_status()),
            ("Memory Retrieval", self.test_memory_retrieval()),
            ("Learning Storage", self.test_learning_storage())
        ]
        
        results = []
        for test_name, test_coro in tests:
            print(f"\n--- {test_name} Test ---")
            result = await test_coro
            results.append((test_name, result))
            print()
        
        # Summary
        print("=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<20} {status}")
            if result:
                passed += 1
        
        print(f"\nTests passed: {passed}/{len(results)}")
        
        if passed == len(results):
            print("🎉 All tests passed! The Advanced Memory Pipeline is ready to use.")
        else:
            print("⚠️  Some tests failed. Check the backend configuration and try again.")
        
        return passed == len(results)
    
    async def cleanup(self):
        """Clean up resources"""
        if self.client:
            await self.client.aclose()

async def main():
    """Main test function"""    # You can modify these settings to match your backend
    BACKEND_URL = "http://localhost:8001"  # Change this to your backend URL
    API_KEY = "development"  # Change this to your API key
    
    print("Advanced Memory Pipeline Test Suite")
    print("====================================")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Key: {API_KEY}")
    print()
    
    client = PipelineTestClient(BACKEND_URL, API_KEY)
    
    try:
        success = await client.run_full_test()
        return success
    finally:
        await client.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
