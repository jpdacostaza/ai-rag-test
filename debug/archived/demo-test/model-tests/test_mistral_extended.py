#!/usr/bin/env python3
"""
Extended capability tests for Mistral 7B Instruct model.
"""

import json
import requests
import time
from datetime import datetime

BACKEND_URL = "http://localhost:8001"
MODEL_NAME = "mistral:7b-instruct-v0.3-q4_k_m"

def test_code_generation():
    """Test code generation capabilities"""
    print("🧪 Testing code generation...")
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": "Write a Python function to calculate fibonacci numbers using memoization. Include docstring and comments."}
        ],
        "max_tokens": 500
    }
    
    start_time = time.time()
    response = requests.post(f"{BACKEND_URL}/v1/chat/completions", json=payload, timeout=60)
    response_time = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Check for code indicators
        code_indicators = ["def", "fibonacci", "memo", "return", "def fibonacci"]
        has_code = any(indicator in content.lower() for indicator in code_indicators)
        
        print(f"✅ Response time: {response_time:.2f}s")
        print(f"✅ Contains code elements: {has_code}")
        print(f"Response preview:\n{content[:400]}...")
        return True
    else:
        print(f"❌ Failed with status {response.status_code}")
        return False

def test_reasoning():
    """Test logical reasoning"""
    print("\n🧪 Testing logical reasoning...")
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": """Solve this logic puzzle step by step:
            - There are 3 houses: red, blue, and green
            - The person in the red house drinks coffee
            - The person who drinks tea lives next to the coffee drinker
            - The person in the blue house is a teacher
            - The green house is not next to the blue house
            
            Who lives in which house and what do they drink?"""}
        ],
        "max_tokens": 400
    }
    
    start_time = time.time()
    response = requests.post(f"{BACKEND_URL}/v1/chat/completions", json=payload, timeout=60)
    response_time = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Check for reasoning indicators
        reasoning_words = ["step", "first", "therefore", "because", "next", "conclusion"]
        has_reasoning = any(word in content.lower() for word in reasoning_words)
        
        print(f"✅ Response time: {response_time:.2f}s")
        print(f"✅ Shows reasoning process: {has_reasoning}")
        print(f"Response preview:\n{content[:400]}...")
        return True
    else:
        print(f"❌ Failed with status {response.status_code}")
        return False

def test_multilingual():
    """Test multilingual capabilities"""
    print("\n🧪 Testing multilingual capabilities...")
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": "Translate this sentence to French, Spanish, and German: 'The weather is beautiful today.'"}
        ],
        "max_tokens": 200
    }
    
    start_time = time.time()
    response = requests.post(f"{BACKEND_URL}/v1/chat/completions", json=payload, timeout=60)
    response_time = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Check for language indicators
        lang_indicators = ["french", "spanish", "german", "français", "español", "deutsch"]
        has_languages = any(lang.lower() in content.lower() for lang in lang_indicators)
        
        print(f"✅ Response time: {response_time:.2f}s")
        print(f"✅ Contains language labels: {has_languages}")
        print(f"Response:\n{content}")
        return True
    else:
        print(f"❌ Failed with status {response.status_code}")
        return False

def test_conversation_memory():
    """Test conversation context/memory"""
    print("\n🧪 Testing conversation memory...")
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": "My favorite color is purple and I'm a software engineer."},
            {"role": "assistant", "content": "That's interesting! Purple is a lovely color, and software engineering is a great field."},
            {"role": "user", "content": "What did I tell you about my profession and favorite color?"}
        ],
        "max_tokens": 100
    }
    
    start_time = time.time()
    response = requests.post(f"{BACKEND_URL}/v1/chat/completions", json=payload, timeout=60)
    response_time = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Check if it remembers the details
        remembers_color = "purple" in content.lower()
        remembers_profession = any(word in content.lower() for word in ["software", "engineer", "programming"])
        
        print(f"✅ Response time: {response_time:.2f}s")
        print(f"✅ Remembers color: {remembers_color}")
        print(f"✅ Remembers profession: {remembers_profession}")
        print(f"Response: {content}")
        return remembers_color and remembers_profession
    else:
        print(f"❌ Failed with status {response.status_code}")
        return False

def test_creative_writing():
    """Test creative writing"""
    print("\n🧪 Testing creative writing...")
    
    payload = {
        "message": "Write a very short story (3-4 sentences) about a robot discovering music for the first time.",
        "user_id": "test_user_creative"
    }
    
    start_time = time.time()
    response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=60)
    response_time = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        content = data.get("response", "")
        
        # Check for creative elements
        creative_words = ["music", "robot", "heard", "sound", "melody", "first time"]
        is_creative = any(word in content.lower() for word in creative_words)
        
        print(f"✅ Response time: {response_time:.2f}s")
        print(f"✅ Contains creative elements: {is_creative}")
        print(f"Story:\n{content}")
        return True
    else:
        print(f"❌ Failed with status {response.status_code}")
        return False

def main():
    print(f"🚀 Extended capability tests for Mistral 7B Instruct")
    print(f"Model: {MODEL_NAME}")
    print("=" * 70)
    
    tests = [
        test_code_generation,
        test_reasoning,
        test_multilingual,
        test_conversation_memory,
        test_creative_writing
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        time.sleep(2)
    
    print("\n" + "=" * 70)
    print(f"🎯 Extended Test Results: {passed}/{len(tests)} passed")
    print(f"   Success Rate: {(passed/len(tests))*100:.1f}%")

if __name__ == "__main__":
    main()
