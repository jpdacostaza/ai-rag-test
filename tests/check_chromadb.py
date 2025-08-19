#!/usr/bin/env python3
"""
ChromaDB Content Analysis
"""

import chromadb
import os

def analyze_chromadb():
    client = chromadb.HttpClient(host='chroma', port=8000)
    collection = client.get_collection('user_memory')

    print('🔍 SEARCHING FOR CV CONTENT IN CHROMADB')
    print('=' * 50)

    # Search for CV-related content
    queries = [
        'Juan-Pierre Da Costa',
        'software developer',
        'resume CV',
        'experience skills',
        'education qualifications'
    ]

    for query in queries:
        print(f'\nQuery: "{query}"')
        results = collection.query(
            query_texts=[query],
            n_results=5
        )
        
        if results['documents'] and results['documents'][0]:
            print(f'  Found {len(results["documents"][0])} results:')
            for i, doc in enumerate(results['documents'][0]):
                distance = results['distances'][0][i]
                similarity = 1 - distance
                doc_preview = doc[:150] + '...' if len(doc) > 150 else doc
                print(f'    {i+1}. Similarity: {similarity:.3f} - {doc_preview}')
        else:
            print('  No results found')

    # Check for duplicate content
    print(f'\n🔍 CHECKING FOR DUPLICATE CONTENT')
    print('=' * 50)
    
    # Get all documents 
    all_docs = collection.get()
    documents = all_docs['documents']
    
    print(f'Total documents in ChromaDB: {len(documents)}')
    
    # Look for duplicates by content hash
    from collections import Counter
    import hashlib
    
    content_hashes = []
    for doc in documents:
        content_hash = hashlib.md5(doc.encode()).hexdigest()[:12]
        content_hashes.append(content_hash)
    
    hash_counts = Counter(content_hashes)
    duplicates_found = False
    
    for content_hash, count in hash_counts.items():
        if count > 1:
            duplicates_found = True
            print(f'⚠️  DUPLICATE CONTENT: Hash {content_hash} appears {count} times')
            
            # Find the actual documents
            for i, doc in enumerate(documents):
                doc_hash = hashlib.md5(doc.encode()).hexdigest()[:12]
                if doc_hash == content_hash:
                    preview = doc[:100] + '...' if len(doc) > 100 else doc
                    print(f'    Document {i}: {preview}')
    
    if not duplicates_found:
        print('✅ No duplicate content found in ChromaDB')

if __name__ == "__main__":
    analyze_chromadb()
