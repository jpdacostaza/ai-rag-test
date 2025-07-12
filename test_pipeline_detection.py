#!/usr/bin/env python3
"""
Test Pipeline Detection in OpenWebUI
===================================

This script verifies that our Enhanced Memory Pipeline is properly detected
and available in the OpenWebUI system.
"""

import asyncio
import httpx

async def test_pipeline_detection():
    """Test if the Enhanced Memory Pipeline is properly detected."""
    
    print("Testing Pipeline Detection...")
    print("=" * 50)
    
    # Test connection to Pipelines service
    try:
        async with httpx.AsyncClient() as client:
            # Test basic connectivity
            response = await client.get("http://localhost:9099/")
            print(f"✓ Pipelines service connection: {response.status_code}")
            
            # Test authenticated pipeline listing
            headers = {"Authorization": "Bearer 0p3n-w3bu!"}
            response = await client.get("http://localhost:9099/pipelines", headers=headers)
            print(f"✓ Pipelines API authentication: {response.status_code}")
            
            if response.status_code == 200:
                pipelines = response.json()
                print(f"✓ Available pipelines: {len(pipelines['data'])}")
                
                for pipeline in pipelines['data']:
                    print(f"  - {pipeline['name']} (ID: {pipeline['id']}, Type: {pipeline['type']})")
                    
                # Check if our specific pipeline is available
                our_pipeline = next((p for p in pipelines['data'] if p['id'] == 'enhanced_memory_pipeline'), None)
                if our_pipeline:
                    print(f"✅ Enhanced Memory Pipeline detected successfully!")
                    print(f"   - Name: {our_pipeline['name']}")
                    print(f"   - Type: {our_pipeline['type']}")
                    print(f"   - Has Valves: {our_pipeline['valves']}")
                else:
                    print("❌ Enhanced Memory Pipeline NOT found in pipeline list")
            
    except Exception as e:
        print(f"❌ Pipeline service test failed: {e}")
    
    # Test OpenWebUI API connection
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8080/health")
            if response.status_code == 200:
                print(f"✓ OpenWebUI service connection: {response.status_code}")
            else:
                print(f"⚠ OpenWebUI health check returned: {response.status_code}")
                
    except Exception as e:
        print(f"❌ OpenWebUI service test failed: {e}")
    
    print("=" * 50)
    print("Test completed. If Enhanced Memory Pipeline is detected,")
    print("the 'Pipelines Not Detected' message should be resolved.")

if __name__ == "__main__":
    asyncio.run(test_pipeline_detection())
