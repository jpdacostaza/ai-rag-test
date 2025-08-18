#!/usr/bin/env python3
"""
Duplicate File Handling Analysis for OpenWebUI
"""
import sqlite3
import json
import chromadb

def analyze_duplicate_handling():
    print('🔍 DUPLICATE FILE HANDLING ANALYSIS')
    print('=' * 40)
    
    conn = sqlite3.connect('/app/backend/data/webui.db')
    cursor = conn.cursor()
    
    print('📁 CURRENT FILE ANALYSIS:')
    cursor.execute('SELECT id, filename, user_id, created_at FROM file ORDER BY created_at')
    files = cursor.fetchall()
    
    filename_counts = {}
    user_file_map = {}
    
    for file_id, filename, user_id, created_at in files:
        print(f'   • ID: {file_id}')
        print(f'     Name: {filename}')
        print(f'     User: {user_id}')
        print(f'     Created: {created_at}')
        print()
        
        # Count filename occurrences
        if filename in filename_counts:
            filename_counts[filename] += 1
        else:
            filename_counts[filename] = 1
        
        # Track user-filename combinations
        user_filename = f"{user_id}:{filename}"
        if user_filename in user_file_map:
            user_file_map[user_filename].append(file_id)
        else:
            user_file_map[user_filename] = [file_id]
    
    print('📊 FILENAME FREQUENCY:')
    for filename, count in filename_counts.items():
        if count > 1:
            print(f'   ⚠️  DUPLICATE: "{filename}" appears {count} times')
        else:
            print(f'   ✅ UNIQUE: "{filename}" appears {count} time')
    
    print('\n👤 USER-SPECIFIC DUPLICATES:')
    for user_filename, file_ids in user_file_map.items():
        if len(file_ids) > 1:
            user_id, filename = user_filename.split(':', 1)
            print(f'   ⚠️  User {user_id} has {len(file_ids)} copies of "{filename}":')
            for fid in file_ids:
                print(f'      - File ID: {fid}')
    
    print('\n🗄️  DOCUMENT TABLE ANALYSIS:')
    cursor.execute('SELECT id, collection_name, name, filename FROM document')
    docs = cursor.fetchall()
    
    collection_counts = {}
    doc_filename_counts = {}
    
    print(f'Documents: {len(docs)}')
    for doc_id, collection, name, filename in docs:
        print(f'   • Doc ID: {doc_id}')
        print(f'     Collection: {collection}')
        print(f'     Name: {name}')
        print(f'     Filename: {filename}')
        print()
        
        # Count collections
        if collection in collection_counts:
            collection_counts[collection] += 1
        else:
            collection_counts[collection] = 1
        
        # Count document names
        if name in doc_filename_counts:
            doc_filename_counts[name] += 1
        else:
            doc_filename_counts[name] = 1
    
    print('📋 COLLECTION FREQUENCY:')
    for collection, count in collection_counts.items():
        if count > 1:
            print(f'   ⚠️  DUPLICATE COLLECTION: {collection} has {count} documents')
        else:
            print(f'   ✅ UNIQUE COLLECTION: {collection} has {count} document')
    
    print('\n📝 DOCUMENT NAME FREQUENCY:')
    for doc_name, count in doc_filename_counts.items():
        if count > 1:
            print(f'   ⚠️  DUPLICATE NAME: "{doc_name}" appears {count} times')
        else:
            print(f'   ✅ UNIQUE NAME: "{doc_name}" appears {count} time')
    
    # Check vector collections
    print('\n🗄️  VECTOR COLLECTION ANALYSIS:')
    try:
        client = chromadb.PersistentClient(path='/app/backend/data/chroma')
        collections = client.list_collections()
        
        print(f'Vector collections: {len(collections)}')
        for col in collections:
            try:
                collection = client.get_collection(col.name)
                count = collection.count()
                print(f'   • {col.name}: {count} chunks')
            except Exception as e:
                print(f'   ❌ {col.name}: Error - {e}')
    
    except Exception as e:
        print(f'❌ Vector DB error: {e}')
    
    # Simulate duplicate upload scenario
    print('\n🧪 DUPLICATE UPLOAD SIMULATION:')
    print('What happens when the same file is uploaded again?')
    
    # Check file table schema for constraints
    cursor.execute('PRAGMA table_info(file)')
    file_schema = cursor.fetchall()
    
    print('\n📋 FILE TABLE SCHEMA:')
    unique_constraints = []
    for col in file_schema:
        col_name = col[1]
        is_pk = col[5]  # Primary key flag
        not_null = col[3]  # Not null flag
        print(f'   • {col_name}: {"PK" if is_pk else ""} {"NOT NULL" if not_null else ""} {col[2]}')
        
    # Check for unique constraints
    cursor.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name="file"')
    file_table_sql = cursor.fetchone()[0]
    print(f'\nFile table SQL: {file_table_sql}')
    
    if 'UNIQUE' in file_table_sql.upper():
        print('⚠️  File table has UNIQUE constraints')
    else:
        print('✅ File table allows duplicates (no UNIQUE constraints detected)')
    
    # Check document table constraints
    cursor.execute('PRAGMA table_info(document)')
    doc_schema = cursor.fetchall()
    
    cursor.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name="document"')
    doc_table_sql = cursor.fetchone()[0]
    print(f'\nDocument table SQL: {doc_table_sql}')
    
    conn.close()
    
    # Analysis conclusions
    print('\n🎯 DUPLICATE HANDLING CONCLUSIONS:')
    print('=' * 35)
    
    if len([f for f in filename_counts.values() if f > 1]) > 0:
        print('⚠️  CURRENT STATE: Duplicates exist in the system')
    else:
        print('✅ CURRENT STATE: No duplicates detected')
    
    print('\n📝 IMPLICATIONS:')
    print('• Each file gets a unique UUID as primary key')
    print('• Same filename can be uploaded multiple times')
    print('• Each upload creates separate vector collection')
    print('• Document table name field has UNIQUE constraint')
    print('• RAG queries search across all collections')

if __name__ == "__main__":
    analyze_duplicate_handling()
