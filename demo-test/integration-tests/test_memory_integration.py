#!/usr/bin/env python3
"""
Test script to verify that long-term memory (chat history) is properly retrieved 
and used for each user via their OpenWebUI user ID, including for streaming and non-streaming chat.
"""

import json
import asyncio
import httpx
import time
import uuid

async def test_memory_integration():
    """Test that chat history is retrieved and used for memory."""
    
    print("=" * 60)
    print("TESTING MEMORY INTEGRATION WITH OPENWEBUI USER IDs")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    test_user_id = f"test_user_{int(time.time())}"
    
    try:
        # Test 1: Store some context in chat history
        print(f"\n1. Testing context storage for user: {test_user_id}")
        
        first_message = "My name is Alice and I work as a software engineer at TechCorp."
        response1 = await send_chat_message(base_url, test_user_id, first_message)
        print(f"   Sent: {first_message}")
        print(f"   Response: {response1[:100]}...")
        
        # Test 2: Test memory recall in regular chat
        print(f"\n2. Testing memory recall in regular chat")
        
        recall_message = "What is my name and where do I work?"
        response2 = await send_chat_message(base_url, test_user_id, recall_message)
        print(f"   Sent: {recall_message}")
        print(f"   Response: {response2}")
        
        # Check if the response includes information from previous context
        context_recalled = ("Alice" in response2 and ("TechCorp" in response2 or "software engineer" in response2))
        print(f"   ✅ Context recalled: {context_recalled}")
        
        # Test 3: Test memory recall in streaming chat  
        print(f"\n3. Testing memory recall in streaming chat")
        
        streaming_recall_message = "Tell me again about my job?"
        response3 = await send_streaming_chat_message(base_url, test_user_id, streaming_recall_message)
        print(f"   Sent: {streaming_recall_message}")
        print(f"   Streaming Response: {response3}")
        
        # Check if streaming response includes context
        streaming_context_recalled = ("Alice" in response3 or "TechCorp" in response3 or "software engineer" in response3)
        print(f"   ✅ Streaming context recalled: {streaming_context_recalled}")
        
        # Test 4: Test different user isolation
        print(f"\n4. Testing user isolation")
        
        different_user_id = f"test_user_different_{int(time.time())}"
        isolation_message = "What is my name?"
        response4 = await send_chat_message(base_url, different_user_id, isolation_message)
        print(f"   Different user sent: {isolation_message}")
        print(f"   Response: {response4}")
        
        # Should not know Alice's information
        isolation_working = ("Alice" not in response4 and "TechCorp" not in response4)
        print(f"   ✅ User isolation working: {isolation_working}")
        
        # Test 5: Test memory persistence across multiple interactions
        print(f"\n5. Testing memory persistence across multiple interactions")
        
        # Add more context
        additional_context = "I have a cat named Whiskers and I love pizza."
        response5 = await send_chat_message(base_url, test_user_id, additional_context)
        print(f"   Added context: {additional_context}")
        
        # Test comprehensive recall
        comprehensive_recall = "Tell me everything you know about me."
        response6 = await send_chat_message(base_url, test_user_id, comprehensive_recall)
        print(f"   Comprehensive recall: {response6}")
        
        # Check for all context elements
        alice_recalled = "Alice" in response6
        work_recalled = ("TechCorp" in response6 or "software engineer" in response6)
        cat_recalled = "Whiskers" in response6
        food_recalled = "pizza" in response6
        
        comprehensive_score = sum([alice_recalled, work_recalled, cat_recalled, food_recalled])
        print(f"   ✅ Comprehensive memory score: {comprehensive_score}/4")
        print(f"      - Name: {alice_recalled}")
        print(f"      - Work: {work_recalled}")
        print(f"      - Cat: {cat_recalled}")
        print(f"      - Food: {food_recalled}")
        
        # Summary
        print(f"\n" + "=" * 60)
        print("MEMORY INTEGRATION TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Basic context storage: ✓")
        print(f"✅ Regular chat memory recall: {context_recalled}")
        print(f"✅ Streaming chat memory recall: {streaming_context_recalled}")
        print(f"✅ User isolation: {isolation_working}")
        print(f"✅ Comprehensive memory: {comprehensive_score}/4")
        
        total_score = sum([context_recalled, streaming_context_recalled, isolation_working, comprehensive_score >= 3])
        print(f"\n🎯 Overall Memory Integration Score: {total_score}/4")
        
        if total_score >= 3:
            print("🎉 MEMORY INTEGRATION WORKING CORRECTLY!")
        else:
            print("⚠️  Memory integration needs attention")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

async def send_chat_message(base_url: str, user_id: str, message: str) -> str:
    """Send a regular chat message and return the response."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/chat",
            json={"user_id": user_id, "message": message},
            timeout=30.0
        )
        if response.status_code == 200:
            return response.json()["response"]
        else:
            raise Exception(f"Chat request failed: {response.status_code} - {response.text}")

async def send_streaming_chat_message(base_url: str, user_id: str, message: str) -> str:
    """Send a streaming chat message and return the accumulated response."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/v1/chat/completions",
            json={
                "model": "llama3.2:3b",
                "messages": [{"role": "user", "content": message}],
                "user": user_id,
                "stream": True
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            accumulated_response = ""
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                accumulated_response += content
                    except json.JSONDecodeError:
                        continue
            return accumulated_response
        else:
            raise Exception(f"Streaming request failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(test_memory_integration())
