#!/usr/bin/env python3
"""
Session Persistence Debug Test
Specifically test session handling and examine stored metadata
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, Any, List


class SessionDebugTest:
    """Debug session persistence issues"""
    
    def __init__(self):
        self.api_base = "http://localhost:5001"
        
    def log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def store_memory(self, content: str, user_id: str, context: str = "Test", 
                    session_id: str = None) -> str:
        """Store a memory and return the memory_id"""
        memory_id = f"debug_{user_id}_{int(time.time() * 1000000)}"
        
        metadata = {
            "user_id": user_id,
            "memory_id": memory_id,
            "context": context,
            "source": "debug_test"
        }
        
        if session_id:
            metadata["session_id"] = session_id
            metadata["context"] = f"{context} | Session: {session_id}"
            
        payload = {
            "content": content,
            "metadata": metadata,
            "user_id": user_id
        }
        
        try:
            response = requests.post(f"{self.api_base}/api/memory/store", 
                                  json=payload, timeout=10)
            if response.status_code == 200:
                self.log("INFO", f"✅ Stored: {memory_id}")
                self.log("INFO", f"   Content: {content}")
                self.log("INFO", f"   Metadata: {json.dumps(metadata, indent=2)}")
                return memory_id
            else:
                self.log("ERROR", f"❌ Store failed: {response.text}")
                return None
        except Exception as e:
            self.log("ERROR", f"❌ Store error: {str(e)}")
            return None

    def retrieve_memories(self, query: str, user_id: str, limit: int = 10, 
                         threshold: float = 2.0) -> List[Dict]:
        """Retrieve memories and show detailed metadata"""
        payload = {
            "query": query,
            "user_id": user_id,
            "limit": limit,
            "threshold": threshold
        }
        
        try:
            response = requests.post(f"{self.api_base}/api/memory/retrieve", 
                                  json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                memories = data.get("memories", [])
                self.log("INFO", f"✅ Retrieved {len(memories)} memories")
                
                for i, memory in enumerate(memories, 1):
                    self.log("INFO", f"   Memory {i}:")
                    self.log("INFO", f"     Content: {memory.get('content', '')[:100]}...")
                    self.log("INFO", f"     Metadata: {json.dumps(memory.get('metadata', {}), indent=6)}")
                    self.log("INFO", f"     Distance: {memory.get('distance', 'N/A')}")
                
                return memories
            else:
                self.log("ERROR", f"❌ Retrieve failed: {response.text}")
                return []
        except Exception as e:
            self.log("ERROR", f"❌ Retrieve error: {str(e)}")
            return []

    def run_session_debug(self):
        """Run detailed session persistence debug"""
        self.log("INFO", "🔍 Starting Session Persistence Debug Test")
        
        user_id = "debug_alice"
        
        # Session 1: Store memory with session ID
        self.log("INFO", "\n=== SESSION 1 ===")
        session1_id = f"{user_id}_session_1_{int(time.time())}"
        
        content1 = "Alice started working on a machine learning project"
        memory_id1 = self.store_memory(content1, user_id, "Session 1", session_id=session1_id)
        
        time.sleep(1)
        
        # Test immediate retrieval in same session
        self.log("INFO", "\n--- Immediate retrieval (same session) ---")
        memories = self.retrieve_memories("machine learning", user_id, limit=5, threshold=2.0)
        
        # Check if session ID is in metadata
        for memory in memories:
            metadata = memory.get("metadata", {})
            context = metadata.get("context", "")
            session_id_in_metadata = metadata.get("session_id", "")
            
            self.log("INFO", f"   Session ID in metadata: {session_id_in_metadata}")
            self.log("INFO", f"   Session ID in context: {session1_id in context}")
            self.log("INFO", f"   Full context: {context}")
        
        # Session 2: Try to retrieve session 1 context
        self.log("INFO", "\n=== SESSION 2 ===")
        session2_id = f"{user_id}_session_2_{int(time.time())}"
        
        # Query for previous session
        self.log("INFO", "\n--- Cross-session retrieval ---")
        previous_memories = self.retrieve_memories("project", user_id, limit=10, threshold=2.0)
        
        session1_found = False
        for memory in previous_memories:
            metadata = memory.get("metadata", {})
            context = metadata.get("context", "")
            if session1_id in context:
                session1_found = True
                self.log("INFO", f"   ✅ Found session 1 memory in session 2!")
                break
        
        if not session1_found:
            self.log("ERROR", f"   ❌ Session 1 memory NOT found in session 2")
            self.log("ERROR", f"   Looking for session ID: {session1_id}")
        
        # Store memory in session 2
        content2 = "Alice continued the project with data preprocessing"
        memory_id2 = self.store_memory(content2, user_id, "Session 2", session_id=session2_id)
        
        time.sleep(1)
        
        # Final test: retrieve all project memories
        self.log("INFO", "\n--- Final cross-session test ---")
        all_memories = self.retrieve_memories("project", user_id, limit=20, threshold=2.0)
        
        session1_count = 0
        session2_count = 0
        
        for memory in all_memories:
            metadata = memory.get("metadata", {})
            context = metadata.get("context", "")
            
            if session1_id in context:
                session1_count += 1
            if session2_id in context:
                session2_count += 1
        
        self.log("INFO", f"\n🎯 SESSION DEBUG RESULTS:")
        self.log("INFO", f"   Total memories retrieved: {len(all_memories)}")
        self.log("INFO", f"   Session 1 memories found: {session1_count}")
        self.log("INFO", f"   Session 2 memories found: {session2_count}")
        self.log("INFO", f"   Cross-session working: {session1_count > 0 and session2_count > 0}")

if __name__ == "__main__":
    test = SessionDebugTest()
    test.run_session_debug()
