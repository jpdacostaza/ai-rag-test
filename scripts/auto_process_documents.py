#!/usr/bin/env python3
"""
Automated Document Processing System for OpenWebUI
This script ensures all uploaded files are properly processed into vector embeddings
"""
import sys
sys.path.append('/app')
import sqlite3
import chromadb
import json
from sentence_transformers import SentenceTransformer

def process_unprocessed_files():
    """Find and process all files that haven't been converted to vector embeddings"""
    print('🔄 AUTOMATED DOCUMENT PROCESSING')
    print('=' * 40)
    
    conn = sqlite3.connect('/app/backend/data/webui.db')
    cursor = conn.cursor()
    
    # Find unprocessed files
    cursor.execute('SELECT id, filename, user_id, data FROM file')
    all_files = cursor.fetchall()
    
    unprocessed_files = []
    
    for file_id, filename, user_id, data in all_files:
        cursor.execute('SELECT COUNT(*) FROM document WHERE collection_name = ?', (f'file-{file_id}',))
        doc_entries = cursor.fetchone()[0]
        
        if doc_entries == 0:
            unprocessed_files.append((file_id, filename, user_id, data))
    
    print(f'📊 Found {len(unprocessed_files)} unprocessed files')
    
    if len(unprocessed_files) == 0:
        print('✅ All files are already processed!')
        conn.close()
        return
    
    # Initialize embedding model and ChromaDB
    try:
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        chroma_client = chromadb.PersistentClient(path='/app/backend/data/chroma')
        print('🧠 Embedding model and ChromaDB initialized')
    except Exception as e:
        print(f'❌ Failed to initialize processing tools: {e}')
        conn.close()
        return
    
    # Process each unprocessed file
    for file_id, filename, user_id, data in unprocessed_files:
        print(f'\\n🔄 Processing: {filename}')
        print(f'   File ID: {file_id}')
        
        try:
            # Extract content from file data
            if data and data != 'null':
                data_obj = json.loads(data)
                content = data_obj.get('content', '')
                
                if content:
                    print(f'   Content length: {len(content)} characters')
                    
                    # 1. Create document entry
                    cursor.execute('SELECT MAX(id) FROM document')
                    max_id = cursor.fetchone()[0]
                    doc_id = (max_id + 1) if max_id else 1
                    
                    collection_name = f'file-{file_id}'
                    
                    cursor.execute('''INSERT OR REPLACE INTO document 
                        (id, collection_name, name, title, filename, content, user_id, timestamp) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                        (doc_id, collection_name, filename, f'{filename} - Auto-processed', 
                         filename, content, user_id, 1755541324))
                    
                    conn.commit()
                    print('   ✅ Document entry created')
                    
                    # 2. Create vector embeddings
                    # Check if collection already exists
                    try:
                        collection = chroma_client.get_collection(collection_name)
                        print('   📋 Collection exists, clearing old data')
                        chroma_client.delete_collection(collection_name)
                    except:
                        pass
                    
                    # Create new collection
                    collection = chroma_client.create_collection(
                        name=collection_name,
                        metadata={"description": f"Auto-processed: {filename}", "user_id": user_id}
                    )
                    
                    # Split content into chunks
                    chunk_size = 500
                    chunks = []
                    for i in range(0, len(content), chunk_size):
                        chunk = content[i:i+chunk_size].strip()
                        if chunk:
                            chunks.append(chunk)
                    
                    print(f'   📝 Created {len(chunks)} chunks')
                    
                    # Generate embeddings
                    if chunks:
                        embeddings = model.encode(chunks)
                        ids = [f'chunk_{i}' for i in range(len(chunks))]
                        metadatas = [{'chunk_index': i, 'source': filename, 'user_id': user_id} 
                                   for i in range(len(chunks))]
                        
                        # Add to ChromaDB
                        collection.add(
                            documents=chunks,
                            embeddings=embeddings.tolist(),
                            metadatas=metadatas,
                            ids=ids
                        )
                        
                        print(f'   ✅ Added {len(chunks)} chunks to vector database')
                        
                        # Test query to verify
                        test_query = filename.split('.')[0]  # Use filename as test query
                        query_embedding = model.encode([test_query])
                        results = collection.query(
                            query_embeddings=query_embedding.tolist(),
                            n_results=1
                        )
                        
                        if results['documents'][0]:
                            print(f'   🔍 Query test successful')
                        else:
                            print(f'   ⚠️  Query test failed')
                            
                    else:
                        print('   ❌ No valid chunks created')
                else:
                    print('   ❌ No content found in file data')
            else:
                print('   ❌ No data field in file record')
                
        except Exception as e:
            print(f'   ❌ Processing failed: {e}')
            import traceback
            traceback.print_exc()
    
    conn.close()
    
    # Final status check
    print(f'\\n📊 PROCESSING COMPLETE')
    print('Verifying results...')
    
    conn = sqlite3.connect('/app/backend/data/webui.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM file')
    file_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM document')
    doc_count = cursor.fetchone()[0]
    
    print(f'Final state: {file_count} files, {doc_count} documents')
    
    if file_count == doc_count:
        print('✅ SUCCESS: All files are now processed!')
    else:
        print(f'⚠️  {file_count - doc_count} files still need processing')
    
    conn.close()

if __name__ == "__main__":
    process_unprocessed_files()
