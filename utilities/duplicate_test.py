#!/usr/bin/env python3
"""
Test duplicate file handling behavior in OpenWebUI
"""
import chromadb
import sqlite3

def test_duplicate_behavior():
    print('🧪 DUPLICATE FILE BEHAVIOR TEST')
    print('=' * 35)
    
    # Test ChromaDB collections
    try:
        client = chromadb.PersistentClient(path='/app/backend/data/chroma')
        
        cv_collections = [
            'file-a9f7fd20-8510-4b82-a652-9860babf750a',
            'file-89f8bfe4-6f9f-47e0-80ff-c780d669b449'
        ]
        
        print('📊 VECTOR COLLECTION COMPARISON:')
        
        collection_data = {}
        
        for i, col_name in enumerate(cv_collections, 1):
            try:
                collection = client.get_collection(col_name)
                count = collection.count()
                
                print(f'\n📁 Collection {i}: {col_name}')
                print(f'   Chunks: {count}')
                
                # Get sample content
                if count > 0:
                    sample = collection.get(limit=3, include=['documents', 'metadatas'])
                    
                    if sample['documents']:
                        doc_preview = sample['documents'][0][:100]
                        metadata = sample['metadatas'][0] if sample['metadatas'] else {}
                        
                        print(f'   Preview: {doc_preview}...')
                        print(f'   Metadata: {metadata}')
                        
                        # Store for comparison
                        collection_data[col_name] = {
                            'count': count,
                            'first_chunk': sample['documents'][0],
                            'metadata': metadata
                        }
                    
                    # Test query
                    results = collection.query(query_texts=['Juan-Pierre'], n_results=1)
                    if results['documents'][0]:
                        result_preview = results['documents'][0][0][:80]
                        similarity = results['distances'][0][0]
                        print(f'   Query result: {result_preview}...')
                        print(f'   Similarity: {similarity:.4f}')
            
            except Exception as e:
                print(f'   ❌ Error: {e}')
        
        # Compare collections
        if len(collection_data) == 2:
            col1_name, col2_name = list(collection_data.keys())
            col1_data = collection_data[col1_name]
            col2_data = collection_data[col2_name]
            
            print(f'\n🔍 CONTENT COMPARISON:')
            print(f'   Chunk counts: {col1_data["count"]} vs {col2_data["count"]}')
            
            if col1_data['first_chunk'] == col2_data['first_chunk']:
                print('   ✅ Content is IDENTICAL')
            else:
                print('   ⚠️  Content is DIFFERENT')
                print(f'      Col1 start: {col1_data["first_chunk"][:50]}...')
                print(f'      Col2 start: {col2_data["first_chunk"][:50]}...')
        
    except Exception as e:
        print(f'❌ ChromaDB error: {e}')
    
    # Test what happens during RAG queries
    print(f'\n🔍 RAG QUERY BEHAVIOR TEST:')
    print('=' * 30)
    
    try:
        # Simulate a search across both collections
        search_term = 'experience'
        all_results = []
        
        for col_name in cv_collections:
            try:
                collection = client.get_collection(col_name)
                results = collection.query(query_texts=[search_term], n_results=3)
                
                if results['documents'][0]:
                    print(f'\n📁 Results from {col_name}:')
                    for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
                        print(f'   {i+1}. Score: {distance:.4f} - {doc[:60]}...')
                        all_results.append({
                            'collection': col_name,
                            'score': distance,
                            'text': doc
                        })
            
            except Exception as e:
                print(f'❌ Error querying {col_name}: {e}')
        
        # Sort all results by score
        all_results.sort(key=lambda x: x['score'])
        
        print(f'\n🏆 COMBINED RESULTS (best matches):')
        for i, result in enumerate(all_results[:5]):
            col_short = result['collection'][-8:]  # Last 8 chars of collection name
            print(f'   {i+1}. [{col_short}] {result["score"]:.4f} - {result["text"][:50]}...')
        
        # Check for duplicate results
        unique_texts = set()
        duplicates = 0
        for result in all_results:
            if result['text'] in unique_texts:
                duplicates += 1
            else:
                unique_texts.add(result['text'])
        
        print(f'\n📊 DUPLICATE ANALYSIS:')
        print(f'   Total results: {len(all_results)}')
        print(f'   Unique content: {len(unique_texts)}')
        print(f'   Duplicates: {duplicates}')
        
        if duplicates > 0:
            print('   ⚠️  RAG queries return duplicate content from both collections')
        else:
            print('   ✅ No duplicate content in results')
    
    except Exception as e:
        print(f'❌ RAG test error: {e}')
    
    # Summary and recommendations
    print(f'\n🎯 DUPLICATE HANDLING SUMMARY:')
    print('=' * 35)
    print('📁 CURRENT BEHAVIOR:')
    print('   • Same file can be uploaded multiple times')
    print('   • Each upload gets unique UUID and collection')
    print('   • Content is duplicated in vector database')
    print('   • RAG queries search across ALL collections')
    print('   • May return duplicate results from same content')
    print()
    print('⚠️  POTENTIAL ISSUES:')
    print('   • Wasted storage space (2x for each duplicate)')
    print('   • Slower query performance (searches more collections)')
    print('   • Duplicate results in RAG responses')
    print('   • User confusion about which version is active')
    print()
    print('✅ BENEFITS:')
    print('   • File redundancy (backup if one corrupts)')
    print('   • Version history preservation')
    print('   • No data loss from re-uploads')

if __name__ == "__main__":
    test_duplicate_behavior()
