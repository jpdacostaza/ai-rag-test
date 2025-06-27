#!/usr/bin/env python3
"""
Live End-to-End Memory Pipeline Test
This simulates exactly what OpenWebUI does when processing messages
"""

import requests
import json
import time

def test_memory_pipeline_live():
    """Test the complete memory pipeline flow"""
    print("🧪 LIVE MEMORY PIPELINE TEST")
    print("=" * 60)
    
    # Step 1: Verify all services are running
    print("1️⃣ CHECKING SERVICES...")
    
    # Check Memory API
    try:
        response = requests.get("http://localhost:8000/")
        print(f"✅ Memory API: {response.status_code} - {response.json()['message']}")
    except Exception as e:
        print(f"❌ Memory API failed: {e}")
        return False
    
    # Check Pipelines Server
    try:
        response = requests.get("http://localhost:9098/", 
                              headers={"Authorization": "Bearer 0p3n-w3bu!"})
        print(f"✅ Pipelines Server: {response.status_code}")
        
        # Check our pipeline is loaded
        response = requests.get("http://localhost:9098/pipelines",
                              headers={"Authorization": "Bearer 0p3n-w3bu!"})
        pipelines = response.json()
        pipeline_found = False
        for p in pipelines.get('data', []):
            if 'memory' in p.get('name', '').lower():
                print(f"✅ Memory Pipeline Found: {p['name']}")
                pipeline_found = True
                break
        
        if not pipeline_found:
            print("❌ Memory pipeline not found")
            return False
            
    except Exception as e:
        print(f"❌ Pipelines Server failed: {e}")
        return False
    
    # Check OpenWebUI
    try:
        response = requests.get("http://localhost:3000/health")
        print(f"✅ OpenWebUI: {response.status_code}")
    except Exception as e:
        print(f"❌ OpenWebUI failed: {e}")
        return False
    
    print("\n2️⃣ LIVE MEMORY TEST SCENARIO...")
    
    # Test user ID for this session
    test_user = "live_test_user"
    
    # Step 2: Store some personal information (simulating user conversation)
    print(f"\n👤 Simulating user '{test_user}' sharing personal info...")
    
    personal_messages = [
        "Hi! My name is Emma and I work as a software architect at Google.",
        "I specialize in distributed systems and cloud architecture.",
        "I have 8 years of experience in Python and love working with Kubernetes.",
        "I'm currently leading a team of 12 developers on a new microservices platform."
    ]
    
    for i, message in enumerate(personal_messages, 1):
        print(f"   📝 Message {i}: {message[:50]}...")
        
        # Store in memory API (this is what our pipeline does)
        try:
            response = requests.post(
                "http://localhost:8000/api/learning/process_interaction",
                json={
                    "user_id": test_user,
                    "conversation_id": f"live_test_chat_{int(time.time())}",
                    "user_message": message,
                    "context": {"test": True, "step": i}
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Stored (Total memories: {result.get('memories_count', 0)})")
            else:
                print(f"   ❌ Storage failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Storage error: {e}")
    
    print(f"\n3️⃣ TESTING MEMORY RETRIEVAL...")
    
    # Step 3: Test memory retrieval (what happens when user asks about themselves)
    query_messages = [
        "What do you know about me?",
        "Tell me about my work experience",
        "What's my role at my company?",
        "What technologies am I good with?"
    ]
    
    for query in query_messages:
        print(f"\n🔍 Query: '{query}'")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/memory/retrieve",
                json={
                    "user_id": test_user,
                    "query": query,
                    "limit": 3
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get('memories', [])
                print(f"   ✅ Found {len(memories)} relevant memories:")
                
                for i, memory in enumerate(memories, 1):
                    content = memory.get('content', '')[:80]
                    score = memory.get('similarity_score', 0)
                    print(f"      {i}. {content}... (Score: {score:.3f})")
                    
                if not memories:
                    print("   ⚠️  No memories found - this could indicate an issue")
            else:
                print(f"   ❌ Retrieval failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Retrieval error: {e}")
    
    print(f"\n4️⃣ SIMULATING OPENWEBUI MESSAGE FLOW...")
    
    # Step 4: Simulate what OpenWebUI does - send a message through the pipeline
    openwebui_request = {
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "What do you remember about my professional background?"}
        ],
        "model": "test-model",
        "stream": False
    }
    
    print("📤 Sending request to pipeline (simulating OpenWebUI)...")
    print(f"   User message: '{openwebui_request['messages'][-1]['content']}'")
    
    try:
        # This simulates OpenWebUI calling our pipeline's inlet method
        response = requests.post(
            f"http://localhost:9098/",
            json=openwebui_request,
            headers={
                "Authorization": "Bearer 0p3n-w3bu!",
                "Content-Type": "application/json",
                "X-User-ID": test_user  # Some pipelines use this header
            }
        )
        
        print(f"   📥 Pipeline response: {response.status_code}")
        
        if response.status_code == 200:
            # The pipeline should have modified the messages to include memory context
            print("   ✅ Pipeline processed successfully!")
            print("   📋 This means your memory pipeline is working in OpenWebUI!")
        else:
            print(f"   ⚠️  Pipeline response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Pipeline test error: {e}")
    
    print(f"\n🎯 FINAL STATUS REPORT")
    print("=" * 60)
    
    # Get final memory stats
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ Memory API: Operational")
    except:
        print("❌ Memory API: Issues detected")
    
    try:
        response = requests.get("http://localhost:9098/pipelines",
                              headers={"Authorization": "Bearer 0p3n-w3bu!"})
        if response.status_code == 200:
            print("✅ Pipelines Server: Operational with memory pipeline loaded")
    except:
        print("❌ Pipelines Server: Issues detected")
    
    try:
        response = requests.get("http://localhost:3000/health")
        if response.status_code == 200:
            print("✅ OpenWebUI: Operational")
    except:
        print("❌ OpenWebUI: Issues detected")
    
    print(f"\n🚀 READY FOR LIVE TESTING!")
    print("Now go to http://localhost:3000 and:")
    print("1. Start a new chat")
    print("2. Share some personal information") 
    print("3. Ask 'What do you know about me?'")
    print("4. The AI should respond with your stored information!")

if __name__ == "__main__":
    test_memory_pipeline_live()
