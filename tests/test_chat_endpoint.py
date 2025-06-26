#!/usr/bin/env python3
"""
Quick test of the chat completions endpoint
"""

import requests
import json


def test_chat_endpoint():
    """TODO: Add proper docstring for test_chat_endpoint."""
    backend_url = "http://localhost:8001"
    headers = {"Authorization": "Bearer f2b985dd-219f-45b1-a90e-170962cc7082", "Content-Type": "application/json"}

    # Test basic chat
    print("Testing basic chat endpoint...")
    chat_data = {
        "model": "mistral:7b-instruct-v0.3-q4_k_m",
        "messages": [{"role": "user", "content": "Hello, please respond with just 'Hi there!'"}],
    }

    try:
        response = requests.post(f"{backend_url}/v1/chat/completions", json=chat_data, headers=headers, timeout=120)

        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")

        if response.status_code == 200:
            print("[OK] Basic chat endpoint works")
        else:
            print(f"[FAIL] Chat endpoint failed: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] Chat endpoint error: {e}")

    # Test with memory
    print("\nTesting chat endpoint with memory...")
    chat_data_memory = {
        "model": "mistral:7b-instruct-v0.3-q4_k_m",
        "messages": [{"role": "user", "content": "What's my name?"}],
        "user_id": "test_openwebui_user",
        "use_memory": True,
    }

    try:
        response = requests.post(
            f"{backend_url}/v1/chat/completions", json=chat_data_memory, headers=headers, timeout=120
        )

        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")

        if response.status_code == 200:
            print("[OK] Memory chat endpoint works")
        else:
            print(f"[FAIL] Memory chat endpoint failed: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] Memory chat endpoint error: {e}")


if __name__ == "__main__":
    test_chat_endpoint()
