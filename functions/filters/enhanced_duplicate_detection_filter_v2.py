"""
Enhanced Duplicate Detection Filter v2.0 - Real-Time Integration
Automatically detects and prevents duplicate uploads in real-time
"""
import json
import hashlib
import sqlite3
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=8, description="Filter priority (higher = runs earlier, before file processing)"
        )
        enable_duplicate_alerts: bool = Field(
            default=True, description="Enable duplicate file upload alerts"
        )
        enable_auto_cleanup: bool = Field(
            default=True, description="Automatically remove old duplicates when new ones are uploaded"
        )
        auto_cleanup_mode: str = Field(
            default="conservative", description="Auto-cleanup mode: 'conservative' (keep oldest), 'aggressive' (keep newest), 'disabled'"
        )
        max_auto_cleanup_per_session: int = Field(
            default=10, description="Maximum number of files to auto-cleanup per conversation"
        )
        similarity_threshold: float = Field(
            default=0.95, description="Similarity threshold for duplicate detection (0.0-1.0)"
        )
        max_duplicates_to_show: int = Field(
            default=3, description="Maximum number of similar files to show in alert"
        )
        alert_mode: str = Field(
            default="warning", description="Alert mode: 'warning', 'block', or 'silent'"
        )
        check_recent_uploads: bool = Field(
            default=True, description="Monitor recent uploads for duplicates"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.type = "filter"
        self.name = "Enhanced Duplicate Detection"
        self.version = "2.0"
        self.db_path = '/app/backend/data/webui.db'

    def _log(self, message: str):
        """Debug logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [DUPLICATE_FILTER_v{self.version}] {message}")

    async def inlet(self, body: dict, user: dict = None) -> dict:
        """
        Enhanced duplicate detection with real-time monitoring
        """
        if not self.valves.enable_duplicate_alerts:
            return body
            
        # Extract user info
        user_id = user.get("id") if user else "global_user"
        
        # Check for recent uploads if enabled
        if self.valves.check_recent_uploads:
            recent_duplicates = self._check_recent_uploads(user_id)
            if recent_duplicates:
                self._add_duplicate_alert_to_conversation(body, recent_duplicates)
        
        # Check if this message mentions file uploads
        messages = body.get("messages", [])
        if not messages:
            return body
            
        last_message = messages[-1]
        message_content = last_message.get("content", "")
        
        # Enhanced file upload detection
        if self._contains_file_reference(message_content):
            self._log(f"File reference detected in message: {message_content[:50]}...")
            
            # Check for potential duplicates based on filename patterns
            duplicate_info = self._check_user_files_for_duplicates(user_id, message_content)
            
            if duplicate_info["has_potential_duplicates"]:
                warning_message = self._create_duplicate_warning(duplicate_info)
                
                if self.valves.alert_mode == "warning":
                    # Add warning message to conversation
                    body["messages"].append({
                        "role": "system",
                        "content": warning_message
                    })
                    self._log(f"Added duplicate warning for user {user_id[:8]}")
                    
                elif self.valves.alert_mode == "block":
                    # Replace user message with block message
                    body["messages"][-1]["content"] = f"⚠️ **Upload Analysis** - {warning_message}"
                    self._log(f"Blocked potential duplicate upload for user {user_id[:8]}")
        
        return body

    def _check_recent_uploads(self, user_id: str, time_window: int = 300) -> List[Dict]:
        """
        Check for duplicate files uploaded in the last time_window seconds
        """
        try:
            import time
            cutoff_time = int(time.time()) - time_window
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent files for this user
            cursor.execute("""
                SELECT id, filename, hash, created_at
                FROM file 
                WHERE user_id = ? AND created_at > ?
                ORDER BY created_at DESC
            """, (user_id, cutoff_time))
            
            recent_files = cursor.fetchall()
            
            # Group by hash to find duplicates
            hash_groups = {}
            for file_id, filename, file_hash, created_at in recent_files:
                if file_hash:
                    if file_hash not in hash_groups:
                        hash_groups[file_hash] = []
                    hash_groups[file_hash].append({
                        'id': file_id,
                        'filename': filename,
                        'created_at': created_at
                    })
            
            # Find groups with duplicates
            duplicates = []
            for file_hash, files in hash_groups.items():
                if len(files) > 1:
                    # Sort by creation time
                    files.sort(key=lambda x: x['created_at'])
                    duplicates.append({
                        'hash': file_hash,
                        'files': files,
                        'count': len(files),
                        'latest_upload': max(f['created_at'] for f in files)
                    })
            
            conn.close()
            
            if duplicates:
                self._log(f"Found {len(duplicates)} recent duplicate sets for user {user_id[:8]}")
            
            return duplicates
            
        except Exception as e:
            self._log(f"Error checking recent uploads: {e}")
            return []

    def _contains_file_reference(self, content: str) -> bool:
        """Enhanced file upload detection"""
        # More comprehensive patterns
        upload_patterns = [
            r'\buploaded?\b',
            r'\battached?\b', 
            r'\bfile[s]?\b',
            r'\bdocument[s]?\b',
            r'\.(pdf|doc|docx|txt|csv|xlsx|ppt|pptx|jpg|png|gif)\b',
            r'\bCV\b',
            r'\bresume\b',
            r'\breport\b'
        ]
        
        content_lower = content.lower()
        return any(re.search(pattern, content_lower, re.IGNORECASE) for pattern in upload_patterns)

    def _check_user_files_for_duplicates(self, user_id: str, content: str) -> Dict:
        """Enhanced duplicate checking with better filename extraction"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user's recent files
            cursor.execute("""
                SELECT filename, hash, created_at, id
                FROM file 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 50
            """, (user_id,))
            
            user_files = cursor.fetchall()
            conn.close()
            
            if not user_files:
                return {"has_potential_duplicates": False}
            
            # Enhanced filename extraction from content
            potential_filenames = self._extract_filenames_from_content(content)
            
            similar_files = []
            
            # Check against existing files
            for filename, file_hash, created_at, file_id in user_files:
                for potential_name in potential_filenames:
                    similarity = self._calculate_filename_similarity(potential_name, filename)
                    if similarity >= self.valves.similarity_threshold:
                        similar_files.append({
                            "filename": filename,
                            "similarity": similarity,
                            "uploaded_date": datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M"),
                            "file_id": file_id,
                            "hash": file_hash[:16] + "..." if file_hash else "no-hash"
                        })
            
            # Remove duplicates and sort by similarity
            seen_files = set()
            unique_similar = []
            for file_info in similar_files:
                file_key = (file_info["filename"], file_info["file_id"])
                if file_key not in seen_files:
                    seen_files.add(file_key)
                    unique_similar.append(file_info)
            
            unique_similar.sort(key=lambda x: x["similarity"], reverse=True)
            unique_similar = unique_similar[:self.valves.max_duplicates_to_show]
            
            return {
                "has_potential_duplicates": len(unique_similar) > 0,
                "similar_files": unique_similar,
                "potential_filenames": potential_filenames
            }
            
        except Exception as e:
            self._log(f"Database error: {e}")
            return {"has_potential_duplicates": False}

    def _extract_filenames_from_content(self, content: str) -> List[str]:
        """Enhanced filename extraction with better patterns"""
        filenames = []
        
        # Pattern 1: Explicit filename mentions
        filename_patterns = [
            r'"([^"]+\.[a-zA-Z0-9]{2,4})"',  # "filename.ext"
            r"'([^']+\.[a-zA-Z0-9]{2,4})'",  # 'filename.ext'
            r'\b([A-Za-z0-9._\-\s]+\.[a-zA-Z0-9]{2,4})\b',  # filename.ext
        ]
        
        for pattern in filename_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            filenames.extend(matches)
        
        # Pattern 2: Common document names
        if re.search(r'\b(cv|resume)\b', content, re.IGNORECASE):
            filenames.extend(["resume.pdf", "CV.pdf", "cv.docx"])
        
        # Pattern 3: Extract quoted phrases that might be filenames
        quoted_text = re.findall(r'"([^"]+)"', content)
        for text in quoted_text:
            if len(text) > 3 and len(text) < 100:  # Reasonable filename length
                filenames.append(text)
        
        # Clean and deduplicate
        cleaned = []
        for name in filenames:
            name = name.strip()
            if len(name) > 3 and name not in cleaned:
                cleaned.append(name)
        
        return cleaned[:5]  # Limit to 5 potential names

    def _calculate_filename_similarity(self, name1: str, name2: str) -> float:
        """Enhanced similarity calculation"""
        if not name1 or not name2:
            return 0.0
            
        # Normalize names
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()
        
        if name1 == name2:
            return 1.0
        
        # Check if one contains the other
        if name1 in name2 or name2 in name1:
            return 0.8
        
        # Word-based similarity for longer names
        if len(name1) > 10 or len(name2) > 10:
            words1 = set(re.findall(r'\b\w+\b', name1))
            words2 = set(re.findall(r'\b\w+\b', name2))
            
            if words1 and words2:
                intersection = len(words1.intersection(words2))
                union = len(words1.union(words2))
                return intersection / union if union > 0 else 0.0
        
        # Character-based similarity for shorter names
        set1 = set(name1)
        set2 = set(name2)
        
        if not set1 or not set2:
            return 0.0
            
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    def _add_duplicate_alert_to_conversation(self, body: dict, recent_duplicates: List[Dict]):
        """Add alert about recently detected duplicates"""
        if not recent_duplicates:
            return
            
        alert_message = "🔍 **Recent Upload Analysis**\n\n"
        alert_message += f"Detected {len(recent_duplicates)} recent duplicate file set(s):\n\n"
        
        for i, dup_set in enumerate(recent_duplicates[:3], 1):
            files = dup_set['files']
            latest_time = datetime.fromtimestamp(dup_set['latest_upload']).strftime("%H:%M:%S")
            
            alert_message += f"**{i}. {files[0]['filename']}** ({dup_set['count']} copies)\n"
            alert_message += f"   Latest upload: {latest_time}\n"
            alert_message += f"   Hash: {dup_set['hash'][:16]}...\n\n"
        
        alert_message += "💡 Consider using the cleanup tools to remove unnecessary duplicates."
        
        # Add as system message
        body["messages"].append({
            "role": "system", 
            "content": alert_message
        })
        
        self._log(f"Added recent duplicates alert ({len(recent_duplicates)} sets)")

    def _create_duplicate_warning(self, duplicate_info: Dict) -> str:
        """Create enhanced duplicate warning message"""
        similar_files = duplicate_info.get("similar_files", [])
        potential_names = duplicate_info.get("potential_filenames", [])
        
        if not similar_files:
            return ""
        
        warning = "⚠️ **Potential Duplicate Files Detected**\n\n"
        
        if potential_names:
            warning += f"Based on your message mentioning: {', '.join(potential_names[:2])}\n\n"
        
        warning += "Similar files already uploaded:\n\n"
        
        for i, file_info in enumerate(similar_files, 1):
            similarity_pct = int(file_info["similarity"] * 100)
            warning += f"{i}. **{file_info['filename']}**\n"
            warning += f"   📊 Similarity: {similarity_pct}%\n"
            warning += f"   📅 Uploaded: {file_info['uploaded_date']}\n"
            warning += f"   🔑 Hash: {file_info['hash']}\n\n"
        
        warning += "💡 **Recommendations:**\n"
        warning += "• Check if you already uploaded this file\n"
        warning += "• Use unique filenames to avoid confusion\n"
        warning += "• Consider using the cleanup tools for duplicates\n"
        
        return warning

    async def outlet(self, body: dict, user: dict = None) -> dict:
        """Process after conversation completion"""
        # Auto-cleanup duplicates if enabled
        if self.valves.enable_auto_cleanup and self.valves.auto_cleanup_mode != "disabled":
            user_id = user.get("id") if user else "global_user"
            cleanup_results = await self._perform_auto_cleanup(user_id)
            
            if cleanup_results['cleaned_count'] > 0:
                cleanup_message = f"🧹 **Auto-Cleanup Completed**\n\n"
                cleanup_message += f"Removed {cleanup_results['cleaned_count']} duplicate files\n"
                cleanup_message += f"Kept {cleanup_results['kept_count']} unique files\n"
                cleanup_message += f"Freed ~{cleanup_results['space_saved']}KB storage\n\n"
                cleanup_message += "✅ Your file library is now optimized!"
                
                # Add cleanup notification to conversation
                body["messages"].append({
                    "role": "system",
                    "content": cleanup_message
                })
                
                self._log(f"Auto-cleanup completed for user {user_id[:8]}: {cleanup_results['cleaned_count']} files removed")
        
        return body

    async def _perform_auto_cleanup(self, user_id: str) -> dict:
        """
        Automatically clean duplicate files for a user
        Returns: {
            'cleaned_count': int,
            'kept_count': int, 
            'space_saved': int,
            'errors': list
        }
        """
        try:
            import chromadb
            from collections import defaultdict
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find all files for this user grouped by hash
            cursor.execute("""
                SELECT id, filename, hash, created_at, data
                FROM file 
                WHERE user_id = ? AND hash IS NOT NULL
                ORDER BY created_at ASC
            """, (user_id,))
            
            user_files = cursor.fetchall()
            
            # Group by hash to find duplicates
            hash_groups = defaultdict(list)
            for file_data in user_files:
                file_id, filename, file_hash, created_at, data = file_data
                hash_groups[file_hash].append({
                    'id': file_id,
                    'filename': filename,
                    'created_at': created_at,
                    'data': data
                })
            
            cleaned_count = 0
            kept_count = 0
            errors = []
            space_saved = 0
            
            # Process each duplicate group (with safety limit)
            processed_count = 0
            for file_hash, files in hash_groups.items():
                if len(files) > 1 and processed_count < self.valves.max_auto_cleanup_per_session:
                    # Sort by creation time based on cleanup mode
                    if self.valves.auto_cleanup_mode == "conservative":
                        files.sort(key=lambda x: x['created_at'])  # Keep oldest
                        keep_file = files[0]
                        remove_files = files[1:]
                    elif self.valves.auto_cleanup_mode == "aggressive":
                        files.sort(key=lambda x: x['created_at'], reverse=True)  # Keep newest
                        keep_file = files[0] 
                        remove_files = files[1:]
                    else:
                        continue  # Skip if mode not recognized
                    
                    self._log(f"Processing {len(files)} duplicates of {keep_file['filename']} (mode: {self.valves.auto_cleanup_mode})")
                    
                    # Remove duplicate files
                    for remove_file in remove_files:
                        if processed_count >= self.valves.max_auto_cleanup_per_session:
                            break
                            
                        try:
                            file_id = remove_file['id']
                            collection_name = f'file-{file_id}'
                            
                            # Delete from file table
                            cursor.execute('DELETE FROM file WHERE id = ?', (file_id,))
                            
                            # Delete from document table  
                            cursor.execute('DELETE FROM document WHERE collection_name = ?', (collection_name,))
                            
                            # Delete vector collection
                            try:
                                client = chromadb.PersistentClient(path='/app/backend/data/chroma')
                                client.delete_collection(collection_name)
                            except Exception as e:
                                self._log(f"Vector collection {collection_name} not found: {e}")
                            
                            cleaned_count += 1
                            processed_count += 1
                            space_saved += len(remove_file.get('data', '') or '') // 1024  # Rough KB estimate
                            
                            self._log(f"Deleted duplicate: {file_id[:8]}... ({remove_file['filename']})")
                            
                        except Exception as e:
                            error_msg = f"Error deleting {remove_file['id'][:8]}: {e}"
                            errors.append(error_msg)
                            self._log(f"ERROR: {error_msg}")
                    
                    kept_count += 1
                else:
                    kept_count += 1
            
            # Commit all changes
            conn.commit()
            conn.close()
            
            return {
                'cleaned_count': cleaned_count,
                'kept_count': kept_count,
                'space_saved': space_saved,
                'errors': errors
            }
            
        except Exception as e:
            self._log(f"Auto-cleanup error: {e}")
            return {
                'cleaned_count': 0,
                'kept_count': 0,
                'space_saved': 0,
                'errors': [str(e)]
            }
