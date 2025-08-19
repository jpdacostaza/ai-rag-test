#!/usr/bin/env python3
"""
Check ChromaClient get method and encoding issues
"""

import sys
sys.path.append('/app/backend')
from open_webui.retrieval.vector.dbs.chroma import ChromaClient

client = ChromaClient()
collection_name = 'user-e7e39ee3-b886-4f92-8fb2-fbeb524fe5ce-documents'

print(f'Checking collection: {collection_name}')

# Check available methods
print('\nAvailable ChromaClient methods:')
methods = [m for m in dir(client) if not m.startswith('_')]
for method in methods:
    print(f'  - {method}')

# Try get() method without limit
try:
    print('\nTrying get() method...')
    results = client.get(collection_name=collection_name)
    print(f'Get method works!')
    print(f'Results type: {type(results)}')
    
    if hasattr(results, 'documents'):
        print(f'Total documents: {len(results.documents)}')
        
        # Check encoding in first few documents
        for i in range(min(3, len(results.documents))):
            doc = results.documents[i]
            print(f'\nDocument {i}:')
            print(f'  Length: {len(doc)} chars')
            print(f'  Type: {type(doc)}')
            print(f'  First 150 chars (repr): {repr(doc[:150])}')
            print(f'  First 150 chars (normal): {doc[:150]}')
            
            # Check for problematic characters
            try:
                encoded = doc.encode('utf-8')
                print(f'  UTF-8 encoding: OK')
            except Exception as e:
                print(f'  UTF-8 encoding error: {e}')
            
            # Check if it contains useful content
            if 'Juan' in doc or 'Pierre' in doc or 'resume' in doc.lower() or 'cv' in doc.lower():
                print(f'  Contains relevant keywords: YES')
            else:
                print(f'  Contains relevant keywords: NO')
    else:
        print('No documents attribute')
        print(f'Available attributes: {[attr for attr in dir(results) if not attr.startswith("_")]}')
        
except Exception as e:
    print(f'Error with get(): {e}')
    import traceback
    traceback.print_exc()

print('\n=== Checking what was injected in recent conversations ===')
# Let's also look at the filter logs to see what was actually injected
print('Recent RAG injection logs show content was injected, checking filter behavior...')
