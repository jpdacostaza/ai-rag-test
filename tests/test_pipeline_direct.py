#!/usr/bin/env python3
"""
Simple Pipeline Test
"""
import sys
import os
import asyncio

# Add paths
sys.path.insert(0, os.path.abspath('./pipelines'))
sys.path.insert(0, os.path.abspath('.'))

async def test_pipeline_direct():
    """Test the pipeline directly"""
    print("🔬 Testing Pipeline Direct Import")
    print("=" * 40)
    
    try:
        # Test direct import
        print("1. Testing direct import...")
        from pipelines.enhanced_memory_pipeline import Pipeline
        print("   ✅ Pipeline imported successfully")
        
        # Test instantiation
        print("2. Testing instantiation...")
        pipeline = Pipeline()
        print("   ✅ Pipeline instantiated successfully")
        
        # Test info
        print("3. Testing info...")
        try:
            info = pipeline.info()
            print(f"   ✅ Pipeline info: {info}")
        except AttributeError:
            print("   ⚠️ No info() method, checking available methods...")
            methods = [method for method in dir(pipeline) if not method.startswith('_')]
            print(f"   Available methods: {methods}")
            # Try to get basic info another way
            print(f"   Pipeline class: {pipeline.__class__.__name__}")
            print(f"   Pipeline module: {pipeline.__class__.__module__}")
        
        # Test with sample data
        print("4. Testing with sample data...")
        
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
            },
            # Also try the format OpenWebUI might use
            "user_id": "c70d5aef-4c5e-4109-bf32-641d5549e886",
            "__user": {
                "id": "c70d5aef-4c5e-4109-bf32-641d5549e886",
                "name": "Test User"
            }
        }
        
        # OpenWebUI pipelines use inlet/outlet pattern
        try:
            result = await pipeline.inlet(body)
            print(f"   ✅ Pipeline inlet executed successfully")
            print(f"   📝 Result type: {type(result)}")
            
            # Show results
            if isinstance(result, dict) and 'messages' in result:
                messages = result['messages']
                print(f"   📨 Messages count: {len(messages)}")
                
                for i, msg in enumerate(messages):
                    content = msg.get('content', '')
                    print(f"   Message {i}: {msg.get('role', 'unknown')} - {content[:100]}...")
                    if 'J.P.' in content or 'Swift' in content:
                        print(f"   🧠 MEMORY FOUND: {content}")
                        
                    # Check for memory-related content
                    if 'memory' in content.lower() or 'remember' in content.lower():
                        print(f"   🧠 MEMORY RELATED: {content}")
            
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
            
        # Test outlet as well
        print("5. Testing outlet...")
        try:
            # Create a mock response
            response = {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Hello! I'm an AI assistant."
                    }
                ]
            }
            
            outlet_result = await pipeline.outlet(response)
            print(f"   ✅ Pipeline outlet executed successfully")
            print(f"   📝 Outlet result type: {type(outlet_result)}")
            
        except Exception as e:
            print(f"   ❌ Outlet error: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pipeline_direct())
