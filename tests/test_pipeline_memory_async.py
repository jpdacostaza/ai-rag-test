#!/usr/bin/env python3
"""
Pipeline Memory Test - Async Version
"""
import sys
import os
import asyncio

# Add paths
sys.path.insert(0, os.path.abspath('./pipelines'))
sys.path.insert(0, os.path.abspath('.'))

async def test_pipeline_memory():
    """Test the pipeline memory functionality with async support"""
    print("🔬 Testing Pipeline Memory Integration (Async)")
    print("=" * 50)
    
    try:
        # Test direct import
        print("1. Testing pipeline import...")
        from pipelines.enhanced_memory_pipeline import Pipeline
        print("   ✅ Pipeline imported successfully")
        
        # Test instantiation
        print("2. Testing pipeline instantiation...")
        pipeline = Pipeline()
        print("   ✅ Pipeline instantiated successfully")
        
        # Test with sample data that should trigger memory lookup
        print("3. Testing memory lookup with user query...")
        
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": "what do you know about me?"
                }
            ],
            "user": {
                "id": "c70d5aef-4c5e-4109-bf32-641d5549e886",
                "name": "Test User"
            }
        }
        
        # Test inlet (processes incoming messages)
        print("   Testing inlet (incoming message processing)...")
        try:
            result = await pipeline.inlet(body)
            print(f"   ✅ Pipeline inlet executed successfully")
            print(f"   📝 Result type: {type(result)}")
            
            # Analyze the result
            if isinstance(result, dict) and 'messages' in result:
                messages = result['messages']
                print(f"   📨 Messages count: {len(messages)}")
                
                for i, msg in enumerate(messages):
                    content = msg.get('content', '')
                    role = msg.get('role', 'unknown')
                    print(f"   Message {i} ({role}): {content[:100]}...")
                    
                    # Check for memory injection
                    if 'J.P.' in content or 'Swift' in content:
                        print(f"   🧠 MEMORY FOUND: {content}")
                    
                    # Check for memory instructions
                    if 'CRITICAL MEMORY' in content or 'MEMORIES FROM' in content:
                        print(f"   🧠 MEMORY INSTRUCTIONS INJECTED: {content}")
                        
                    # Check for persona activation
                    if 'remember' in content.lower() or 'memory' in content.lower():
                        print(f"   🧠 MEMORY CONTEXT: {content}")
            
            elif isinstance(result, str):
                print(f"   📝 Pipeline returned string: {result[:200]}...")
                if 'J.P.' in result or 'Swift' in result:
                    print(f"   🧠 MEMORY FOUND in string result")
            
            else:
                print(f"   📝 Pipeline returned: {result}")
                
        except Exception as e:
            print(f"   ❌ Inlet error: {e}")
            import traceback
            traceback.print_exc()
            
        # Test outlet (processes outgoing responses)
        print("4. Testing outlet (outgoing response processing)...")
        try:
            # Create a mock response
            response = {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Hello! I'm an AI assistant. I don't have any information about you."
                    }
                ]
            }
            
            outlet_result = await pipeline.outlet(response)
            print(f"   ✅ Pipeline outlet executed successfully")
            print(f"   📝 Outlet result type: {type(outlet_result)}")
            
            # Check if outlet modified the response
            if isinstance(outlet_result, dict) and 'messages' in outlet_result:
                messages = outlet_result['messages']
                for i, msg in enumerate(messages):
                    content = msg.get('content', '')
                    print(f"   Outlet Message {i}: {content[:100]}...")
            
        except Exception as e:
            print(f"   ❌ Outlet error: {e}")
            import traceback
            traceback.print_exc()
            
        # Test explicit memory storage capability
        print("5. Testing explicit memory storage...")
        try:
            if hasattr(pipeline, 'store_memory'):
                # Try to store a memory directly
                memory_result = await pipeline.store_memory(
                    user_id="c70d5aef-4c5e-4109-bf32-641d5549e886",
                    content="User explicitly asked to remember their name is J.P. and they work at Swift",
                    explicit=True
                )
                print(f"   ✅ Memory stored: {memory_result}")
            else:
                print("   ⚠️ No direct store_memory method available")
        except Exception as e:
            print(f"   ❌ Memory storage error: {e}")
            
        # Test memory retrieval capability
        print("6. Testing memory retrieval...")
        try:
            if hasattr(pipeline, 'get_relevant_memories'):
                # Try to retrieve memories directly
                memories = await pipeline.get_relevant_memories(
                    user_id="c70d5aef-4c5e-4109-bf32-641d5549e886",
                    query="J.P. Swift work"
                )
                print(f"   ✅ Retrieved {len(memories)} memories")
                for i, memory in enumerate(memories):
                    print(f"   Memory {i}: {memory}")
            else:
                print("   ⚠️ No direct get_relevant_memories method available")
        except Exception as e:
            print(f"   ❌ Memory retrieval error: {e}")
            
    except Exception as e:
        print(f"   ❌ General error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pipeline_memory())
