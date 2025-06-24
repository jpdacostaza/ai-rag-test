#!/usr/bin/env python3
"""Test script to trigger debug messages in the OpenAI-compatible endpoint."""

import requests
import json
import time

def test_openai_endpoint():
    """Test the OpenAI-compatible endpoint with debug logging."""
    
    url = "http://localhost:8001/v1/chat/completions"
    
    # Test with default model
    payload = {
        "model": "llama3.2:3b",
        "messages": [
            {"role": "user", "content": "Hello! Please respond with 'Debug test successful'"}
        ],
        "max_tokens": 50,
        "temperature": 0.7,
        "stream": False
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("Testing OpenAI endpoint with default model...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.text:
            print(f"Response Text: {response.text}")
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    response_json = response.json()
                    print(f"Response JSON: {json.dumps(response_json, indent=2)}")
                except:
                    print("Failed to parse response as JSON")
        else:
            print("Empty response body")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test with Mistral model
    payload["model"] = "mistral:7b-instruct-v0.3-q4_k_m"
    
    print("Testing OpenAI endpoint with Mistral model...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.text:
            print(f"Response Text: {response.text}")
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    response_json = response.json()
                    print(f"Response JSON: {json.dumps(response_json, indent=2)}")
                except:
                    print("Failed to parse response as JSON")
        else:
            print("Empty response body")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_openai_endpoint()
