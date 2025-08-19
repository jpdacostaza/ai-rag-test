#!/usr/bin/env python3
"""
Test script to verify the RAG filter can work correctly
"""

import sys
sys.path.append('/app/backend')
sys.path.append('/app/functions/filters')

# Test the filter can be imported and initialized
try:
    from rag_context_injection_filter import Filter
    print("✅ Filter imported successfully")
    
    # Initialize the filter
    filter_instance = Filter()
    print("✅ Filter initialized")
    
    # Test the document search method
    import asyncio
    
    async def test_search():
        user_id = "e7e39ee3-b886-4f92-8fb2-fbeb524fe5ce"
        query = "CV information"
        
        print(f"Testing search for user: {user_id}")
        print(f"Query: {query}")
        
        try:
            results = await filter_instance._search_user_documents(user_id, query)
            print(f"✅ Search completed: {results is not None}")
            
            if results:
                print(f"Found {len(results)} documents")
                for i, result in enumerate(results):
                    print(f"Document {i}: similarity={result.get('similarity', 'N/A')}")
                    print(f"Content preview: {result.get('content', '')[:200]}...")
            else:
                print("No documents found")
                
        except Exception as e:
            print(f"❌ Search error: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the test
    asyncio.run(test_search())
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
