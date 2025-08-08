#!/usr/bin/env python3
"""
Store test memories under global_user for pipeline testing
"""

import requests
import json

def store_global_memories():
    """Store test memories under global_user for pipeline access"""
    print("🧠 Storing test memories for global pipeline access")
    print("=" * 55)
    
    memory_api_url = "http://localhost:5001"
    global_user_id = "global_user"
    
    test_memories = [
        {
            "content": "User prefers Python over JavaScript for backend development. Has experience with FastAPI and Flask.",
            "metadata": {"category": "preferences", "topic": "programming"}
        },
        {
            "content": "User is working on a memory system project with Redis cache and ChromaDB vector storage.",
            "metadata": {"category": "current_project", "topic": "memory_system"}
        },
        {
            "content": "User's development environment: Windows with PowerShell, Docker containers, VS Code.",
            "metadata": {"category": "environment", "topic": "development_setup"}
        },
        {
            "content": "User has asked about pipeline memory integration and cache performance testing multiple times.",
            "metadata": {"category": "conversation_history", "topic": "memory_pipelines"}
        },
        {
            "content": "User is interested in Orange Pi 5 Plus optimization and high-performance computing configurations.",
            "metadata": {"category": "interests", "topic": "hardware_optimization"}
        }
    ]
    
    stored_count = 0
    for memory in test_memories:
        try:
            response = requests.post(
                f"{memory_api_url}/api/memory/store",
                json={
                    "user_id": global_user_id,
                    "content": memory["content"],
                    "context": json.dumps(memory["metadata"]),
                    "importance": 0.8,
                    "source": "global_pipeline_setup"
                }
            )
            if response.status_code == 200:
                stored_count += 1
                print(f"✅ Global Memory {stored_count}: {memory['content'][:50]}...")
            else:
                print(f"❌ Failed to store memory: {response.status_code}")
        except Exception as e:
            print(f"❌ Error storing memory: {e}")
    
    print(f"\n📊 Total global memories stored: {stored_count}/5")
    return stored_count

if __name__ == "__main__":
    store_global_memories()
