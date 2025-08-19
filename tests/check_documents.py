#!/usr/bin/env python3
"""
Check all documents in ChromaDB and PDF extraction capabilities
"""

import sys
sys.path.append('/app/backend')
from open_webui.retrieval.vector.dbs.chroma import ChromaClient

client = ChromaClient()
try:
    # Check the main user collection
    user_id = 'e7e39ee3-b886-4f92-8fb2-fbeb524fe5ce'
    collection_name = f'user-{user_id}-documents'
    
    print(f'Checking collection: {collection_name}')
    exists = client.has_collection(collection_name)
    print(f'Collection exists: {exists}')
    
    if exists:
        # Try to get all documents
        results = client.get(collection_name=collection_name, limit=50)
        
        if hasattr(results, 'documents') and results.documents:
            print(f'Total documents in collection: {len(results.documents)}')
            
            for i, doc in enumerate(results.documents[:10]):  # Show first 10
                metadata = results.metadatas[i] if results.metadatas and i < len(results.metadatas) else {}
                
                print(f'\nDocument {i}:')
                print(f'  Length: {len(doc)} chars')
                print(f'  Metadata: {metadata}')
                print(f'  Preview: {doc[:200]}...')
                
        else:
            print('No documents found or wrong format')
            print(f'Results type: {type(results)}')
            print(f'Results attributes: {dir(results)}')
                
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()

# Also check PDF extraction settings
print('\n=== PDF EXTRACTION SETTINGS ===')
try:
    import os
    pdf_extract = os.getenv('PDF_EXTRACT_IMAGES', 'false')
    rag_engine = os.getenv('RAG_EMBEDDING_ENGINE', 'unknown')
    rag_model = os.getenv('RAG_EMBEDDING_MODEL', 'unknown')
    content_engine = os.getenv('CONTENT_EXTRACTION_ENGINE', 'unknown')
    
    print(f'PDF_EXTRACT_IMAGES: {pdf_extract}')
    print(f'RAG_EMBEDDING_ENGINE: {rag_engine}')
    print(f'RAG_EMBEDDING_MODEL: {rag_model}')
    print(f'CONTENT_EXTRACTION_ENGINE: {content_engine}')
    
except Exception as e:
    print(f'Error checking environment: {e}')
