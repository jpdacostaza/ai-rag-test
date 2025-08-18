#!/usr/bin/env python3
"""
Fix CV processing by creating document entries for vector embedding
"""
import sys
sys.path.append('/app')
import sqlite3
import json

def process_cv_file():
    """Process the CV file to create document entry for RAG"""
    try:
        conn = sqlite3.connect('/app/backend/data/webui.db')
        cursor = conn.cursor()
        
        # Get CV file data
        cursor.execute("SELECT id, user_id, filename, data FROM file WHERE filename LIKE '%Da Costa%' LIMIT 1")
        cv_file = cursor.fetchone()
        
        if cv_file:
            file_id, user_id, filename, data = cv_file
            print(f'Processing: {filename} (ID: {file_id})')
            
            # Extract content
            data_obj = json.loads(data)
            content = data_obj.get('content', '')
            
            if content:
                collection_name = f'file-{file_id}'
                
                # Generate a new integer ID for the document table
                cursor.execute('SELECT MAX(id) FROM document')
                max_id = cursor.fetchone()[0]
                doc_id = (max_id + 1) if max_id else 1
                
                # Insert document entry
                cursor.execute('''INSERT OR REPLACE INTO document 
                    (id, collection_name, name, title, filename, content, user_id, timestamp) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (doc_id, collection_name, filename, 'Juan-Pierre Da Costa CV 2025', 
                     filename, content, user_id, 1755541324))
                
                conn.commit()
                
                # Verify
                cursor.execute('SELECT COUNT(*) FROM document')
                doc_count = cursor.fetchone()[0]
                print(f'✅ Document created successfully!')
                print(f'📊 Total documents: {doc_count}')
                print(f'📂 Collection name: {collection_name}')
                print(f'📄 Content length: {len(content)} characters')
                
                return collection_name
            else:
                print('❌ No content found in file data')
        else:
            print('❌ CV file not found')
        
        conn.close()
        
    except Exception as e:
        print(f'❌ Processing error: {e}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    collection_name = process_cv_file()
    if collection_name:
        print(f'\n🎯 Next step: Vector embeddings need to be created for collection: {collection_name}')
