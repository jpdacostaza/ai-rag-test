#!/usr/bin/env python3
"""
OpenWebUI Auto-Deduplication Integration Hook
This script modifies OpenWebUI's upload handler to include automatic duplicate detection
"""

import os
import sys
import json
import hashlib
import sqlite3
from pathlib import Path

class AutoDeduplicationHook:
    """
    Real-time duplicate detection that integrates with OpenWebUI's upload process
    """
    
    def __init__(self):
        self.db_path = '/app/backend/data/webui.db'
        
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def check_duplicate_before_upload(self, user_id: str, filename: str, file_content: bytes) -> dict:
        """
        Check for duplicates BEFORE the file is actually uploaded to the system
        Returns: {
            'is_duplicate': bool,
            'action': 'allow' | 'warn' | 'block',
            'message': str,
            'existing_files': list
        }
        """
        file_hash = self.calculate_file_hash(file_content)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for exact hash duplicates
            cursor.execute('''
                SELECT id, filename, created_at 
                FROM file 
                WHERE user_id = ? AND hash = ?
                ORDER BY created_at DESC
            ''', (user_id, file_hash))
            
            exact_duplicates = cursor.fetchall()
            
            # Check for filename duplicates (potential updates)
            cursor.execute('''
                SELECT id, filename, hash, created_at 
                FROM file 
                WHERE user_id = ? AND filename = ? AND hash != ?
                ORDER BY created_at DESC
                LIMIT 3
            ''', (user_id, filename, file_hash))
            
            filename_matches = cursor.fetchall()
            conn.close()
            
            if exact_duplicates:
                # Exact duplicate found
                latest = exact_duplicates[0]
                return {
                    'is_duplicate': True,
                    'action': 'block',
                    'message': f'⚠️ **Exact Duplicate Detected**\\n\\nThis file is identical to "{latest[1]}" uploaded on {latest[2]}.\\n\\n**Options:**\\n• Skip upload (recommended)\\n• Upload anyway (not recommended)',
                    'existing_files': exact_duplicates,
                    'duplicate_type': 'exact',
                    'file_hash': file_hash
                }
            
            elif filename_matches:
                # Same filename, different content (potential update)
                latest = filename_matches[0]
                return {
                    'is_duplicate': True,
                    'action': 'warn',
                    'message': f'📝 **Filename Match Detected**\\n\\nA file named "{filename}" already exists but with different content.\\n\\n**Options:**\\n• Replace existing file\\n• Upload as new version\\n• Cancel upload',
                    'existing_files': filename_matches,
                    'duplicate_type': 'filename',
                    'file_hash': file_hash
                }
            
            else:
                # No duplicates found
                return {
                    'is_duplicate': False,
                    'action': 'allow',
                    'message': 'File is unique, proceeding with upload.',
                    'existing_files': [],
                    'duplicate_type': None,
                    'file_hash': file_hash
                }
                
        except Exception as e:
            print(f"Error checking duplicates: {e}")
            return {
                'is_duplicate': False,
                'action': 'allow',
                'message': f'Unable to check for duplicates: {e}',
                'existing_files': [],
                'duplicate_type': 'error',
                'file_hash': None
            }
    
    def install_upload_hook(self):
        """
        Install the auto-deduplication hook into OpenWebUI's upload process
        """
        print("🔧 Installing Auto-Deduplication Upload Hook...")
        
        # This would require modifying OpenWebUI's source code
        # For now, we'll create a monitoring script
        hook_script = '''
# This hook should be integrated into OpenWebUI's upload handler
# Location: /app/backend/open_webui/routers/files.py

from .auto_deduplication_hook import AutoDeduplicationHook

@app.post("/api/v1/files/")
async def upload_file(file: UploadFile, user=Depends(get_current_user)):
    """Enhanced upload with auto-deduplication"""
    
    # Read file content
    file_content = await file.read()
    
    # Check for duplicates BEFORE processing
    dedup_hook = AutoDeduplicationHook()
    duplicate_check = dedup_hook.check_duplicate_before_upload(
        user.id, file.filename, file_content
    )
    
    if duplicate_check['is_duplicate']:
        if duplicate_check['action'] == 'block':
            return JSONResponse(
                status_code=409,  # Conflict
                content={
                    "detail": "Duplicate file detected",
                    "message": duplicate_check['message'],
                    "duplicate_info": duplicate_check
                }
            )
        elif duplicate_check['action'] == 'warn':
            # Return warning with options
            return JSONResponse(
                status_code=202,  # Accepted with conditions
                content={
                    "detail": "Potential duplicate detected",
                    "message": duplicate_check['message'],
                    "duplicate_info": duplicate_check,
                    "options": ["replace", "version", "proceed"]
                }
            )
    
    # Proceed with normal upload if no issues
    return await original_upload_file(file, user)
'''
        
        # Save the hook script for reference
        with open('/tmp/upload_hook_integration.py', 'w') as f:
            f.write(hook_script)
        
        print("✅ Hook script created at /tmp/upload_hook_integration.py")
        print("📝 Note: This requires integration with OpenWebUI source code")
        
    def create_monitoring_script(self):
        """
        Create a monitoring script that watches for new uploads and alerts about duplicates
        """
        monitoring_script = '''#!/usr/bin/env python3
"""
OpenWebUI Upload Monitor - Auto Duplicate Detection
Monitors the database for new uploads and alerts about duplicates
"""
import sqlite3
import time
import json
from datetime import datetime

class UploadMonitor:
    def __init__(self):
        self.db_path = '/app/backend/data/webui.db'
        self.last_check_time = int(time.time())
        
    def monitor_uploads(self):
        """Monitor for new file uploads and check for duplicates"""
        print(f"🔍 Starting upload monitoring at {datetime.now()}")
        
        while True:
            try:
                current_time = int(time.time())
                
                # Check for files uploaded since last check
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, user_id, filename, hash, created_at
                    FROM file 
                    WHERE created_at > ?
                    ORDER BY created_at DESC
                ''', (self.last_check_time,))
                
                new_files = cursor.fetchall()
                
                for file_data in new_files:
                    file_id, user_id, filename, file_hash, created_at = file_data
                    
                    if file_hash:  # Only check files with hashes
                        # Check for duplicates of this hash
                        cursor.execute('''
                            SELECT COUNT(*) 
                            FROM file 
                            WHERE hash = ? AND user_id = ?
                        ''', (file_hash, user_id))
                        
                        duplicate_count = cursor.fetchone()[0]
                        
                        if duplicate_count > 1:
                            print(f"⚠️  DUPLICATE DETECTED:")
                            print(f"   File: {filename}")
                            print(f"   User: {user_id[:8]}...")
                            print(f"   Hash: {file_hash[:16]}...")
                            print(f"   Total copies: {duplicate_count}")
                            print(f"   Uploaded: {datetime.fromtimestamp(created_at)}")
                            print()
                
                conn.close()
                self.last_check_time = current_time
                
                # Wait before next check
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                time.sleep(60)  # Wait longer on error

