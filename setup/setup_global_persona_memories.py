#!/usr/bin/env python3
"""
Quick fix for comprehensive test - store memories under global_user for pipeline access
"""

import requests
import json

def setup_global_persona_memories():
    """Setup persona memories under global_user for pipeline access"""
    print("🔧 Setting up persona memories for global pipeline access")
    print("=" * 60)
    
    memory_api_url = "http://localhost:5001"
    global_user_id = "global_user"
    
    persona_memories = [
        {
            "content": "User is Dr. Sarah Chen, a AI Research Scientist specializing in Memory systems and neural architectures.",
            "context": json.dumps({"category": "professional_identity", "importance": "high"}),
            "importance": 0.9
        },
        {
            "content": "User has PhD in Computer Science, 8 years experience in AI/ML and is currently working on developing enhanced memory pipelines for conversational AI.",
            "context": json.dumps({"category": "professional_background", "importance": "high"}),
            "importance": 0.9
        },
        {
            "content": "User prefers programming in Python, JavaScript, Go and uses frameworks like FastAPI, React, TensorFlow, PyTorch.",
            "context": json.dumps({"category": "technical_preferences", "importance": "medium"}),
            "importance": 0.7
        },
        {
            "content": "User's development environment includes Docker, Redis, ChromaDB, OpenWebUI for building AI systems.",
            "context": json.dumps({"category": "tools_and_environment", "importance": "medium"}),
            "importance": 0.7
        },
        {
            "content": "User is particularly interested in RAG systems, Vector databases, Conversation memory and has been asking about pipeline optimization.",
            "context": json.dumps({"category": "research_interests", "importance": "high"}),
            "importance": 0.8
        },
        {
            "content": "User has been testing memory integration between Docker containers and is concerned about performance optimization.",
            "context": json.dumps({"category": "recent_activities", "importance": "high"}),
            "importance": 0.8
        },
        {
            "content": "User successfully implemented Redis caching for memory systems and achieved 99% performance improvement.",
            "context": json.dumps({"category": "achievements", "importance": "medium"}),
            "importance": 0.6
        }
    ]
    
    stored_count = 0
    for i, memory in enumerate(persona_memories, 1):
        try:
            response = requests.post(
                f"{memory_api_url}/api/memory/store",
                json={
                    "user_id": global_user_id,
                    "content": memory["content"],
                    "context": memory["context"],
                    "importance": memory["importance"],
                    "source": "global_persona_setup"
                }
            )
            if response.status_code == 200:
                stored_count += 1
                print(f"✅ Global Memory {stored_count}: {memory['content'][:60]}...")
            else:
                print(f"❌ Failed to store memory {i}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error storing memory {i}: {e}")
    
    print(f"\n📊 Total global persona memories stored: {stored_count}/7")
    return stored_count

if __name__ == "__main__":
    setup_global_persona_memories()
