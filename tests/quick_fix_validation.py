#!/usr/bin/env python3
"""
Quick Fix Test - Document Upload and RAG Validation
Tests the document upload with proper parameters and validates RAG functionality.
"""

import sys
import os
import tempfile
import requests
import time

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_document_upload_rag_fixed():
    """Test document upload and RAG with proper parameters."""
    
    base_url = "http://localhost:8001"
    api_key = "f2b985dd-219f-45b1-a90e-170962cc7082"
    
    print("🧪 QUICK FIX TEST - Document Upload and RAG")
    print("="*50)
    
    # Create test document
    test_content = """
    TechCorp Company Information
    
    Founded: 2020
    Location: San Francisco, California
    CEO: Jane Smith
    Employees: 150
    Industry: AI Technology
    
    Products:
    - AI Chatbot Platform
    - Machine Learning Consulting
    - Data Analytics Tools
    
    Recent Achievements:
    - Won Best AI Startup Award 2023
    - Raised $10M Series A funding
    - Expanded to 3 countries
    """
    
    # Test 1: Document Upload with proper parameters
    print("\n📄 Step 1: Testing document upload with user_id...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name
    
    try:
        with open(temp_file_path, 'rb') as file:
            # Include user_id as form data
            files = {'file': ('company_info.txt', file, 'text/plain')}
            data = {'user_id': 'test_user_123'}  # Add required user_id
            headers = {"Authorization": f"Bearer {api_key}"}
            
            upload_response = requests.post(
                f"{base_url}/upload/document",
                files=files,
                data=data,  # Form data with user_id
                headers=headers,
                timeout=30
            )
            
            print(f"   Upload Status: {upload_response.status_code}")
            print(f"   Response: {upload_response.text[:200]}...")
            
            upload_success = upload_response.status_code == 200
            
            if upload_success:
                print("   ✅ Document upload successful!")
                
                # Wait for processing
                print("   ⏳ Waiting for document processing...")
                time.sleep(5)
                
                # Test 2: RAG Query
                print("\n🔍 Step 2: Testing RAG query...")
                
                rag_query = "When was TechCorp founded and who is the CEO?"
                chat_payload = {
                    "messages": [{"role": "user", "content": rag_query}],
                    "model": "gpt-4o-mini",
                    "max_tokens": 200
                }
                
                rag_response = requests.post(
                    f"{base_url}/v1/chat/completions", 
                    json=chat_payload, 
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    timeout=30
                )
                
                print(f"   RAG Status: {rag_response.status_code}")
                
                if rag_response.status_code == 200:
                    rag_data = rag_response.json()
                    rag_content = rag_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    print(f"   RAG Response: {rag_content}")
                    
                    # Check if response contains information from document
                    contains_year = "2020" in rag_content
                    contains_ceo = "Jane Smith" in rag_content or "Jane" in rag_content
                    
                    print(f"   Contains founding year (2020): {'✅' if contains_year else '❌'}")
                    print(f"   Contains CEO name (Jane Smith): {'✅' if contains_ceo else '❌'}")
                    
                    if contains_year or contains_ceo:
                        print("   ✅ RAG functionality working - document information retrieved!")
                        return True
                    else:
                        print("   ⚠️ RAG response doesn't contain expected document information")
                        print("   This might indicate the document wasn't properly indexed or retrieved")
                        return False
                else:
                    print(f"   ❌ RAG query failed with status {rag_response.status_code}")
                    return False
            else:
                print(f"   ❌ Document upload failed with status {upload_response.status_code}")
                print(f"   Response: {upload_response.text}")
                return False
                
    except Exception as e:
        print(f"   ❌ Exception during test: {e}")
        return False
    finally:
        # Clean up temp file
        os.unlink(temp_file_path)

def test_api_authentication():
    """Test API authentication properly."""
    
    base_url = "http://localhost:8001"
    
    print("\n🔐 QUICK FIX TEST - API Authentication")
    print("="*40)
    
    # Test 1: No API key
    print("\n🧪 Test 1: Request without API key...")
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "test"}]},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(f"   Expected: 401 (Unauthorized)")
        print(f"   Result: {'✅ Correct' if response.status_code == 401 else '❌ Incorrect - No auth enforcement'}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 2: Invalid API key
    print("\n🧪 Test 2: Request with invalid API key...")
    try:
        headers = {"Authorization": "Bearer invalid_key_12345"}
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "test"}]},
            headers=headers,
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(f"   Expected: 401 (Unauthorized)")
        print(f"   Result: {'✅ Correct' if response.status_code == 401 else '❌ Incorrect - Invalid key accepted'}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 3: Valid API key
    print("\n🧪 Test 3: Request with valid API key...")
    try:
        headers = {"Authorization": "Bearer f2b985dd-219f-45b1-a90e-170962cc7082"}
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "Hello"}]},
            headers=headers,
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(f"   Expected: 200 (Success)")
        print(f"   Result: {'✅ Correct' if response.status_code == 200 else '❌ Incorrect - Valid key rejected'}")
    except Exception as e:
        print(f"   Exception: {e}")