if __name__ == "__main__":
    monitor = UploadMonitor()
    monitor.monitor_uploads()
'''
        
        # Save the monitoring script in the proper location
        with open('/app/backend/scripts/monitoring/upload_monitor.py', 'w') as f:
            f.write(monitoring_script)
        
        print("✅ Upload monitor created at /app/backend/scripts/monitoring/upload_monitor.py")

def main():
    """Main function to set up auto-deduplication"""
    print("🚀 OpenWebUI Auto-Deduplication Setup")
    print("=" * 40)
    
    hook = AutoDeduplicationHook()
    
    # Test the duplicate detection
    print("🧪 Testing duplicate detection...")
    
    # Create a test scenario
    test_content = b"This is test content for duplicate detection"
    test_result = hook.check_duplicate_before_upload(
        "test_user", 
        "test_file.txt", 
        test_content
    )
    
    print(f"Test result: {test_result['action']} - {test_result['message']}")
    
    # Install monitoring components
    hook.install_upload_hook()
    hook.create_monitoring_script()
    
    print()
    print("📋 NEXT STEPS:")
    print("1. ✅ Upload monitoring script created")
    print("2. 📝 Integration hook script created")
    print("3. 🔧 Manual integration with OpenWebUI required")
    print()
    print("To enable real-time monitoring:")
    print("   docker exec -d backend-openwebui python /app/backend/scripts/monitoring/upload_monitor.py")

if __name__ == "__main__":
    main()
