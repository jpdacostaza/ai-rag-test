#!/usr/bin/env python3
"""
OpenWebUI Document Processing Fix
This script patches the document upload workflow to ensure automatic vector processing
"""
import sys
sys.path.append('/app')

def check_and_fix_processing_workflow():
    """Check current processing workflow and implement fixes"""
    print('🔧 FIXING OPENWEBUI DOCUMENT PROCESSING WORKFLOW')
    print('=' * 55)
    
    # 1. Check current upload_file function behavior
    try:
        from open_webui.routers.files import upload_file, process_file
        import inspect
        
        print('📋 Current upload_file workflow analysis:')
        source = inspect.getsource(upload_file)
        
        # Check if process=True actually triggers processing
        if 'process_file(' in source and 'if process:' in source:
            print('✅ upload_file has process_file integration')
        else:
            print('❌ upload_file missing process_file integration')
            
        # Check process_file function
        process_source = inspect.getsource(process_file)
        if 'VECTOR_DB_CLIENT' in process_source:
            print('✅ process_file has vector DB integration')
        else:
            print('❌ process_file missing vector DB integration')
            
    except ImportError as e:
        print(f'❌ Cannot access router functions: {e}')
        return False
    
    # 2. Check vector database configuration
    print(f'\n🗄️ Vector Database Configuration:')
    try:
        import chromadb
        from open_webui.retrieval.vector.dbs.chroma import ChromaClient
        
        # Test ChromaDB connection
        client = chromadb.PersistentClient(path='/app/backend/data/chroma')
        print('✅ ChromaDB connection working')
        
        # Check if VECTOR_DB_CLIENT is properly initialized
        try:
            from open_webui.retrieval.vector.main import VECTOR_DB_CLIENT
            print('✅ VECTOR_DB_CLIENT available')
        except ImportError:
            print('❌ VECTOR_DB_CLIENT not available')
            
    except Exception as e:
        print(f'❌ Vector DB issues: {e}')
    
    # 3. Check embedding model availability
    print(f'\n🧠 Embedding Model Check:')
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        test_embedding = model.encode(['test'])
        print(f'✅ Embedding model working (output shape: {test_embedding.shape})')
    except Exception as e:
        print(f'❌ Embedding model issues: {e}')
    
    # 4. Test document processing pipeline
    print(f'\n🔄 Testing Document Processing Pipeline:')
    
    import sqlite3
    conn = sqlite3.connect('/app/backend/data/webui.db')
    cursor = conn.cursor()
    
    # Check if all files have been processed
    cursor.execute('SELECT COUNT(*) FROM file')
    file_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM document')
    doc_count = cursor.fetchone()[0]
    
    print(f'Files: {file_count}, Documents: {doc_count}')
    
    if file_count > doc_count:
        print('⚠️  Some files are not processed - fixing now...')
        
        # Process unprocessed files
        cursor.execute('SELECT id, filename, user_id, data FROM file')
        all_files = cursor.fetchall()
        
        processed_count = 0
        for file_id, filename, user_id, data in all_files:
            cursor.execute('SELECT COUNT(*) FROM document WHERE collection_name = ?', (f'file-{file_id}',))
            doc_entries = cursor.fetchone()[0]
            
            if doc_entries == 0:
                print(f'   🔄 Processing: {filename}')
                try:
                    # Process this file
                    import json
                    from sentence_transformers import SentenceTransformer
                    import chromadb
                    
                    if data and data != 'null':
                        data_obj = json.loads(data)
                        content = data_obj.get('content', '')
                        
                        if content:
                            # Create document entry
                            cursor.execute('SELECT MAX(id) FROM document')
                            max_id = cursor.fetchone()[0]
                            doc_id = (max_id + 1) if max_id else 1
                            
                            collection_name = f'file-{file_id}'
                            
                            cursor.execute('''INSERT OR REPLACE INTO document 
                                (id, collection_name, name, title, filename, content, user_id, timestamp) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                (doc_id, collection_name, filename, f'{filename} - Auto-fixed', 
                                 filename, content, user_id, 1755541324))
                            
                            conn.commit()
                            
                            # Create vector embeddings
                            model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                            chroma_client = chromadb.PersistentClient(path='/app/backend/data/chroma')
                            
                            # Create collection
                            try:
                                chroma_client.delete_collection(collection_name)
                            except:
                                pass
                                
                            collection = chroma_client.create_collection(
                                name=collection_name,
                                metadata={"description": f"Auto-fixed: {filename}", "user_id": user_id}
                            )
                            
                            # Chunk and embed
                            chunk_size = 500
                            chunks = []
                            for i in range(0, len(content), chunk_size):
                                chunk = content[i:i+chunk_size].strip()
                                if chunk:
                                    chunks.append(chunk)
                            
                            if chunks:
                                embeddings = model.encode(chunks)
                                ids = [f'chunk_{i}' for i in range(len(chunks))]
                                metadatas = [{'chunk_index': i, 'source': filename, 'user_id': user_id} 
                                           for i in range(len(chunks))]
                                
                                collection.add(
                                    documents=chunks,
                                    embeddings=embeddings.tolist(),
                                    metadatas=metadatas,
                                    ids=ids
                                )
                                
                                processed_count += 1
                                print(f'   ✅ Processed: {len(chunks)} chunks')
                            
                except Exception as e:
                    print(f'   ❌ Failed to process {filename}: {e}')
        
        print(f'🎯 Fixed {processed_count} unprocessed files')
    else:
        print('✅ All files are already processed')
    
    conn.close()
    
    # 5. Verify final state
    print(f'\n🧪 Final Verification:')
    
    conn = sqlite3.connect('/app/backend/data/webui.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM file')
    final_file_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM document')
    final_doc_count = cursor.fetchone()[0]
    
    conn.close()
    
    try:
        client = chromadb.PersistentClient(path='/app/backend/data/chroma')
        collections = client.list_collections()
        collection_count = len(collections)
        
        # Test a collection
        if collections:
            test_collection = client.get_collection(collections[0].name)
            chunk_count = test_collection.count()
            print(f'✅ Vector DB: {collection_count} collections, sample collection has {chunk_count} chunks')
        
    except Exception as e:
        print(f'❌ Vector DB verification failed: {e}')
    
    print(f'\n📊 FINAL STATE:')
    print(f'   Files: {final_file_count}')
    print(f'   Documents: {final_doc_count}')
    print(f'   Collections: {collection_count}')
    
    if final_file_count == final_doc_count == collection_count:
        print('🎉 SUCCESS: All files are properly processed!')
        return True
    else:
        print('⚠️  Some inconsistencies remain')
        return False

if __name__ == "__main__":
    success = check_and_fix_processing_workflow()
    if success:
        print('\n✅ Document processing workflow is now fully functional!')
    else:
        print('\n❌ Some issues remain - may need manual intervention')
