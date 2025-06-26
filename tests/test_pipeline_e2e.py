"""
End-to-End Pipeline Test
Tests the complete OpenWebUI pipeline workflow for persistent memory
"""

import os

import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:8001"
API_KEY = os.getenv("API_KEY", "default_test_key")
TEST_USER_ID = "alice_user"
TEST_CONVERSATION_ID = "test_conv_alice"


def simulate_openwebui_workflow():
    """Simulate the complete OpenWebUI pipeline workflow"""
    print("🎭 Simulating OpenWebUI Pipeline Workflow")
    print("=" * 50)

    # Step 1: Store some initial memory
    print("📝 Step 1: Storing initial user information...")
    learn_data = {
        "user_id": TEST_USER_ID,
        "conversation_id": TEST_CONVERSATION_ID,
        "user_message": "Hi, my name is Alice and I'm a software developer from San Francisco. I love Python and machine learning.",
        "assistant_response": "Nice to meet you, Alice! It's great to hear you're into Python and machine learning. San Francisco must be an exciting place for tech!",
        "response_time": 1.2,
        "tools_used": [],
        "source": "openwebui_simulation",
    }

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    response = requests.post(f"{BACKEND_URL}/api/learning/process_interaction", json=learn_data, headers=headers)

    if response.status_code == 200:
        print("✅ Initial memory stored successfully")
    else:
        print(f"❌ Failed to store initial memory: {response.status_code}")
        return False

    # Wait for indexing
    print("⏳ Waiting for memory indexing...")
    time.sleep(3)

    # Step 2: Simulate new conversation - inlet (memory injection)
    print("\n💬 Step 2: Simulating new conversation (inlet - memory injection)...")
    inlet_data = {
        "body": {"messages": [{"role": "user", "content": "What do you remember about me?"}]},
        "user": {"id": TEST_USER_ID},
    }

    response = requests.post(f"{BACKEND_URL}/pipelines/memory_pipeline/inlet", json=inlet_data, headers=headers)

    if response.status_code == 200:
        result = response.json()
        print("✅ Pipeline inlet processed successfully")

        # Check if memory was injected
        messages = result.get("messages", [])
        print(f"📄 Messages after inlet processing:")
        for i, msg in enumerate(messages):
            print(f"   Message {i+1} ({msg.get('role', 'unknown')}): {msg.get('content', '')[:100]}...")

        memory_injected = result.get("__metadata__", {}).get("memory_injected", False)
        if memory_injected:
            print("🎉 Memory was successfully injected!")
            return True
        else:
            print("⚠️ Memory injection reported as false")

        # Check if any message contains memory context
        has_memory_context = any(
            "alice" in msg.get("content", "").lower()
            or "python" in msg.get("content", "").lower()
            or "developer" in msg.get("content", "").lower()
            or "san francisco" in msg.get("content", "").lower()
            for msg in messages
        )

        if has_memory_context:
            print("✅ Memory context found in messages!")
            return True
        else:
            print("⚠️ No clear memory context found in messages")
            return False

    else:
        print(f"❌ Pipeline inlet failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_cross_chat_memory():
    """Test cross-chat memory persistence"""
    print("\n🔄 Testing Cross-Chat Memory Persistence")
    print("=" * 40)

    # First conversation
    print("💬 First conversation: Introducing myself...")
    first_conv_data = {
        "user_id": TEST_USER_ID,
        "conversation_id": "conv_1_" + str(int(time.time())),
        "user_message": "Hi! I'm Alice, a Python developer. I work on AI projects.",
        "assistant_response": "Hello Alice! Great to meet a fellow Python enthusiast. AI projects sound fascinating!",
        "response_time": 1.0,
        "tools_used": [],
        "source": "cross_chat_test_1",
    }

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    response = requests.post(f"{BACKEND_URL}/api/learning/process_interaction", json=first_conv_data, headers=headers)

    if response.status_code != 200:
        print(f"❌ First conversation storage failed: {response.status_code}")
        return False

    print("✅ First conversation stored")

    # Wait for processing
    time.sleep(2)

    # Second conversation (different conversation ID)
    print("💬 Second conversation: Testing memory recall...")
    inlet_data = {
        "body": {"messages": [{"role": "user", "content": "Do you remember what I told you about my work?"}]},
        "user": {"id": TEST_USER_ID},
    }

    response = requests.post(f"{BACKEND_URL}/pipelines/memory_pipeline/inlet", json=inlet_data, headers=headers)

    if response.status_code == 200:
        result = response.json()
        messages = result.get("messages", [])

        # Look for memory injection
        memory_found = any(
            "alice" in msg.get("content", "").lower()
            or "python" in msg.get("content", "").lower()
            or "developer" in msg.get("content", "").lower()
            or "ai projects" in msg.get("content", "").lower()
            for msg in messages
        )

        if memory_found:
            print("🎉 Cross-chat memory working! Previous conversation remembered.")
            return True
        else:
            print("⚠️ No evidence of cross-chat memory")
            return False
    else:
        print(f"❌ Second conversation test failed: {response.status_code}")
        return False


if __name__ == "__main__":
    print("🚀 Starting End-to-End Pipeline Test")
    print("Testing persistent memory across conversations...")
    print()

    # Run the simulation
    workflow_success = simulate_openwebui_workflow()
    cross_chat_success = test_cross_chat_memory()

    print("\n" + "=" * 50)
    print("🏁 Final Results:")
    print(f"   OpenWebUI Workflow Simulation: {'✅ PASS' if workflow_success else '❌ FAIL'}")
    print(f"   Cross-Chat Memory Persistence: {'✅ PASS' if cross_chat_success else '❌ FAIL'}")

    if workflow_success and cross_chat_success:
        print("\n🎉 SUCCESS! Pipeline is working for persistent, cross-chat memory!")
        print("   OpenWebUI should now remember users across all conversations.")
    elif workflow_success:
        print("\n⚠️ PARTIAL SUCCESS: Pipeline works but cross-chat memory needs investigation.")
    else:
        print("\n❌ Pipeline needs more work. Memory injection not working as expected.")
