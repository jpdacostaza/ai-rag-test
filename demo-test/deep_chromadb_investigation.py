#!/usr/bin/env python3
"""
Deep dive into ChromaDB storage and search mechanics
"""

import requests
import time
import json

BASE_URL = "http://localhost:8001"
API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"
CHROMA_URL = "http://localhost:8002"

def investigate_chromadb_storage():
    print("🔍 Deep Investigation: ChromaDB Storage & Search")
    
    # Test with a very specific user_id and content
    user_id = "investigation_user_123"
    test_content = "Machine learning and artificial intelligence research with Python programming language."
    filename = "investigation_doc.txt"
    
    print(f"👤 Using User ID: {user_id}")
    print(f"📄 Document content: {test_content}")
    
    # Step 1: Upload document
    print("\n📤 Step 1: Uploading document...")
    files = {'file': (filename, test_content, 'text/plain')}
    data = {'user_id': user_id}
    
    upload_response = requests.post(
        f"{BASE_URL}/upload/document",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=20
    )
    
    if upload_response.status_code != 200:
        print(f"❌ Upload failed: {upload_response.status_code}")
        print(f"Response: {upload_response.text}")
        return
    
    upload_result = upload_response.json()
    print(f"✅ Upload successful: {upload_result}")
    
    # Wait for processing
    print("\n⏳ Waiting 5 seconds for document processing...")
    time.sleep(5)
    
    # Step 2: Try direct ChromaDB access
    print("\n🔍 Step 2: Direct ChromaDB investigation...")
    try:
        # Check ChromaDB health
        health_response = requests.get(f"{CHROMA_URL}/api/v1/heartbeat", timeout=5)
        print(f"ChromaDB health: {health_response.status_code}")
        
        # Try to get collections
        collections_response = requests.get(f"{CHROMA_URL}/api/v1/collections", timeout=5)
        if collections_response.status_code == 200:
            collections = collections_response.json()
            print(f"Collections: {json.dumps(collections, indent=2)}")
        else:
            print(f"Failed to get collections: {collections_response.status_code}")
            
    except Exception as e:
        print(f"ChromaDB direct access failed: {e}")
    
    # Step 3: Test various search queries
    print("\n🔍 Step 3: Testing various search queries...")
    
    test_queries = [
        "machine learning",           # Should match
        "artificial intelligence",    # Should match  
        "Python programming",         # Should match
        "research",                   # Should match
        "completely unrelated topic", # Should not match
        test_content[:50],            # Exact content match
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Query {i}: '{query}'")
        
        search_payload = {
            'query': query,
            'user_id': user_id,  # Use exact same user_id
            'limit': 5
        }
        
        try:
            search_response = requests.post(
                f"{BASE_URL}/upload/search",
                data=search_payload,
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=15
            )
            
            if search_response.status_code == 200:
                search_results = search_response.json()
                print(f"📊 Results: {search_results}")
                
                if search_results.get('results_count', 0) > 0:
                    print("🎯 SUCCESS: Found results!")
                    for j, result in enumerate(search_results.get('results', []), 1):
                        print(f"   Result {j}: {result}")
                else:
                    print("⚠️ No results found")
                    
            else:
                print(f"❌ Search failed: {search_response.status_code}")
                print(f"Response: {search_response.text}")
                
        except Exception as e:
            print(f"❌ Search error: {e}")
    
    # Step 4: Check backend logs for our specific operations
    print("\n📋 Step 4: Checking backend logs...")
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "logs", "backend-llm-backend", "--tail", "50"],
            capture_output=True,
            text=True,
            timeout=10,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode == 0:
            logs = result.stdout
            
            # Look for our specific user_id in logs
            lines = logs.split('\n')
            relevant_lines = [line for line in lines if user_id in line or 'MEMORY' in line or 'CHROMADB' in line]
            
            if relevant_lines:
                print("📋 Relevant log lines:")
                for line in relevant_lines[-10:]:  # Last 10 relevant lines
                    print(f"   {line}")
            else:
                print("📋 No specific logs found for our operations")
                
        else:
            print(f"❌ Failed to get logs: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error getting logs: {e}")

if __name__ == "__main__":
    investigate_chromadb_storage()
