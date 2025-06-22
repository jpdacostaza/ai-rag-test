#!/usr/bin/env python3

import requests
import time
import tempfile
import os

def test_complete_workflow():
    """Test the complete workflow: upload document -> search for it"""
    print("🧪 Testing complete document upload and search workflow...")
    
    # Step 1: Upload a test document
    print("\n📤 Step 1: Uploading test document...")
    
    # Create a temporary test file
    test_content = """
    This is a test document for semantic search.
    It contains information about machine learning and artificial intelligence.
    The document discusses neural networks, deep learning, and natural language processing.
    We use this document to test the RAG (Retrieval-Augmented Generation) system.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name
    
    try:
        upload_url = "http://localhost:8001/upload"
        with open(temp_file_path, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            data = {'user_id': 'test-workflow-user'}
            
            upload_response = requests.post(upload_url, files=files, data=data, timeout=30)
            print(f"Upload status: {upload_response.status_code}")
            if upload_response.status_code == 200:
                upload_result = upload_response.json()
                print(f"Upload successful: {upload_result}")
                print(f"Document ID: {upload_result.get('document_id', 'N/A')}")
                print(f"Chunks created: {upload_result.get('chunks_created', 'N/A')}")
            else:
                print(f"Upload failed: {upload_response.text}")
                return False
                
    except Exception as e:
        print(f"Upload error: {e}")
        return False
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)
    
    # Wait a moment for processing
    print("\n⏳ Waiting for document processing...")
    time.sleep(3)
    
    # Step 2: Search for content from the uploaded document
    print("\n🔍 Step 2: Searching for content...")
    
    search_queries = [
        "machine learning",
        "artificial intelligence", 
        "neural networks",
        "RAG system",
        "test document"
    ]
    
    search_url = "http://localhost:8001/upload/search"
    
    for query in search_queries:
        print(f"\n🔍 Testing query: '{query}'")
        try:
            search_data = {
                "query": query,
                "user_id": "test-workflow-user",
                "limit": 5
            }
            
            search_response = requests.post(search_url, data=search_data, timeout=30)
            print(f"Search status: {search_response.status_code}")
            
            if search_response.status_code == 200:
                search_result = search_response.json()
                results_count = search_result.get('results_count', 0)
                print(f"Results found: {results_count}")
                
                if results_count > 0:
                    print("✅ SUCCESS: Found results!")
                    for i, result in enumerate(search_result.get('results', [])[:2]):
                        print(f"  Result {i+1}: {result.get('content', '')[:100]}...")
                        print(f"    Similarity: {result.get('similarity', 'N/A')}")
                    return True
                else:
                    print("❌ No results found")
            else:
                print(f"Search failed: {search_response.text}")
                
        except Exception as e:
            print(f"Search error: {e}")
    
    return False

def main():
    print("🔍 Complete workflow test to identify semantic search issues...")
    print("=" * 70)
    
    # Check backend health first
    try:
        health_response = requests.get("http://localhost:8001/health", timeout=10)
        if health_response.status_code == 200:
            health = health_response.json()
            print(f"✅ Backend health: {health.get('summary', 'N/A')}")
        else:
            print(f"❌ Backend health check failed: {health_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return
    
    # Run the complete workflow test
    success = test_complete_workflow()
    
    print("\n" + "=" * 70)
    print("🔍 Workflow Test Result:")
    if success:
        print("✅ SUCCESS: Documents can be uploaded and searched successfully!")
        print("   The semantic search system is working correctly.")
    else:
        print("❌ FAILURE: Either upload failed or search returned no results.")
        print("   Check backend logs for detailed error information.")
        print("   The NumPy array error may be preventing search results.")

if __name__ == "__main__":
    main()
