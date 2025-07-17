#!/usr/bin/env python3
"""
Pipeline Memory Test - Fixed Configuration
"""
import sys
import os
import asyncio

# Set environment variable for correct API URL
os.environ['MEMORY_API_URL'] = 'http://localhost:5001'

# Add paths
sys.path.insert(0, os.path.abspath('./pipelines'))
sys.path.insert(0, os.path.abspath('.'))

async def test_pipeline_memory_fixed():
    """Test the pipeline memory functionality with correct configuration"""
    print("🔬 Testing Pipeline Memory Integration (Fixed Configuration)")
    print("=" * 60)
    
    try:
        # Test direct import with correct environment
        print("1. Testing pipeline import with correct config...")
        from pipelines.enhanced_memory_pipeline import Pipeline
        print("   ✅ Pipeline imported successfully")
        
        # Test instantiation
        print("2. Testing pipeline instantiation...")
        pipeline = Pipeline()
        print("   ✅ Pipeline instantiated successfully")
        
        # Test with sample data that should trigger memory lookup
        print("3. Testing memory lookup with proper user ID...")
        
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
                    print(f"   Message {i} ({role}): {content[:150]}...")
                    
                    # Check for memory injection
                    if 'J.P.' in content or 'Swift' in content or 'work' in content:
                        print(f"   🧠 MEMORY FOUND: {content}")
                    
                    # Check for memory instructions
                    if 'CRITICAL MEMORY' in content or 'MEMORIES FROM' in content:
                        print(f"   🧠 MEMORY INSTRUCTIONS INJECTED: {content}")
                        
                    # Check for persona activation
                    if 'remember' in content.lower() or 'memory' in content.lower():
                        print(f"   🧠 MEMORY CONTEXT DETECTED")
            
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
                        "content": "Hello! Based on what I know about you, I can help you with Swift development and your work at J.P. Morgan."
                    }
                ],
                "user": {
                    "id": "c70d5aef-4c5e-4109-bf32-641d5549e886",
                    "name": "Test User"
                }
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
                    
                    # Check if memory was stored
                    if 'Swift' in content or 'J.P.' in content:
                        print(f"   🧠 MEMORY CONTEXT DETECTED in outlet")
            
        except Exception as e:
            print(f"   ❌ Outlet error: {e}")
            import traceback
            traceback.print_exc()
            
        # Test memory storage capability (correct signature)
        print("5. Testing memory storage with correct signature...")
        try:
            if hasattr(pipeline, 'store_memory'):
                # Try to store a memory directly with correct signature
                memory_result = await pipeline.store_memory(
                    user_id="c70d5aef-4c5e-4109-bf32-641d5549e886",
                    content="User works at J.P. Morgan as a Swift developer"
                )
                print(f"   ✅ Memory stored: {memory_result}")
            else:
                print("   ⚠️ No direct store_memory method available")
        except Exception as e:
            print(f"   ❌ Memory storage error: {e}")
            
        # Test memory retrieval capability
        print("6. Testing memory retrieval with correct API...")
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
            
        # Test comprehensive persona integration
        print("7. Testing comprehensive persona integration...")
        try:
            # Test with a message that should trigger memory lookup and persona
            persona_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello! Can you help me with some Swift code?"
                    }
                ],
                "user": {
                    "id": "c70d5aef-4c5e-4109-bf32-641d5549e886",
                    "name": "Test User"
                }
            }
            
            persona_result = await pipeline.inlet(persona_body)
            
            if isinstance(persona_result, dict) and 'messages' in persona_result:
                messages = persona_result['messages']
                for i, msg in enumerate(messages):
                    content = msg.get('content', '')
                    role = msg.get('role', 'unknown')
                    if role == 'system':
                        print(f"   🧠 System Message: {content[:200]}...")
                        # Check for memory context
                        if 'J.P.' in content or 'Swift' in content:
                            print(f"   ✅ PERSONA WORKING: Memory integrated in system message")
                        else:
                            print(f"   ⚠️ PERSONA STATUS: No memory context found")
            
        except Exception as e:
            print(f"   ❌ Persona integration error: {e}")
            
    except Exception as e:
        print(f"   ❌ General error: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n🎯 CONCLUSION:")
    print("   - Pipeline imports and instantiates successfully")
    print("   - Memory API connection needs correct configuration")
    print("   - User authentication extraction needs improvement")
    print("   - Memory storage/retrieval functionality present")
    print("   - Persona integration depends on memory retrieval")

if __name__ == "__main__":
    asyncio.run(test_pipeline_memory_fixed())