def test_cache_performance():
    """Test cache performance with identical requests."""
    
    base_url = "http://localhost:8001"
    api_key = "f2b985dd-219f-45b1-a90e-170962cc7082"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    print("\n💾 QUICK FIX TEST - Cache Performance")
    print("="*35)
    
    # Use a deterministic query for consistent caching
    test_query = "What is 2 + 2?"
    chat_payload = {
        "messages": [{"role": "user", "content": test_query}],
        "model": "gpt-4o-mini",
        "max_tokens": 50,
        "temperature": 0  # Zero temperature for deterministic response
    }
    
    print(f"\n🧪 Testing cache with query: '{test_query}'")
    
    # First request (should miss cache)
    print("\n📤 First request (cache miss expected)...")
    start_time = time.time()
    response1 = requests.post(
        f"{base_url}/v1/chat/completions", 
        json=chat_payload, 
        headers=headers,
        timeout=30
    )
    time1 = time.time() - start_time
    
    if response1.status_code == 200:
        print(f"   ✅ First request successful ({time1:.3f}s)")
        
        # Small delay to ensure any async processing completes
        time.sleep(1)
        
        # Second request (should hit cache)
        print("\n📥 Second request (cache hit expected)...")
        start_time = time.time()
        response2 = requests.post(
            f"{base_url}/v1/chat/completions", 
            json=chat_payload, 
            headers=headers,
            timeout=30
        )
        time2 = time.time() - start_time
        
        if response2.status_code == 200:
            print(f"   ✅ Second request successful ({time2:.3f}s)")
            
            # Check for cache hit (significant speed improvement)
            speedup = time1 / time2 if time2 > 0 else 1
            is_cache_hit = time2 < time1 * 0.5  # 50% faster suggests cache hit
            
            print(f"\n📊 Cache Performance Analysis:")
            print(f"   First request:  {time1:.3f}s")
            print(f"   Second request: {time2:.3f}s")
            print(f"   Speedup:        {speedup:.1f}x")
            print(f"   Cache hit:      {'✅ Likely' if is_cache_hit else '❌ No clear evidence'}")
            
            return is_cache_hit
        else:
            print(f"   ❌ Second request failed: {response2.status_code}")
            return False
    else:
        print(f"   ❌ First request failed: {response1.status_code}")
        return False

def main():
    """Run the quick fix tests."""
    
    print("🚀 QUICK FIX VALIDATION TESTS")
    print("Testing specific issues identified in comprehensive testing")
    print("="*60)
    
    results = {}
    
    # Test 1: Document Upload and RAG (with proper user_id)
    results["Document Upload & RAG"] = test_document_upload_rag_fixed()
    
    # Test 2: API Authentication 
    test_api_authentication()  # This is more of a diagnostic test
    
    # Test 3: Cache Performance
    results["Cache Performance"] = test_cache_performance()
    
    # Summary
    print("\n" + "="*60)
    print("📊 QUICK FIX TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All quick fix tests passed!")
    else:
        print("⚠️ Some issues remain - see detailed output above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
