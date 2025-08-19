#!/usr/bin/env python3
"""
Test script to verify ChromaClient API methods work correctly
"""

# Test the ChromaClient API to verify our method signatures
print("Testing ChromaClient API methods...")

try:
    # Try to import the ChromaClient from OpenWebUI
    import sys
    sys.path.append('/app/backend')
    from open_webui.retrieval.vector.dbs.chroma import ChromaClient
    
    print("✅ ChromaClient imported successfully")
    
    # Initialize client
    client = ChromaClient()
    print("✅ ChromaClient initialized")
    
    # List available methods
    methods = [method for method in dir(client) if not method.startswith('_')]
    print(f"Available methods: {methods}")
    
    # Test collection exists
    collection_name = "user-e7e39ee3-b886-4f92-8fb2-fbeb524fe5ce-documents"
    
    # Test search method signature
    try:
        # Generate test embeddings
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        query_embeddings = model.encode(["test query"])
        vectors = [query_embeddings[0].tolist()]
        
        print(f"Generated embeddings: {len(vectors[0])} dimensions")
        
        search_results = client.search(
            collection_name=collection_name,
            vectors=vectors,
            limit=1
        )
        print(f"✅ Search method works: {type(search_results)}")
        
        if hasattr(search_results, 'documents') and search_results.documents:
            print(f"Found {len(search_results.documents[0])} documents")
        
    except Exception as e:
        print(f"❌ Search method error: {e}")
    
    # Test query method signature
    try:
        query_results = client.query(
            collection_name=collection_name,
            filter={},
            limit=1
        )
        print(f"✅ Query method works: {type(query_results)}")
        
        if hasattr(query_results, 'documents') and query_results.documents:
            print(f"Found {len(query_results.documents[0])} documents")
        
    except Exception as e:
        print(f"❌ Query method error: {e}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
