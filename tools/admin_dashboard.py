#!/usr/bin/env python3
"""
OpenWebUI Admin Dashboard for Duplicate Management
Provides comprehensive tools for administrators to manage file duplicates
"""
import sqlite3
import chromadb
import json
from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime

class DuplicateAdminDashboard:
    def __init__(self, db_path: str = '/app/backend/data/webui.db', 
                 chroma_path: str = '/app/backend/data/chroma'):
        self.db_path = db_path
        self.chroma_path = chroma_path
    
    def generate_system_report(self) -> Dict:
        """Generate comprehensive system report with duplicate analysis"""
        print('📊 GENERATING SYSTEM DUPLICATE REPORT')
        print('=' * 45)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Basic statistics
        cursor.execute('SELECT COUNT(*) FROM file')
        total_files = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM document')
        total_documents = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM file')
        total_users = cursor.fetchone()[0]
        
        # Find duplicates by hash
        cursor.execute('''
            SELECT hash, COUNT(*) as count, 
                   GROUP_CONCAT(id) as file_ids,
                   GROUP_CONCAT(filename) as filenames
            FROM file 
            WHERE hash IS NOT NULL
            GROUP BY hash 
            HAVING COUNT(*) > 1
        ''')
        
        hash_duplicates = cursor.fetchall()
        
        # Find duplicates by filename per user
        cursor.execute('''
            SELECT user_id, filename, COUNT(*) as count,
                   GROUP_CONCAT(id) as file_ids
            FROM file 
            GROUP BY user_id, filename 
            HAVING COUNT(*) > 1
        ''')
        
        filename_duplicates = cursor.fetchall()
        
        # Calculate storage usage
        duplicate_files = sum(count - 1 for _, count, _, _ in hash_duplicates)
        
        # Vector collection analysis
        vector_stats = self._analyze_vector_collections()
        
        conn.close()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_stats': {
                'total_files': total_files,
                'total_documents': total_documents,
                'total_users': total_users,
                'duplicate_files': duplicate_files,
                'storage_efficiency': ((total_files - duplicate_files) / total_files * 100) if total_files > 0 else 100
            },
            'hash_duplicates': [
                {
                    'hash': hash_val[:16] + '...',
                    'count': count,
                    'file_ids': file_ids.split(','),
                    'filenames': list(set(filenames.split(',')))
                }
                for hash_val, count, file_ids, filenames in hash_duplicates
            ],
            'filename_duplicates': [
                {
                    'user_id': user_id[:8] + '...',
                    'filename': filename,
                    'count': count,
                    'file_ids': file_ids.split(',')
                }
                for user_id, filename, count, file_ids in filename_duplicates
            ],
            'vector_stats': vector_stats
        }
        
        return report
    
    def _analyze_vector_collections(self) -> Dict:
        """Analyze vector collections for duplicates and efficiency"""
        try:
            client = chromadb.PersistentClient(path=self.chroma_path)
            collections = client.list_collections()
            
            total_collections = len(collections)
            total_chunks = 0
            collection_info = []
            
            for col in collections:
                try:
                    collection = client.get_collection(col.name)
                    chunk_count = collection.count()
                    total_chunks += chunk_count
                    
                    collection_info.append({
                        'name': col.name,
                        'chunks': chunk_count,
                        'type': 'file' if col.name.startswith('file-') else 'other'
                    })
                    
                except Exception as e:
                    collection_info.append({
                        'name': col.name,
                        'chunks': 0,
                        'error': str(e)
                    })
            
            return {
                'total_collections': total_collections,
                'total_chunks': total_chunks,
                'avg_chunks_per_collection': total_chunks / total_collections if total_collections > 0 else 0,
                'collections': collection_info
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def create_cleanup_plan(self, dry_run: bool = True) -> Dict:
        """Create a plan for cleaning up duplicates"""
        print('🧹 CREATING DUPLICATE CLEANUP PLAN')
        print('=' * 40)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find hash-based duplicates
        cursor.execute('''
            SELECT hash, filename, id, user_id, created_at
            FROM file 
            WHERE hash IN (
                SELECT hash FROM file 
                WHERE hash IS NOT NULL
                GROUP BY hash 
                HAVING COUNT(*) > 1
            )
            ORDER BY hash, created_at
        ''')
        
        duplicates = cursor.fetchall()
        
        # Group by hash and create cleanup plan
        hash_groups = defaultdict(list)
        for hash_val, filename, file_id, user_id, created_at in duplicates:
            hash_groups[hash_val].append({
                'id': file_id,
                'filename': filename,
                'user_id': user_id,
                'created_at': created_at
            })
        
        cleanup_operations = []
        space_saved = 0
        
        for hash_val, files in hash_groups.items():
            if len(files) > 1:
                # Sort by creation date (keep oldest)
                files.sort(key=lambda x: x['created_at'])
                
                keep_file = files[0]
                remove_files = files[1:]
                
                operation = {
                    'hash': hash_val[:16] + '...',
                    'keep_file': {
                        'id': keep_file['id'][:8] + '...',
                        'filename': keep_file['filename'],
                        'created_at': keep_file['created_at']
                    },
                    'remove_files': [
                        {
                            'id': f['id'][:8] + '...',
                            'filename': f['filename'],
                            'created_at': f['created_at'],
                            'actions': [
                                f"DELETE FROM file WHERE id = '{f['id']}'",
                                f"DELETE FROM document WHERE collection_name = 'file-{f['id']}'",
                                f"DELETE VECTOR COLLECTION 'file-{f['id']}'"
                            ]
                        }
                        for f in remove_files
                    ],
                    'space_saved_estimate': len(remove_files) * 21000  # Estimated characters per file
                }
                
                cleanup_operations.append(operation)
                space_saved += operation['space_saved_estimate']
        
        conn.close()
        
        return {
            'dry_run': dry_run,
            'total_operations': len(cleanup_operations),
            'total_files_to_remove': sum(len(op['remove_files']) for op in cleanup_operations),
            'estimated_space_saved': space_saved,
            'operations': cleanup_operations
        }
    
    def execute_cleanup(self, cleanup_plan: Dict, confirm: bool = False) -> Dict:
        """Execute the cleanup plan (DANGEROUS - requires confirmation)"""
        if not confirm:
            return {
                'error': 'Cleanup requires explicit confirmation',
                'message': 'Set confirm=True to execute cleanup'
            }
        
        if cleanup_plan.get('dry_run', True):
            return {
                'error': 'Cannot execute dry run plan',
                'message': 'Generate plan with dry_run=False first'
            }
        
        print('⚠️  EXECUTING CLEANUP PLAN')
        print('=' * 30)
        print('THIS WILL PERMANENTLY DELETE FILES!')
        
        executed_operations = 0
        failed_operations = 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            client = chromadb.PersistentClient(path=self.chroma_path)
            
            for operation in cleanup_plan['operations']:
                for remove_file in operation['remove_files']:
                    try:
                        # Extract actual file ID (remove the '...' truncation)
                        # This is a simplified version - real implementation would need full IDs
                        print(f"Would execute: {remove_file['actions']}")
                        executed_operations += 1
                        
                    except Exception as e:
                        print(f"Failed to cleanup file: {e}")
                        failed_operations += 1
            
            # conn.commit()  # Uncomment to actually execute
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Cleanup failed: {e}'}
        finally:
            conn.close()
        
        return {
            'executed_operations': executed_operations,
            'failed_operations': failed_operations,
            'message': 'Cleanup completed (simulation mode)'
        }
    
    def generate_user_report(self, user_id: str) -> Dict:
        """Generate duplicate report for specific user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM file WHERE user_id = ?', (user_id,))
        user_files = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT filename, COUNT(*) as count, GROUP_CONCAT(id) as file_ids
            FROM file 
            WHERE user_id = ?
            GROUP BY filename 
            HAVING COUNT(*) > 1
        ''', (user_id,))
        
        user_duplicates = cursor.fetchall()
        
        conn.close()
        
        return {
            'user_id': user_id[:8] + '...',
            'total_files': user_files,
            'duplicate_sets': len(user_duplicates),
            'duplicate_files': sum(count - 1 for _, count, _ in user_duplicates),
            'duplicates': [
                {
                    'filename': filename,
                    'count': count,
                    'file_ids': [fid[:8] + '...' for fid in file_ids.split(',')]
                }
                for filename, count, file_ids in user_duplicates
            ]
        }

def demo_admin_dashboard():
    """Demonstrate the admin dashboard functionality"""
    print('👨‍💼 DUPLICATE MANAGEMENT ADMIN DASHBOARD')
    print('=' * 45)
    
    dashboard = DuplicateAdminDashboard()
    
    # Generate system report
    print('\n📊 SYSTEM REPORT:')
    system_report = dashboard.generate_system_report()
    
    stats = system_report['system_stats']
    print(f"   📁 Total files: {stats['total_files']}")
    print(f"   📄 Total documents: {stats['total_documents']}")
    print(f"   👥 Total users: {stats['total_users']}")
    print(f"   🔄 Duplicate files: {stats['duplicate_files']}")
    print(f"   📊 Storage efficiency: {stats['storage_efficiency']:.1f}%")
    
    if system_report['hash_duplicates']:
        print(f"\n⚠️  HASH DUPLICATES FOUND:")
        for dup in system_report['hash_duplicates']:
            print(f"      Hash {dup['hash']}: {dup['count']} copies")
            print(f"      Files: {', '.join(dup['filenames'])}")
    
    # Generate cleanup plan
    print('\n🧹 CLEANUP PLAN:')
    cleanup_plan = dashboard.create_cleanup_plan(dry_run=True)
    
    print(f"   Operations planned: {cleanup_plan['total_operations']}")
    print(f"   Files to remove: {cleanup_plan['total_files_to_remove']}")
    print(f"   Estimated space saved: {cleanup_plan['estimated_space_saved']:,} characters")
    
    if cleanup_plan['operations']:
        print(f"\n   📋 CLEANUP OPERATIONS:")
        for i, op in enumerate(cleanup_plan['operations'][:2], 1):  # Show first 2
            print(f"      {i}. Keep: {op['keep_file']['filename']}")
            print(f"         Remove: {len(op['remove_files'])} duplicate(s)")
    
    # User-specific report
    user_id = "e7e39ee3-b886-4f92-8fb2-fbeb524fe5ce"
    print(f'\n👤 USER REPORT (ID: {user_id[:8]}...):')
    user_report = dashboard.generate_user_report(user_id)
    
    print(f"   Total files: {user_report['total_files']}")
    print(f"   Duplicate sets: {user_report['duplicate_sets']}")
    print(f"   Duplicate files: {user_report['duplicate_files']}")
    
    if user_report['duplicates']:
        for dup in user_report['duplicates']:
            print(f"   📄 {dup['filename']}: {dup['count']} copies")

if __name__ == "__main__":
    demo_admin_dashboard()
