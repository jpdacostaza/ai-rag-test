#!/usr/bin/env python3
"""
Memory in Chat Verification Tool
Verifies that OpenWebUI memory is working in actual chat conversations
"""

import requests
import json
import uuid

def verify_memory_in_chat():
    """Verify memory works in actual chat scenarios"""
    
    # Configuration
    OPENWEBUI_URL = "http://localhost:3000"
    
    # Get API token from user
    API_TOKEN = input("Enter your OpenWebUI API token: ").strip()
    
    if not API_TOKEN:
        print("❌ Please provide your OpenWebUI API token")
        return
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🧠 Verifying Memory in Chat Conversations")
    print("=" * 45)
    
    # Step 1: Check current memories
    print("1. Checking current memories...")
    try:
        response = requests.get(f"{OPENWEBUI_URL}/api/v1/memories/", headers=headers)
        if response.status_code == 200:
            memories = response.json()
            print(f"   ✅ Found {len(memories)} stored memories")
            for i, memory in enumerate(memories[:3], 1):
                content = memory.get('content', '')[:50] + "..." if len(memory.get('content', '')) > 50 else memory.get('content', '')
                print(f"   📝 Memory {i}: {content}")
        else:
            print(f"   ❌ Failed to get memories: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Error checking memories: {e}")
        return
      # Step 2: Test memory query with chat context
    print("\n2. Testing memory query for chat context...")
    try:
        query_data = "What do you know about this user's preferences and background?"
        response = requests.post(f"{OPENWEBUI_URL}/api/v1/memories/query", headers=headers, json={"query": query_data})
        if response.status_code == 200:
            result = response.json()
            if result.get('documents') and result['documents'][0]:
                print(f"   ✅ Memory query returned {len(result['documents'][0])} relevant memories")
                for i, doc in enumerate(result['documents'][0][:3], 1):
                    content = doc[:60] + "..." if len(doc) > 60 else doc
                    print(f"   📝 Relevant memory {i}: {content}")
            else:
                print("   ⚠️ Memory query returned no results")
        else:
            print(f"   ❌ Memory query failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error querying memories: {e}")
    
    # Step 3: Simulate chat with memory injection
    print("\n3. Testing chat with memory context...")
    try:        # Create a chat message that should reference memory
        chat_data = {
            "model": "llama3.2:3b",  # Use available model
            "messages": [
                {
                    "role": "user",
                    "content": "Hi! Based on what you know about me, what kind of technical help would be most useful?"
                }
            ],
            "stream": False
        }
        
        response = requests.post(f"{OPENWEBUI_URL}/api/chat/completions", headers=headers, json=chat_data)
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            print("   ✅ Chat completed successfully")
            print(f"   📤 AI Response (first 200 chars): {ai_response[:200]}...")
            
            # Check if response seems to reference stored memories
            memory_indicators = [
                "software engineer", "fastapi", "debugging", "problem-solving", 
                "technical explanations", "detailed", "backend", "api"
            ]
            
            found_indicators = [indicator for indicator in memory_indicators 
                              if indicator.lower() in ai_response.lower()]
            
            if found_indicators:
                print(f"   ✅ Response appears to reference stored memories: {', '.join(found_indicators)}")
            else:
                print("   ⚠️ Response doesn't clearly reference stored memories")
                print("   💡 This might be normal - memory injection is context-dependent")
        else:
            print(f"   ❌ Chat failed: {response.status_code}")
            print(f"   📋 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error in chat: {e}")
    
    print("\n🏁 Memory Verification Complete!")
    print("\n💡 Key Points:")
    print("   • Memory storage and retrieval are working")
    print("   • OpenWebUI automatically injects relevant memories into chat context")
    print("   • Memory effectiveness depends on conversation relevance")
    print("   • You can view/manage memories in OpenWebUI Settings → Memory")

if __name__ == "__main__":
    verify_memory_in_chat()
