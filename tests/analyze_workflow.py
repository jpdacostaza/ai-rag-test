#!/usr/bin/env python3
"""
Comprehensive analysis of OpenWebUI's document processing workflow
"""
import sys
sys.path.append('/app')
import sqlite3
import chromadb
import json

def analyze_workflow():
    """Analyze the current document processing workflow"""
    print('🔍 DOCUMENT PROCESSING WORKFLOW ANALYSIS')
    print('=' * 50)
    
    # Database analysis
    conn = sqlite3.connect('/app/backend/data/webui.db')
    cursor = conn.cursor()
    
    # Check current state
    cursor.execute('SELECT COUNT(*) FROM file')
    file_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM document')
    doc_count = cursor.fetchone()[0]
    
    print(f'📊 Current State:')
    print(f'   Files: {file_count}')
    print(f'   Documents: {doc_count}')
    
    # Analyze file processing status
    cursor.execute('SELECT id, filename, user_id FROM file')
    files = cursor.fetchall()
    
    print(f'\n📁 File Processing Status:')
    processed_files = 0
    unprocessed_files = 0
    
    for file_id, filename, user_id in files:
        cursor.execute('SELECT COUNT(*) FROM document WHERE collection_name = ?', (f'file-{file_id}',))
        doc_entries = cursor.fetchone()[0]
        
        if doc_entries > 0:
            processed_files += 1
            status = '✅ PROCESSED'
        else:
            unprocessed_files += 1
            status = '❌ NOT PROCESSED'
            
        print(f'   {filename}: {status}')
        print(f'     File ID: {file_id}')
        print(f'     User ID: {user_id}')
        print(f'     Document entries: {doc_entries}')
    
    print(f'\n📈 Processing Summary:')
    print(f'   Processed files: {processed_files}/{file_count}')
    print(f'   Unprocessed files: {unprocessed_files}/{file_count}')
    
    # Vector database analysis
    print(f'\n🗄️ Vector Database Analysis:')
    try:
        client = chromadb.PersistentClient(path='/app/backend/data/chroma')
        
        # Get collections (handling API changes)
        try:
            collections = client.list_collections()
            collection_names = [c.name for c in collections]
        except AttributeError:
            # Older API
            collection_names = client.list_collections()
        
        print(f'   Collections: {len(collection_names)}')
        
        for col_name in collection_names:
            try:
                collection = client.get_collection(col_name)
                count = collection.count()
                print(f'     {col_name}: {count} chunks')
                
                # Test if collection is queryable
                if count > 0:
                    try:
                        result = collection.peek(1)
                        if result and result.get('documents'):
                            doc_preview = result['documents'][0][:100]
                            print(f'       Preview: {doc_preview}...')
                    except Exception as e:
                        print(f'       Query test failed: {e}')
                        
            except Exception as e:
                print(f'     Error accessing {col_name}: {e}')
                
    except Exception as e:
        print(f'   Vector DB connection failed: {e}')
    
    # Workflow assessment
    print(f'\n🎯 WORKFLOW ASSESSMENT:')
    
    if unprocessed_files == 0:
        print('✅ All files are processed into documents')
    else:
        print(f'⚠️  {unprocessed_files} files need processing')
    
    if len(collection_names) == processed_files:
        print('✅ Vector collections match processed files')
    else:
        print(f'⚠️  Vector collections ({len(collection_names)}) != processed files ({processed_files})')
    
    # Check if automatic processing is working
    print(f'\n🔧 AUTOMATIC PROCESSING STATUS:')
    
    if file_count > 0 and doc_count == 0:
        print('❌ BROKEN: No files are being processed automatically')
        print('   Files are uploaded but not converted to documents')
        print('   Vector embeddings are not created')
    elif unprocessed_files > 0:
        print('⚠️  PARTIAL: Some files are not being processed automatically')
        print('   New uploads may not trigger vector processing')
    else:
        print('✅ WORKING: All files appear to be processed automatically')
    
    # Recommendations
    print(f'\n💡 RECOMMENDATIONS:')
    
    if unprocessed_files > 0:
        print('1. 🔧 Fix automatic processing for new uploads')
        print('2. 📝 Manually process existing unprocessed files')
        print('3. 🧪 Test new file upload to verify auto-processing')
    
    if len(collection_names) != processed_files:
        print('4. 🗄️ Sync vector collections with document entries')
    
    print('5. 🚀 Create automation script for future file processing')
    
    conn.close()

if __name__ == "__main__":
    analyze_workflow()
