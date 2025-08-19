#!/usr/bin/env python3
"""
OpenWebUI Real-Time Duplicate Monitor
Monitors uploads and detects duplicates automatically
"""

import sqlite3
import time
import hashlib
from datetime import datetime

class RealTimeDuplicateMonitor:
    def __init__(self):
        self.db_path = '/app/backend/data/webui.db'
        self.last_check_time = int(time.time()) - 3600  # Start from 1 hour ago
        
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def check_for_new_uploads(self):
        """Check for files uploaded since last check"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get new files since last check
            cursor.execute("""
                SELECT id, user_id, filename, hash, created_at
                FROM file 
                WHERE created_at > ?
                ORDER BY created_at DESC
            """, (self.last_check_time,))
            
            new_files = cursor.fetchall()
            
            for file_data in new_files:
                file_id, user_id, filename, file_hash, created_at = file_data
                
                if file_hash:  # Only check files with hashes
                    # Check for duplicates of this hash
                    cursor.execute("""
                        SELECT id, filename, created_at 
                        FROM file 
                        WHERE hash = ? AND user_id = ? AND id != ?
                        ORDER BY created_at ASC
                    """, (file_hash, user_id, file_id))
                    
                    duplicates = cursor.fetchall()
                    
                    if duplicates:
                        print(f"🚨 DUPLICATE DETECTED!")
                        print(f"   📄 New File: {filename}")
                        print(f"   👤 User: {user_id[:8]}...")
                        print(f"   🔑 Hash: {file_hash[:16]}...")
                        print(f"   📅 Uploaded: {datetime.fromtimestamp(created_at)}")
                        print(f"   🔄 Duplicates:")
                        
                        for i, (dup_id, dup_filename, dup_created) in enumerate(duplicates, 1):
                            print(f"      {i}. {dup_filename} (ID: {dup_id[:8]}..., Created: {datetime.fromtimestamp(dup_created)})")
                        
                        print(f"   📊 Total copies: {len(duplicates) + 1}")
                        print()
                    else:
                        print(f"✅ UNIQUE FILE: {filename} (User: {user_id[:8]}...)")
            
            conn.close()
            return len(new_files)
            
        except Exception as e:
            print(f"❌ Error checking uploads: {e}")
            return 0
    
    def get_current_duplicate_stats(self):
        """Get current duplicate statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count total files
            cursor.execute("SELECT COUNT(*) FROM file")
            total_files = cursor.fetchone()[0]
            
            # Count files with duplicates
            cursor.execute("""
                SELECT hash, COUNT(*) as count
                FROM file 
                WHERE hash IS NOT NULL
                GROUP BY hash
                HAVING COUNT(*) > 1
            """)
            
            duplicate_groups = cursor.fetchall()
            duplicate_files = sum(count for _, count in duplicate_groups)
            unique_duplicate_sets = len(duplicate_groups)
            
            conn.close()
            
            return {
                'total_files': total_files,
                'duplicate_files': duplicate_files,
                'unique_duplicate_sets': unique_duplicate_sets,
                'unique_files': total_files - duplicate_files + unique_duplicate_sets
            }
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return None
    
    def start_monitoring(self, check_interval=30):
        """Start real-time monitoring"""
        print("🔍 REAL-TIME DUPLICATE MONITORING STARTED")
        print("=" * 45)
        print(f"⏰ Check interval: {check_interval} seconds")
        print(f"📊 Database: {self.db_path}")
        print()
        
        # Show initial stats
        stats = self.get_current_duplicate_stats()
        if stats:
            print("📊 CURRENT SYSTEM STATUS:")
            print(f"   Total files: {stats['total_files']}")
            print(f"   Duplicate files: {stats['duplicate_files']}")
            print(f"   Unique duplicate sets: {stats['unique_duplicate_sets']}")
            print(f"   Unique files: {stats['unique_files']}")
            print()
        
        print("🔄 Monitoring for new uploads...")
        print("   (Press Ctrl+C to stop)")
        print()
        
        try:
            while True:
                current_time = int(time.time())
                new_uploads = self.check_for_new_uploads()
                
                if new_uploads > 0:
                    print(f"📈 Processed {new_uploads} new uploads")
                
                self.last_check_time = current_time
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")

def test_duplicate_detection():
    """Test the duplicate detection system"""
    print("🧪 TESTING DUPLICATE DETECTION")
    print("=" * 30)
    
    monitor = RealTimeDuplicateMonitor()
    
    # Get current stats
    stats = monitor.get_current_duplicate_stats()
    if stats:
        print("📊 CURRENT SYSTEM STATUS:")
        print(f"   Total files: {stats['total_files']}")
        print(f"   Files with duplicates: {stats['duplicate_files']}")
        print(f"   Unique duplicate sets: {stats['unique_duplicate_sets']}")
        
        if stats['duplicate_files'] > 0:
            print(f"\n⚠️  DUPLICATES DETECTED!")
            print(f"   You have {stats['duplicate_files']} duplicate files")
            print(f"   Organized in {stats['unique_duplicate_sets']} duplicate sets")
            print(f"   Storage waste: ~{(stats['duplicate_files'] - stats['unique_duplicate_sets']) * 50}KB estimated")
        else:
            print("\n✅ NO DUPLICATES FOUND!")
    
    print("\n" + "=" * 30)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        # Start real-time monitoring
        monitor = RealTimeDuplicateMonitor()
        monitor.start_monitoring()
    else:
        # Just test and show stats
        test_duplicate_detection()
        
        print("\n🚀 TO START REAL-TIME MONITORING:")
        print("   python scripts/monitoring/realtime_monitor.py monitor")
