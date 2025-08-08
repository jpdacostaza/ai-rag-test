#!/usr/bin/env python3
"""
Quick test of pipeline memory enhancement with global memories
"""

import requests
import json

def test_pipeline_memory_enhancement():
    """Quick test of the pipeline with global memories"""
    print("🧪 Testing Pipeline Memory Enhancement with Global Memories")
    print("=" * 65)
    
    pipeline_url = "http://localhost:9099"
    
    # Test message that should trigger memory enhancement
    test_message = {
        "user": {
            "id": "test_user",
            "name": "Test User",
            "role": "user"
        },
        "messages": [
            {
                "role": "user",
                "content": "I need help optimizing my Python memory system project with Redis cache. What's the best approach for pipeline performance?"
            }
        ],
        "body": {
            "model": "test-model",
            "messages": [
                {
                    "role": "user",
                    "content": "I need help optimizing my Python memory system project with Redis cache. What's the best approach for pipeline performance?"
                }
            ],
            "stream": False
        }
    }
    
    print(f"📤 Test Message: {test_message['messages'][0]['content']}")
    
    try:
        response = requests.post(
            f"{pipeline_url}/enhanced_memory_pipeline/filter/inlet",
            json=test_message,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract the enhanced message
            body = result.get("body", {})
            messages = body.get("messages", [])
            
            if messages:
                enhanced_content = messages[0]["content"]
                original_content = test_message["messages"][0]["content"]
                
                print(f"\n📊 Original length: {len(original_content)} chars")
                print(f"📊 Enhanced length: {len(enhanced_content)} chars")
                
                if len(enhanced_content) > len(original_content):
                    print("✅ SUCCESS: Message enhanced with memory context!")
                    
                    if "Memory" in enhanced_content or "Context" in enhanced_content:
                        print("✅ Memory markers found in enhanced content")
                    
                    print("\n📝 Enhanced Content Preview:")
                    print("-" * 60)
                    print(enhanced_content[:800] + "..." if len(enhanced_content) > 800 else enhanced_content)
                    print("-" * 60)
                    
                    return True
                else:
                    print("❌ Message not enhanced")
                    print(f"Original: {original_content}")
                    print(f"Enhanced: {enhanced_content}")
                    return False
            else:
                print("❌ No messages in response")
                return False
        else:
            print(f"❌ Pipeline request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_pipeline_memory_enhancement()
    print(f"\n🎯 Result: {'SUCCESS' if success else 'FAILED'}")
