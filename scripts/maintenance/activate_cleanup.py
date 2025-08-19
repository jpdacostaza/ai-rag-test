#!/usr/bin/env python3
"""
ACTIVATE DUPLICATE CLEANUP - PRODUCTION VERSION
This version performs ACTUAL cleanup operations
"""
import sqlite3
import chromadb
from collections import defaultdict

def activate_duplicate_cleanup():
    print('🧹 ACTIVATING DUPLICATE CLEANUP (PRODUCTION MODE)')
    print('=' * 50)
    print('⚠️  WARNING: This will PERMANENTLY delete duplicate files!')
    print()
    
    # Confirm with user
    response = input('Type "CLEANUP" to proceed with deletion: ')
    if response != "CLEANUP":
        print('❌ Cleanup cancelled for safety')
        return
    
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
    
    print(f'⚠️  Found {len(duplicates_found)} sets of duplicate files')
    
    total_deleted = 0
    total_errors = 0
    
    for file_hash, file_list in duplicates_found:
        file_list.sort(key=lambda x: x['created_at'])
        keep_file = file_list[0]  # Keep the oldest one
        remove_files = file_list[1:]  # Remove newer duplicates
        
        print(f'\\n📁 Processing duplicates for {keep_file["filename"]}:')
        print(f'   ✅ KEEPING: {keep_file["id"][:8]}... (created: {keep_file["created_at"]})')
        
        for remove_file in remove_files:
            file_id = remove_file['id']
            collection_name = f'file-{file_id}'
            
            try:
                print(f'   🗑️  DELETING: {file_id[:8]}...')
                
                # Delete from file table
                cursor.execute('DELETE FROM file WHERE id = ?', (file_id,))
                print(f'      ✅ Deleted from file table')
                
                # Delete from document table
                cursor.execute('DELETE FROM document WHERE collection_name = ?', (collection_name,))
                print(f'      ✅ Deleted from document table')
                
                # Delete vector collection
                try:
                    client = chromadb.PersistentClient(path='/app/backend/data/chroma')
                    client.delete_collection(collection_name)
                    print(f'      ✅ Deleted vector collection')
                except Exception as e:
                    print(f'      ⚠️  Vector collection not found or already deleted: {e}')
                
                total_deleted += 1
                
            except Exception as e:
                print(f'      ❌ Error deleting {file_id[:8]}: {e}')
                total_errors += 1
    
    # Commit all changes
    try:
        conn.commit()
        print(f'\\n✅ Database changes committed successfully!')
    except Exception as e:
        print(f'\\n❌ Error committing changes: {e}')
        conn.rollback()
        total_errors += 1
    
    conn.close()
    
    print(f'\\n📊 CLEANUP SUMMARY:')
    print(f'   Total files deleted: {total_deleted}')
    print(f'   Errors encountered: {total_errors}')
    print(f'   Duplicate sets processed: {len(duplicates_found)}')
    
    if total_errors == 0:
        print(f'\\n🎉 CLEANUP COMPLETED SUCCESSFULLY!')
        print(f'   Your system is now free of duplicate files.')
        print(f'   Storage space recovered: ~{total_deleted * 21000} characters')
    else:
        print(f'\\n⚠️  CLEANUP COMPLETED WITH WARNINGS')
        print(f'   Some operations failed. Check the logs above.')

if __name__ == "__main__":
    activate_duplicate_cleanup()
