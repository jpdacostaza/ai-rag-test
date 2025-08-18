#!/usr/bin/env python3
"""
OpenWebUI Duplicate File Cleanup Tool
CAUTION: This tool can permanently delete files and vector collections
"""
import sqlite3
import chromadb
from collections import defaultdict

def create_duplicate_cleanup_tool():
    print('🧹 OPENWEBUI DUPLICATE CLEANUP TOOL')
    print('=' * 40)
    print('⚠️  WARNING: This tool can permanently delete data!')
    print('    Always backup your database before running cleanup')
    print()
    
    conn = sqlite3.connect('/app/backend/data/webui.db')
    cursor = conn.cursor()
    
    # Find duplicates by hash
    print('🔍 SCANNING FOR DUPLICATES...')
    cursor.execute('SELECT id, filename, hash, created_at FROM file ORDER BY created_at')
    files = cursor.fetchall()
    
    # Group by hash
    hash_groups = defaultdict(list)
    for file_id, filename, file_hash, created_at in files:
        if file_hash:  # Only process files with hashes
            hash_groups[file_hash].append({
                'id': file_id,
                'filename': filename,
                'created_at': created_at
            })
    
    duplicates_found = []
    for file_hash, file_list in hash_groups.items():
        if len(file_list) > 1:
            duplicates_found.append((file_hash, file_list))
    
    if not duplicates_found:
        print('✅ No duplicates found!')
        conn.close()
        return
    
    print(f'⚠️  Found {len(duplicates_found)} sets of duplicate files:')
    print()
    
    for i, (file_hash, file_list) in enumerate(duplicates_found, 1):
        print(f'📁 Duplicate Set {i} (hash: {file_hash[:16]}...):')
        
        # Sort by creation date (keep oldest)
        file_list.sort(key=lambda x: x['created_at'])
        
        keep_file = file_list[0]  # Keep the oldest one
        remove_files = file_list[1:]  # Remove newer duplicates
        
        print(f'   ✅ KEEP: {keep_file["filename"]} (ID: {keep_file["id"][:8]}...)')
        print(f'      Created: {keep_file["created_at"]}')
        
        for remove_file in remove_files:
            print(f'   ❌ REMOVE: {remove_file["filename"]} (ID: {remove_file["id"][:8]}...)')
            print(f'      Created: {remove_file["created_at"]}')
        print()
    
    # THIS IS A DEMO - ACTUAL CLEANUP CODE IS COMMENTED OUT FOR SAFETY
    print('🔧 CLEANUP OPERATIONS (DEMO MODE):')
    print('   The following operations would be performed:')
    print()
    
    for file_hash, file_list in duplicates_found:
        file_list.sort(key=lambda x: x['created_at'])
        remove_files = file_list[1:]
        
        for remove_file in remove_files:
            file_id = remove_file['id']
            collection_name = f'file-{file_id}'
            
            print(f'   📄 Delete from file table: {file_id}')
            print(f'   📝 Delete from document table: {collection_name}')
            print(f'   🗄️  Delete vector collection: {collection_name}')
            
            # ACTUAL CLEANUP CODE (COMMENTED FOR SAFETY):
            # cursor.execute('DELETE FROM file WHERE id = ?', (file_id,))
            # cursor.execute('DELETE FROM document WHERE collection_name = ?', (collection_name,))
            # 
            # try:
            #     client = chromadb.PersistentClient(path='/app/backend/data/chroma')
            #     client.delete_collection(collection_name)
            # except:
            #     pass
    
    # conn.commit()  # Uncomment to actually perform deletions
    conn.close()
    
    print()
    print('💡 TO ENABLE ACTUAL CLEANUP:')
    print('   1. Backup your database: cp /app/backend/data/webui.db webui.db.backup')
    print('   2. Uncomment the cleanup code in this script')
    print('   3. Run the script again')
    print()
    print('📊 SUMMARY:')
    total_duplicates = sum(len(file_list) - 1 for _, file_list in duplicates_found)
    print(f'   Total duplicate files that could be removed: {total_duplicates}')
    print(f'   Storage space that could be recovered: ~{total_duplicates * 21000} characters')

def show_duplicate_prevention_code():
    print('\n🛡️  DUPLICATE PREVENTION CODE:')
    print('=' * 35)
    print('''
# Example code to add to OpenWebUI file upload handler:

def check_duplicate_file(user_id, file_hash):
    """Check if file already exists for this user"""
    cursor.execute(
        'SELECT id, filename FROM file WHERE user_id = ? AND hash = ?', 
        (user_id, file_hash)
    )
    existing = cursor.fetchone()
    
    if existing:
        return {
            'duplicate': True,
            'existing_id': existing[0],
            'existing_filename': existing[1]
        }
    return {'duplicate': False}

# In the upload handler:
duplicate_check = check_duplicate_file(user_id, file_hash)
if duplicate_check['duplicate']:
    return {
        'error': 'File already exists',
        'message': f'You already uploaded "{duplicate_check["existing_filename"]}"',
        'options': ['replace', 'keep_both', 'cancel']
    }
''')

if __name__ == "__main__":
    create_duplicate_cleanup_tool()
    show_duplicate_prevention_code()
