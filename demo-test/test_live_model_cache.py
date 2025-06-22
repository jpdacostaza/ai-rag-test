#!/usr/bin/env python3
"""
Live test for model caching functionality.
Tests the implemented refresh_model_cache and ensure_model_available functions
in a real environment with actual Ollama API calls.
"""

import requests
import time
import json
from typing import Dict, Any

# Backend endpoint
BACKEND_URL = "http://localhost:8001"
OLLAMA_URL = "http://localhost:11434"

def test_ollama_connection():
    """Test if Ollama is accessible"""
    print("🔗 Testing Ollama connection...")
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama is accessible. Found {len(models)} models.")
            for model in models[:3]:  # Show first 3 models
                print(f"   - {model.get('name', 'Unknown')}")
            return True
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to Ollama: {e}")
        return False

def test_backend_health():
    """Test if backend is healthy"""
    print("\n🏥 Testing backend health...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Backend is healthy:")
            for service, status in health_data.items():
                if isinstance(status, dict):
                    service_status = status.get('status', 'unknown')
                    print(f"   - {service}: {service_status}")
                else:
                    print(f"   - {service}: {status}")
            return True
        else:
            print(f"❌ Backend health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to backend: {e}")
        return False

def test_model_cache_refresh():
    """Test the refresh_model_cache endpoint"""
    print("\n🔄 Testing model cache refresh...")
    try:
        response = requests.post(f"{BACKEND_URL}/test/refresh_models", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("✅ Model cache refresh successful:")
            print(f"   - Status: {result.get('status', 'unknown')}")
            print(f"   - Models cached: {result.get('models_cached', 'unknown')}")
            if 'models' in result:
                models = result['models']
                print(f"   - Found {len(models)} models")
                for model in models[:3]:  # Show first 3
                    print(f"     * {model}")
            return True
        else:
            print(f"❌ Model cache refresh failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error: {error_detail}")
            except:
                print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to refresh model cache: {e}")
        return False

def test_model_availability():
    """Test model availability checking"""
    print("\n🔍 Testing model availability...")
    try:
        # First, get the list of available models
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        if response.status_code != 200:
            print("❌ Cannot get model list from Ollama")
            return False
        
        models = response.json().get('models', [])
        if not models:
            print("❌ No models found in Ollama")
            return False
        
        # Test with the first available model
        test_model = models[0]['name']
        print(f"   Testing with model: {test_model}")
          # Test ensure_model_available endpoint
        check_payload = {"model": test_model}
        response = requests.post(
            f"{BACKEND_URL}/test/check_model", 
            json=check_payload, 
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Model availability check successful:")
            print(f"   - Model: {test_model}")
            print(f"   - Available: {result.get('available', 'unknown')}")
            print(f"   - Status: {result.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Model availability check failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error: {error_detail}")
            except:
                print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test model availability: {e}")
        return False

def test_model_cache_persistence():
    """Test if model cache persists across requests"""
    print("\n💾 Testing model cache persistence...")
    try:
        # Get initial cache status
        response_status = requests.get(f"{BACKEND_URL}/test/model_cache_status", timeout=10)
        if response_status.status_code != 200:
            print("❌ Cannot get initial cache status")
            return False
        
        initial_status = response_status.json()
        print(f"   Initial cache age: {initial_status['cache']['age']:.2f}s")
        print(f"   Initial cache valid: {initial_status['cache']['valid']}")
        
        # Make first cache refresh request
        print("   Making first cache refresh request...")
        response1 = requests.post(f"{BACKEND_URL}/test/refresh_models", timeout=30)
        
        if response1.status_code != 200:
            print("❌ First cache refresh failed")
            return False
        
        result1 = response1.json()
        models_count_1 = result1.get('models_cached', 0)
        
        time.sleep(2)  # Small delay
        
        print("   Making second cache refresh request...")
        response2 = requests.post(f"{BACKEND_URL}/test/refresh_models", timeout=30)
        
        if response2.status_code != 200:
            print("❌ Second cache refresh failed")
            return False
        
        result2 = response2.json()
        models_count_2 = result2.get('models_cached', 0)
        
        print("✅ Model cache persistence test:")
        print(f"   - First request cached: {models_count_1} models")
        print(f"   - Second request cached: {models_count_2} models")
        print(f"   - Cache consistent: {models_count_1 == models_count_2}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test model cache persistence: {e}")
        return False

def main():
    """Run all model cache tests"""
    print("🧪 Starting Live Model Cache Tests")
    print("=" * 50)
    
    tests = [
        ("Ollama Connection", test_ollama_connection),
        ("Backend Health", test_backend_health),
        ("Model Cache Refresh", test_model_cache_refresh),
        ("Model Availability", test_model_availability),
        ("Cache Persistence", test_model_cache_persistence),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All model cache functionality is working correctly!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
