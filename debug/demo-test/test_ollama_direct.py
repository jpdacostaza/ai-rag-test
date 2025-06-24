#!/usr/bin/env python3
"""
Test Ollama API endpoints directly to debug the issue.
"""

import json
import requests
import time

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "mistral:7b-instruct-v0.3-q4_k_m"

def test_ollama_generate():
    """Test the generate endpoint"""
    print("Testing /api/generate endpoint...")
    
    payload = {
        "model": MODEL_NAME,
        "prompt": "Hello, introduce yourself briefly.",
        "stream": False
    }
    
    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data.get('response', '')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_ollama_chat():
    """Test the chat endpoint"""
    print("\nTesting /api/chat endpoint...")
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": "Hello, introduce yourself briefly."}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Full response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_ollama_tags():
    """Test the tags endpoint"""
    print("\nTesting /api/tags endpoint...")
    
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            print(f"Available models: {models}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_ollama_tags()
    test_ollama_generate()
    test_ollama_chat()
