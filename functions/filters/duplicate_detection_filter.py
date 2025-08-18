"""
OpenWebUI Duplicate Detection Filter - Zero Configuration
Automatically detects and alerts users about potential duplicate uploads
"""
import json
import hashlib
import sqlite3
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=5, description="Filter priority (higher = runs earlier)"
        )
        enable_duplicate_alerts: bool = Field(
            default=True, description="Enable duplicate file upload alerts"
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

    def __init__(self):
        self.valves = self.Valves()
        self.db_path = '/app/backend/data/webui.db'

    async def inlet(self, body: dict, user: dict = None) -> dict:
        """
        Zero-configuration duplicate detection for file uploads
        Runs automatically when users upload files
        """
        
        if not self.valves.enable_duplicate_alerts:
            return body
            
        # Extract user info
        user_id = user.get("id") if user else None
        if not user_id:
            return body
            
        # Check if this is a file upload message
        messages = body.get("messages", [])
        if not messages:
            return body
            
        last_message = messages[-1]
        message_content = last_message.get("content", "")
        
        # Look for file upload indicators
        if not self._contains_file_upload(message_content):
            return body
            
        try:
            # Check for potential duplicates
            duplicate_info = self._check_user_files_for_duplicates(user_id, message_content)
            
            if duplicate_info["has_potential_duplicates"]:
                # Add duplicate warning to the conversation
                warning_message = self._create_duplicate_warning(duplicate_info)
                
                if self.valves.alert_mode == "warning":
                    # Add warning message to conversation
                    body["messages"].append({
                        "role": "system",
                        "content": warning_message
                    })
                elif self.valves.alert_mode == "block":
                    # Replace user message with block message
                    body["messages"][-1]["content"] = f"⚠️ **Upload Blocked** - {warning_message}"
                    
        except Exception as e:
            print(f"[DUPLICATE_FILTER] Error: {e}")
            # Fail silently to avoid breaking uploads
            
        return body

    def _contains_file_upload(self, content: str) -> bool:
        """Check if message content indicates a file upload"""
        upload_indicators = [
            "uploaded", "attachment", "file:", "document:", 
            ".pdf", ".doc", ".txt", ".csv", ".xlsx"
        ]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in upload_indicators)

    def _check_user_files_for_duplicates(self, user_id: str, content: str) -> Dict:
        """Check user's existing files for potential duplicates"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user's recent files
            cursor.execute("""
                SELECT filename, hash, created_at 
                FROM file 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 50
            """, (user_id,))
            
            user_files = cursor.fetchall()
            conn.close()
            
            if not user_files:
                return {"has_potential_duplicates": False}
                
            # Extract filename from content (basic extraction)
            potential_filename = self._extract_filename_from_content(content)
            
            # Check for similar filenames
            similar_files = []
            for filename, file_hash, created_at in user_files:
                similarity = self._calculate_filename_similarity(potential_filename, filename)
                if similarity >= self.valves.similarity_threshold:
                    similar_files.append({
                        "filename": filename,
                        "similarity": similarity,
                        "uploaded_date": created_at
                    })
            
            # Sort by similarity and limit results
            similar_files.sort(key=lambda x: x["similarity"], reverse=True)
            similar_files = similar_files[:self.valves.max_duplicates_to_show]
            
            return {
                "has_potential_duplicates": len(similar_files) > 0,
                "similar_files": similar_files,
                "potential_filename": potential_filename
            }
            
        except Exception as e:
            print(f"[DUPLICATE_FILTER] Database error: {e}")
            return {"has_potential_duplicates": False}

    def _extract_filename_from_content(self, content: str) -> str:
        """Extract potential filename from message content"""
        # Basic filename extraction - can be enhanced
        words = content.split()
        for word in words:
            if "." in word and len(word) > 4:
                # Looks like a filename
                return word.strip(",.!?")
        return "unknown_file"

    def _calculate_filename_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two filenames"""
        if not name1 or not name2:
            return 0.0
            
        # Normalize names
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()
        
        if name1 == name2:
            return 1.0
            
        # Simple character-based similarity
        set1 = set(name1)
        set2 = set(name2)
        
        if not set1 or not set2:
            return 0.0
            
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    def _create_duplicate_warning(self, duplicate_info: Dict) -> str:
        """Create user-friendly duplicate warning message"""
        similar_files = duplicate_info.get("similar_files", [])
        potential_name = duplicate_info.get("potential_filename", "this file")
        
        if not similar_files:
            return ""
            
        warning = f"⚠️ **Potential Duplicate Detected**\n\n"
        warning += f"The file '{potential_name}' appears similar to files you've already uploaded:\n\n"
        
        for i, file_info in enumerate(similar_files, 1):
            similarity_pct = int(file_info["similarity"] * 100)
            warning += f"{i}. **{file_info['filename']}** "
            warning += f"({similarity_pct}% similar, uploaded: {file_info['uploaded_date']})\n"
        
        warning += f"\n💡 **Tip**: If this is truly a new file, consider renaming it to avoid confusion."
        
        return warning
