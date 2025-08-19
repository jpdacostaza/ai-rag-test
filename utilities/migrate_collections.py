#!/usr/bin/env python3
"""
Migration script to convert file-based ChromaDB collections to user-based collections.

This script:
1. Identifies all file-based collections (file-{file_id})
2. Groups documents by user_id from metadata
3. Creates user-based collections (user-{user_id}-documents)
4. Migrates documents with proper metadata
5. Deletes old file-based collections
"""

import chromadb
import sqlite3
import json
from typing import Dict, List, Set

def get_file_user_mapping():
    """Get mapping of file_id to user_id from OpenWebUI database."""
    conn = sqlite3.connect('/app/backend/data/webui.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, user_id, filename FROM file')
    files = cursor.fetchall()
    
    file_to_user = {}
    for file_id, user_id, filename in files:
        file_to_user[file_id] = {
            'user_id': user_id,
            'filename': filename
        }
    
    conn.close()
    return file_to_user

def migrate_collections():
    """Migrate file-based collections to user-based collections."""
    
    # Connect to ChromaDB
    client = chromadb.PersistentClient(path='/app/backend/data/vector_db')
    
    # Get file to user mapping
    file_to_user = get_file_user_mapping()
    print(f"Found {len(file_to_user)} files in database")
    
    # Get all collections
    collections = client.list_collections()
    file_collections = [str(c) for c in collections if str(c).startswith('file-')]
    
    print(f"Found {len(file_collections)} file-based collections to migrate")
    
    # Group documents by user
    user_documents = {}  # user_id -> list of documents
    
    for collection_name in file_collections:
        print(f"Processing collection: {collection_name}")
        
        # Extract file_id from collection name
        file_id = collection_name.replace('file-', '')
        
        # Get user_id for this file
        if file_id not in file_to_user:
            print(f"  WARNING: File {file_id} not found in database, skipping")
            continue
            
        user_info = file_to_user[file_id]
        user_id = user_info['user_id']
        
        # Get the collection
        try:
            collection = client.get_collection(collection_name)
            
            # Get all documents from this collection
            result = collection.get(include=['documents', 'metadatas', 'embeddings'])
            
            if not result or not result['documents']:
                print(f"  No documents found in {collection_name}")
                continue
                
            # Initialize user documents list if needed
            if user_id not in user_documents:
                user_documents[user_id] = {
                    'documents': [],
                    'metadatas': [],
                    'embeddings': [],
                    'ids': []
                }
            
            # Add documents to user collection
            for i, doc in enumerate(result['documents']):
                metadata = result['metadatas'][i] if result['metadatas'] else {}
                embedding = result['embeddings'][i] if result['embeddings'] else None
                doc_id = result['ids'][i] if result['ids'] else f"migrated_{file_id}_{i}"
                
                # Ensure file_id is in metadata
                if 'file_id' not in metadata:
                    metadata['file_id'] = file_id
                    
                # Ensure user_id is in metadata  
                if 'created_by' not in metadata:
                    metadata['created_by'] = user_id
                
                user_documents[user_id]['documents'].append(doc)
                user_documents[user_id]['metadatas'].append(metadata)
                user_documents[user_id]['embeddings'].append(embedding)
                user_documents[user_id]['ids'].append(doc_id)
            
            print(f"  Migrated {len(result['documents'])} documents from {collection_name}")
            
        except Exception as e:
            print(f"  ERROR processing {collection_name}: {e}")
    
    # Create user-based collections
    print(f"\nCreating user-based collections for {len(user_documents)} users")
    
    for user_id, data in user_documents.items():
        user_collection_name = f"user-{user_id}-documents"
        print(f"Creating collection: {user_collection_name}")
        
        try:
            # Create or get user collection
            user_collection = client.get_or_create_collection(
                name=user_collection_name,
                metadata={"description": f"Documents for user {user_id}"}
            )
            
            # Add all documents to user collection
            if data['embeddings'] and all(emb is not None for emb in data['embeddings']):
                user_collection.add(
                    documents=data['documents'],
                    metadatas=data['metadatas'],
                    embeddings=data['embeddings'],
                    ids=data['ids']
                )
            else:
                # If embeddings are missing, add without them (ChromaDB will generate)
                user_collection.add(
                    documents=data['documents'],
                    metadatas=data['metadatas'],
                    ids=data['ids']
                )
            
            print(f"  Added {len(data['documents'])} documents to {user_collection_name}")
            
        except Exception as e:
            print(f"  ERROR creating user collection {user_collection_name}: {e}")
    
    # Delete old file-based collections
    print(f"\nDeleting {len(file_collections)} old file-based collections")
    
    for collection_name in file_collections:
        try:
            client.delete_collection(collection_name)
            print(f"  Deleted {collection_name}")
        except Exception as e:
            print(f"  ERROR deleting {collection_name}: {e}")
    
    print("\nMigration completed!")
    
    # Verify migration
    print("\nVerification:")
    remaining_collections = client.list_collections()
    user_colls = [str(c) for c in remaining_collections if str(c).startswith('user-') and str(c).endswith('-documents')]
    file_colls = [str(c) for c in remaining_collections if str(c).startswith('file-')]
    
    print(f"  User-based document collections: {len(user_colls)}")
    print(f"  Remaining file-based collections: {len(file_colls)}")
    
    for user_coll in user_colls:
        try:
            coll = client.get_collection(user_coll)
            count = coll.count()
            print(f"    {user_coll}: {count} documents")
        except Exception as e:
            print(f"    {user_coll}: ERROR - {e}")

if __name__ == "__main__":
    migrate_collections()
