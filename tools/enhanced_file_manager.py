#!/usr/bin/env python3
"""
OpenWebUI Enhanced File Upload Handler with Duplicate Prevention
This implements smart duplicate detection and user choice options
"""
import sqlite3
import hashlib
import json
from typing import Dict, List, Optional, Tuple
import chromadb
from datetime import datetime

class DuplicateFileManager:
    def __init__(self, db_path: str = '/app/backend/data/webui.db', 
                 chroma_path: str = '/app/backend/data/chroma'):
        self.db_path = db_path
        self.chroma_path = chroma_path
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def check_duplicate_file(self, user_id: str, file_hash: str, filename: str) -> Dict:
        """
        Check if file already exists for this user
        Returns duplicate info with options for user
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check for exact hash match
        cursor.execute('''
            SELECT id, filename, created_at 
            FROM file 
            WHERE user_id = ? AND hash = ?
            ORDER BY created_at DESC
        ''', (user_id, file_hash))
        
        exact_matches = cursor.fetchall()
        
        # Check for filename matches (potential updates)
        cursor.execute('''
            SELECT id, filename, hash, created_at 
            FROM file 
            WHERE user_id = ? AND filename = ? AND hash != ?
            ORDER BY created_at DESC
        ''', (user_id, filename, file_hash))
        
        filename_matches = cursor.fetchall()
        
        conn.close()
        
        result = {
            'has_exact_duplicate': len(exact_matches) > 0,
            'has_filename_match': len(filename_matches) > 0,
            'exact_matches': exact_matches,
            'filename_matches': filename_matches,
            'recommendations': []
        }
        
        if exact_matches:
            latest_exact = exact_matches[0]
            result['recommendations'].extend([
                {
                    'action': 'skip',
                    'title': 'Skip Upload',
                    'description': f'File identical to existing upload from {latest_exact[2]}',
                    'existing_id': latest_exact[0]
                },
                {
                    'action': 'keep_both',
                    'title': 'Upload Anyway',
                    'description': 'Create duplicate copy (not recommended)',
                    'warning': 'Will double storage usage and create duplicate results'
                }
            ])
        
        if filename_matches:
            latest_filename = filename_matches[0]
            result['recommendations'].extend([
                {
                    'action': 'replace',
                    'title': 'Replace Existing',
                    'description': f'Replace previous version from {latest_filename[3]}',
                    'existing_id': latest_filename[0],
                    'warning': 'Previous version will be permanently deleted'
                },
                {
                    'action': 'version',
                    'title': 'Keep as New Version',
                    'description': 'Upload as updated version alongside existing',
                    'existing_id': latest_filename[0]
                }
            ])
        
        return result
    
    def handle_upload_decision(self, user_id: str, filename: str, file_content: bytes, 
                             action: str, existing_id: Optional[str] = None) -> Dict:
        """
        Handle user's decision about duplicate file upload
        """
        file_hash = self.calculate_file_hash(file_content)
        
        if action == 'skip':
            return {
                'success': True,
                'action': 'skipped',
                'message': 'Upload skipped - using existing file',
                'file_id': existing_id
            }
        
        elif action == 'replace':
            return self._replace_existing_file(existing_id, filename, file_content, file_hash, user_id)
        
        elif action == 'version':
            return self._upload_as_version(filename, file_content, file_hash, user_id)
        
        elif action == 'keep_both':
            return self._upload_duplicate(filename, file_content, file_hash, user_id)
        
        else:
            return self._upload_new(filename, file_content, file_hash, user_id)
    
    def _replace_existing_file(self, existing_id: str, filename: str, 
                              file_content: bytes, file_hash: str, user_id: str) -> Dict:
        """Replace an existing file and update its vector collection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get existing file info
            cursor.execute('SELECT collection_name FROM document WHERE collection_name = ?', 
                         (f'file-{existing_id}',))
            existing_doc = cursor.fetchone()
            
            # Update file table
            cursor.execute('''
                UPDATE file 
                SET hash = ?, data = ?, updated_at = ?
                WHERE id = ?
            ''', (file_hash, json.dumps({'content': file_content.decode('utf-8', errors='ignore')}), 
                  int(datetime.now().timestamp()), existing_id))
            
            # Update document table
            content = file_content.decode('utf-8', errors='ignore')
            cursor.execute('''
                UPDATE document 
                SET content = ?, timestamp = ?
                WHERE collection_name = ?
            ''', (content, int(datetime.now().timestamp()), f'file-{existing_id}'))
            
            conn.commit()
            
            # Update vector collection
            self._update_vector_collection(f'file-{existing_id}', content, filename, user_id)
            
            return {
                'success': True,
                'action': 'replaced',
                'message': f'Successfully replaced existing file',
                'file_id': existing_id
            }
            
        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'action': 'error',
                'message': f'Failed to replace file: {str(e)}'
            }
        finally:
            conn.close()
    
    def _upload_as_version(self, filename: str, file_content: bytes, 
                          file_hash: str, user_id: str) -> Dict:
        """Upload as a new version with versioned filename"""
        import uuid
        
        # Create version suffix
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) == 2:
            versioned_filename = f"{name_parts[0]}_v{timestamp}.{name_parts[1]}"
        else:
            versioned_filename = f"{filename}_v{timestamp}"
        
        return self._upload_new(versioned_filename, file_content, file_hash, user_id)
    
    def _upload_duplicate(self, filename: str, file_content: bytes, 
                         file_hash: str, user_id: str) -> Dict:
        """Upload as duplicate (not recommended)"""
        result = self._upload_new(filename, file_content, file_hash, user_id)
        if result['success']:
            result['warning'] = 'Duplicate file uploaded - may cause redundant search results'
        return result
    
    def _upload_new(self, filename: str, file_content: bytes, 
                   file_hash: str, user_id: str) -> Dict:
        """Upload as completely new file"""
        import uuid
        
        file_id = str(uuid.uuid4())
        content = file_content.decode('utf-8', errors='ignore')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Insert into file table
            cursor.execute('''
                INSERT INTO file (id, user_id, filename, hash, data, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_id, user_id, filename, file_hash, 
                  json.dumps({'content': content}), int(datetime.now().timestamp())))
            
            # Insert into document table
            collection_name = f'file-{file_id}'
            cursor.execute('''
                INSERT INTO document (collection_name, name, title, filename, content, user_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (collection_name, filename, f'{filename} - Uploaded', 
                  filename, content, user_id, int(datetime.now().timestamp())))
            
            conn.commit()
            
            # Create vector collection
            self._create_vector_collection(collection_name, content, filename, user_id)
            
            return {
                'success': True,
                'action': 'uploaded',
                'message': f'Successfully uploaded {filename}',
                'file_id': file_id
            }
            
        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'action': 'error',
                'message': f'Failed to upload file: {str(e)}'
            }
        finally:
            conn.close()
    
    def _create_vector_collection(self, collection_name: str, content: str, 
                                 filename: str, user_id: str) -> None:
        """Create vector embeddings for new content"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Initialize embedding model
            model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            
            # Connect to ChromaDB
            client = chromadb.PersistentClient(path=self.chroma_path)
            
            # Delete existing collection if it exists
            try:
                client.delete_collection(collection_name)
            except:
                pass
            
            # Create new collection
            collection = client.create_collection(
                name=collection_name,
                metadata={"description": f"Document: {filename}", "user_id": user_id}
            )
            
            # Chunk content
            chunk_size = 500
            chunks = []
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i+chunk_size].strip()
                if chunk:
                    chunks.append(chunk)
            
            if chunks:
                # Generate embeddings
                embeddings = model.encode(chunks)
                
                # Create metadata
                ids = [f'chunk_{i}' for i in range(len(chunks))]
                metadatas = [{'chunk_index': i, 'source': filename, 'user_id': user_id} 
                           for i in range(len(chunks))]
                
                # Add to collection
                collection.add(
                    documents=chunks,
                    embeddings=embeddings.tolist(),
                    metadatas=metadatas,
                    ids=ids
                )
                
        except Exception as e:
            print(f"Error creating vector collection: {e}")
    
    def _update_vector_collection(self, collection_name: str, content: str, 
                                 filename: str, user_id: str) -> None:
        """Update existing vector collection with new content"""
        # For updates, we delete and recreate the collection
        self._create_vector_collection(collection_name, content, filename, user_id)

def demo_duplicate_prevention():
    """Demonstrate the duplicate prevention system"""
    print('🛡️ DUPLICATE PREVENTION SYSTEM DEMO')
    print('=' * 40)
    
    manager = DuplicateFileManager()
    
    # Simulate checking for duplicates of your CV
    user_id = "e7e39ee3-b886-4f92-8fb2-fbeb524fe5ce"
    cv_hash = "5c7ae324b98140ff1de55e81437c3ac708cd38867c4e4b072c27ee4071d55479"
    filename = "J.P. Da Costa 2025 - Resume.pdf"
    
    print(f'👤 User: {user_id}')
    print(f'📄 File: {filename}')
    print(f'🔑 Hash: {cv_hash[:16]}...')
    print()
    
    # Check for duplicates
    duplicate_info = manager.check_duplicate_file(user_id, cv_hash, filename)
    
    print('🔍 DUPLICATE CHECK RESULTS:')
    print(f'   Exact duplicates found: {duplicate_info["has_exact_duplicate"]}')
    print(f'   Filename matches found: {duplicate_info["has_filename_match"]}')
    
    if duplicate_info['exact_matches']:
        print('\n📁 EXACT DUPLICATES:')
        for match in duplicate_info['exact_matches']:
            print(f'   • ID: {match[0][:8]}... | File: {match[1]} | Created: {match[2]}')
    
    if duplicate_info['filename_matches']:
        print('\n📝 FILENAME MATCHES:')
        for match in duplicate_info['filename_matches']:
            print(f'   • ID: {match[0][:8]}... | Hash: {match[2][:8]}... | Created: {match[3]}')
    
    print('\n🎯 RECOMMENDED ACTIONS:')
    for i, rec in enumerate(duplicate_info['recommendations'], 1):
        print(f'   {i}. {rec["title"]}')
        print(f'      {rec["description"]}')
        if 'warning' in rec:
            print(f'      ⚠️  {rec["warning"]}')
        print()

if __name__ == "__main__":
    demo_duplicate_prevention()
