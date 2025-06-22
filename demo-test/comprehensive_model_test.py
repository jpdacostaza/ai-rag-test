#!/usr/bin/env python3
"""
Comprehensive test script for the FastAPI backend with Mistral model integration.
Tests both /chat and /v1/chat/completions endpoints with all available models.
"""

import requests
import json
import time
from typing import Dict, Any

def test_endpoint(url: str, payload: Dict[str, Any], test_name: str) -> bool:
    """Test an endpoint and return success status."""
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {test_name}")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 60)
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
        elapsed = (time.time() - start_time) * 1000
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"⏱️  Response Time: {elapsed:.2f}ms")
        print(f"📄 Headers: {dict(response.headers)}")
        
        if response.text:
            print(f"📝 Response Text: {response.text}")
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    response_json = response.json()
                    print(f"🎯 Response JSON: {json.dumps(response_json, indent=2)}")
                    
                    # Check for content in response
                    if 'choices' in response_json and len(response_json['choices']) > 0:
                        content = response_json['choices'][0].get('message', {}).get('content', '')
                        if content.strip():
                            print(f"✅ SUCCESS: Got content: '{content.strip()}'")
                            return True
                        else:
                            print(f"❌ FAILED: Empty content")
                            return False
                    elif 'response' in response_json:
                        content = response_json.get('response', '')
                        if content.strip():
                            print(f"✅ SUCCESS: Got response: '{content.strip()}'")
                            return True
                        else:
                            print(f"❌ FAILED: Empty response")
                            return False
                except Exception as e:
                    print(f"❌ JSON parsing error: {e}")
                    return False
        else:
            print("❌ FAILED: Empty response body")
            return False
            
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        print(f"❌ ERROR after {elapsed:.2f}ms: {e}")
        return False
    
    # Fallback return
    return False

def test_models():
    """Test all available models with both endpoints."""
    
    # Test models
    models_to_test = [
        "llama3.2:3b",
        "mistral:7b-instruct-v0.3-q4_k_m",
        "llama3.2:1b"
    ]
    
    base_url = "http://localhost:8001"
    test_message = "Hello! Please respond with a short greeting and tell me your model name."
    
    results = []
    
    print("🚀 COMPREHENSIVE MODEL AND ENDPOINT TESTING")
    print("=" * 80)
    
    # Test /v1/models endpoint first
    print(f"\n🔍 Testing /v1/models endpoint...")
    try:
        response = requests.get(f"{base_url}/v1/models")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            models = response.json()
            print(f"Available models: {[model['id'] for model in models['data']]}")
        else:
            print(f"Failed to get models: {response.text}")
    except Exception as e:
        print(f"Error getting models: {e}")
    
    # Test each model with both endpoints
    for model in models_to_test:
        print(f"\n🤖 TESTING MODEL: {model}")
        print("=" * 80)
        
        # Test /chat endpoint
        chat_payload = {
            "user_id": "test_user_comprehensive",
            "message": test_message
        }
        
        success_chat = test_endpoint(
            f"{base_url}/chat",
            chat_payload,
            f"Chat Endpoint with {model}"
        )
        results.append(f"Chat/{model}: {'✅ PASS' if success_chat else '❌ FAIL'}")
        
        # Test /v1/chat/completions endpoint
        openai_payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": test_message}
            ],
            "max_tokens": 100,
            "temperature": 0.7,
            "stream": False
        }
        
        success_openai = test_endpoint(
            f"{base_url}/v1/chat/completions",
            openai_payload,
            f"OpenAI Completions with {model}"
        )
        results.append(f"OpenAI/{model}: {'✅ PASS' if success_openai else '❌ FAIL'}")
    
    # Test streaming endpoint
    print(f"\n🌊 TESTING STREAMING...")
    streaming_payload = {
        "model": "llama3.2:3b",
        "messages": [
            {"role": "user", "content": "Count from 1 to 5 with explanations."}
        ],
        "stream": True,
        "max_tokens": 100
    }
    
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json=streaming_payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=30
        )
        
        print(f"Streaming Status: {response.status_code}")
        if response.status_code == 200:
            print("Streaming content:")
            content_received = ""
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    print(f"  {line_text}")
                    if line_text.startswith('data: ') and not line_text.endswith('[DONE]'):
                        try:
                            data = json.loads(line_text[6:])
                            if 'choices' in data and data['choices']:
                                delta_content = data['choices'][0].get('delta', {}).get('content', '')
                                content_received += delta_content
                        except:
                            pass
            
            if content_received.strip():
                print(f"✅ Streaming SUCCESS: Received content")
                results.append("Streaming: ✅ PASS")
            else:
                print(f"❌ Streaming FAILED: No content received")
                results.append("Streaming: ❌ FAIL")
        else:
            print(f"❌ Streaming FAILED: {response.text}")
            results.append("Streaming: ❌ FAIL")
            
    except Exception as e:
        print(f"❌ Streaming ERROR: {e}")
        results.append("Streaming: ❌ FAIL")
    
    # Print summary
    print(f"\n📊 FINAL RESULTS SUMMARY")
    print("=" * 80)
    for result in results:
        print(f"  {result}")
    
    print(f"\n🎯 CONCLUSION:")
    total_tests = len(results)
    passed_tests = len([r for r in results if "✅ PASS" in r])
    print(f"  Passed: {passed_tests}/{total_tests}")
    print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print(f"  🎉 ALL TESTS PASSED! Backend is fully functional.")
    else:
        print(f"  ⚠️  Some tests failed. Check individual results above.")

if __name__ == "__main__":
    test_models()
