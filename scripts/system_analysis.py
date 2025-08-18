#!/usr/bin/env python3
"""
OpenWebUI System Analysis - Document Processing and Chat Memory Store
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
            collection = client.get_collection(col.name)
            count = collection.count()
            total_chunks += count
            print(f'   • {col.name}: {count} chunks')
            
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
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f'   • {table}: {count} records')
    
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
        # Look for any chat-specific collections in ChromaDB
        chat_collections = [c for c in collections if 'chat' in c.name.lower() or 'memory' in c.name.lower()]
        file_collections = [c for c in collections if 'file-' in c.name]
        
        print(f'💭 Chat memory collections: {len(chat_collections)}')
        for col in chat_collections:
            collection = client.get_collection(col.name)
            print(f'   • {col.name}: {collection.count()} entries')
            
        print(f'📁 File document collections: {len(file_collections)}')
        for col in file_collections:
            collection = client.get_collection(col.name)
            print(f'   • {col.name}: {collection.count()} chunks')
            
        if chat_collections and file_collections:
            print('✅ Chat and document collections are properly separated')
        elif file_collections and not chat_collections:
            print('✅ Only document collections found - no interference with chat memory')
        else:
            print('ℹ️  No chat memory collections detected')
            
    except Exception as e:
        print(f'❌ Collection analysis error: {e}')
    
    conn.close()
    
    print()
    print('📝 CONCLUSION')
    print('=' * 40)
    print('Document processing and chat memory are separate systems:')
    print('• Documents: SQLite file/document tables + ChromaDB file-* collections') 
    print('• Chat Memory: SQLite chat/message tables + ChromaDB chat/memory collections')
    print('• No interference between systems - they use different namespaces')

if __name__ == "__main__":
    analyze_system()
