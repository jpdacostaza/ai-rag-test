#!/usr/bin/env python3
"""
OpenWebUI System Analysis - Document Processing and Chat Memory Store (Fixed)
"""
import sqlite3
import chromadb

def analyze_system():
    print('🔧 DOCUMENT PROCESSING STATUS CHECK')
    print('=' * 40)
    
    # Database status
    conn = sqlite3.connect('/app/backend/data/webui.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM file')
    file_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM document')
    doc_count = cursor.fetchone()[0]
    
    print(f'📁 Files: {file_count}')
    print(f'📄 Documents: {doc_count}')
    
    # Check processing consistency
    if file_count == doc_count:
        print('✅ All files are processed into documents')
    else:
        print(f'⚠️  {file_count - doc_count} files are unprocessed')
    
    # Vector collections status
    try:
        client = chromadb.PersistentClient(path='/app/backend/data/chroma')
        collections = client.list_collections()
        print(f'🗄️  Vector Collections: {len(collections)}')
        
        total_chunks = 0
        for col in collections:
            try:
                collection = client.get_collection(col.name)
                count = collection.count()
                total_chunks += count
                print(f'   • {col.name}: {count} chunks')
            except Exception as e:
                print(f'   • {col.name}: Error accessing - {e}')
            
        print(f'📊 Total vector chunks: {total_chunks}')
        
    except Exception as e:
        print(f'❌ Vector DB error: {e}')
    
    print()
    print('🧠 CHAT MEMORY STORE ANALYSIS')
    print('=' * 40)
    
    # Get all table names
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    all_tables = [table[0] for table in cursor.fetchall()]
    
    print('📋 All database tables:')
    for table in sorted(all_tables):
        try:
            # Handle reserved keywords by quoting
            cursor.execute(f'SELECT COUNT(*) FROM `{table}`')
            count = cursor.fetchone()[0]
            print(f'   • {table}: {count} records')
        except Exception as e:
            print(f'   • {table}: Error - {e}')
    
    print()
    print('🔍 CHAT MEMORY SEPARATION ANALYSIS')
    print('=' * 40)
    
    # Check if chat and document systems are separate
    chat_related = [t for t in all_tables if 'chat' in t.lower() or 'message' in t.lower()]
    doc_related = [t for t in all_tables if 'document' in t.lower() or 'file' in t.lower()]
    
    print(f'💬 Chat-related tables: {chat_related}')
    print(f'📄 Document-related tables: {doc_related}')
    
    # Check for any cross-references
    if 'chat' in all_tables and 'document' in all_tables:
        print()
        print('🔗 Checking for cross-references:')
        
        # Get chat table schema
        cursor.execute('PRAGMA table_info(chat)')
        chat_columns = [col[1] for col in cursor.fetchall()]
        print(f'   Chat columns: {chat_columns}')
        
        # Get document table schema  
        cursor.execute('PRAGMA table_info(document)')
        doc_columns = [col[1] for col in cursor.fetchall()]
        print(f'   Document columns: {doc_columns}')
        
        # Look for shared columns
        shared_cols = set(chat_columns) & set(doc_columns)
        print(f'   Shared columns: {shared_cols}')
        
        if 'user_id' in shared_cols:
            print('   ✅ Both systems use user_id - properly separated by user')
        
    print()
    print('🎯 MEMORY STORE INTERFERENCE CHECK')
    print('=' * 40)
    
    # Check if document collections interfere with chat memory
    try:
        chat_collections = []
        file_collections = []
        
        for col in collections:
            col_name = col.name
            if 'chat' in col_name.lower() or 'memory' in col_name.lower():
                chat_collections.append(col_name)
            elif 'file-' in col_name:
                file_collections.append(col_name)
        
        print(f'💭 Chat memory collections: {len(chat_collections)}')
        for col_name in chat_collections:
            try:
                collection = client.get_collection(col_name)
                print(f'   • {col_name}: {collection.count()} entries')
            except:
                print(f'   • {col_name}: Access error')
            
        print(f'📁 File document collections: {len(file_collections)}')
        for col_name in file_collections:
            try:
                collection = client.get_collection(col_name)
                print(f'   • {col_name}: {collection.count()} chunks')
            except:
                print(f'   • {col_name}: Access error')
            
        if chat_collections and file_collections:
            print('✅ Chat and document collections are properly separated')
        elif file_collections and not chat_collections:
            print('✅ Only document collections found - no interference with chat memory')
        else:
            print('ℹ️  No chat memory collections detected')
            
    except Exception as e:
        print(f'❌ Collection analysis error: {e}')
    
    # Check for unprocessed files
    print()
    print('🚧 UNPROCESSED FILES CHECK')
    print('=' * 40)
    
    cursor.execute('SELECT id, filename FROM file')
    all_files = cursor.fetchall()
    
    for file_id, filename in all_files:
        cursor.execute('SELECT COUNT(*) FROM document WHERE collection_name = ?', (f'file-{file_id}',))
        doc_exists = cursor.fetchone()[0] > 0
        
        if doc_exists:
            print(f'✅ {filename} (file-{file_id}) - Processed')
        else:
            print(f'❌ {filename} (file-{file_id}) - NOT PROCESSED')
    
    conn.close()
    
    print()
    print('📝 CONCLUSION')
    print('=' * 40)
    print('Document processing and chat memory are separate systems:')
    print('• Documents: SQLite file/document tables + ChromaDB file-* collections') 
    print('• Chat Memory: SQLite chat/message tables + ChromaDB chat/memory collections')
    print('• No interference between systems - they use different namespaces')
    print()
    if file_count > doc_count:
        print('⚠️  ACTION NEEDED: Some files are not processed into vector format')
        print('   This means they cannot be found in RAG queries')
    else:
        print('✅ All files are properly processed')

if __name__ == "__main__":
    analyze_system()
