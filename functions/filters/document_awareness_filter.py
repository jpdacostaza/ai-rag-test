"""
Document Awareness Filter for OpenWebUI
Injects information about available user documents into the conversation context
"""
import sqlite3
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=2, description="Filter priority (higher = runs earlier)"
        )
        enable_document_awareness: bool = Field(
            default=True, description="Enable document awareness injection"
        )
        max_documents_to_show: int = Field(
            default=5, description="Maximum number of documents to mention"
        )
        show_document_details: bool = Field(
            default=True, description="Show document filenames and upload dates"
        )
        trigger_keywords: List[str] = Field(
            default=["cv", "resume", "document", "file", "upload", "pdf"],
            description="Keywords that trigger document awareness"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.db_path = '/app/backend/data/webui.db'

    async def inlet(self, body: dict, user: dict = None) -> dict:
        """
        Inject document awareness into conversation when relevant
        """
        print(f"[DOCUMENT_AWARENESS] Filter called - enable_document_awareness: {self.valves.enable_document_awareness}")
        print(f"[DOCUMENT_AWARENESS] User context received: {user}")
        print(f"[DOCUMENT_AWARENESS] User type: {type(user)}")
        
        if not self.valves.enable_document_awareness:
            print(f"[DOCUMENT_AWARENESS] Filter disabled, returning body unchanged")
            return body
            
        # Extract user info - require valid user ID
        user_id = user.get("id") if user else None
        if not user_id:
            print(f"[DOCUMENT_AWARENESS] No user ID found, returning body unchanged")
            return body
        print(f"[DOCUMENT_AWARENESS] User ID: {user_id}")
            
        # Check if this is a relevant conversation
        messages = body.get("messages", [])
        print(f"[DOCUMENT_AWARENESS] Found {len(messages)} messages")
        if not messages:
            print(f"[DOCUMENT_AWARENESS] No messages found, returning body unchanged")
            return body
            
        last_message = messages[-1]
        message_content = last_message.get("content", "").lower()
        print(f"[DOCUMENT_AWARENESS] Last message content: {message_content[:100]}...")
        
        # Check if conversation is about documents/files/CV
        is_document_related = any(keyword in message_content for keyword in self.valves.trigger_keywords)
        print(f"[DOCUMENT_AWARENESS] Document related: {is_document_related}")
        
        if not is_document_related:
            return body
            
        try:
            # Get user's available documents
            user_documents = self._get_user_documents(user_id)
            
            if user_documents:
                # Create document awareness message
                awareness_message = self._create_document_awareness_message(user_documents)
                
                # Inject as system message
                system_message = {
                    "role": "system",
                    "content": awareness_message
                }
                
                # Add to conversation context
                body["messages"].insert(-1, system_message)
                
        except Exception as e:
            print(f"[DOCUMENT_AWARENESS] Error: {e}")
            # Fail silently to avoid breaking conversations
            
        return body

    def _get_user_documents(self, user_id: str) -> List[Dict]:
        """Get user's available documents from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user's files and documents
            cursor.execute("""
                SELECT 
                    f.filename,
                    f.created_at,
                    f.hash,
                    d.name as doc_name,
                    d.title as doc_title,
                    d.collection_name
                FROM file f
                LEFT JOIN document d ON f.user_id = d.user_id 
                    AND (d.filename = f.filename OR d.name LIKE '%' || f.filename || '%')
                WHERE f.user_id = ?
                ORDER BY f.created_at DESC
                LIMIT ?
            """, (user_id, self.valves.max_documents_to_show))
            
            results = cursor.fetchall()
            conn.close()
            
            documents = []
            for row in results:
                filename, created_at, file_hash, doc_name, doc_title, collection_name = row
                
                documents.append({
                    "filename": filename,
                    "created_at": created_at,
                    "hash": file_hash[:8] + "...",
                    "doc_name": doc_name,
                    "doc_title": doc_title,
                    "collection_name": collection_name,
                    "has_processed_content": bool(collection_name)
                })
            
            return documents
            
        except Exception as e:
            print(f"[DOCUMENT_AWARENESS] Database error: {e}")
            return []

    def _create_document_awareness_message(self, documents: List[Dict]) -> str:
        """Create a system message about available documents"""
        
        if not documents:
            return "No documents are currently available for this user."
        
        message_parts = [
            "📄 **DOCUMENT CONTEXT** - The user has the following documents available:",
            ""
        ]
        
        for i, doc in enumerate(documents, 1):
            filename = doc["filename"]
            created_at = doc["created_at"]
            has_content = doc["has_processed_content"]
            
            if self.valves.show_document_details:
                status = "✅ PROCESSED & SEARCHABLE" if has_content else "⏳ UPLOADED (processing may be needed)"
                message_parts.append(f"{i}. **{filename}**")
                message_parts.append(f"   - Status: {status}")
                message_parts.append(f"   - Uploaded: {created_at}")
                
                if has_content and doc["collection_name"]:
                    message_parts.append(f"   - Collection: {doc['collection_name']}")
                
                message_parts.append("")
        
        # Add usage instructions
        message_parts.extend([
            "**IMPORTANT FOR AI:**",
            "- You HAVE ACCESS to the content of processed documents",
            "- You can search and reference information from these files",
            "- If asked about CV/resume content, search the available documents",
            "- Do not ask users to paste content that's already uploaded",
            "- Use semantic search to find relevant information from documents",
            ""
        ])
        
        # Special handling for CV/resume
        cv_files = [doc for doc in documents if any(cv_word in doc["filename"].lower() 
                   for cv_word in ["cv", "resume", "curriculum"])]
        
        if cv_files:
            message_parts.extend([
                "🎯 **CV/RESUME DETECTED:**",
                f"The user has uploaded: {', '.join([doc['filename'] for doc in cv_files])}",
                "You can access and analyze the CV content directly - no need to ask for it to be pasted!",
                ""
            ])
        
        return "\n".join(message_parts)

    def _should_inject_awareness(self, message_content: str) -> bool:
        """Determine if document awareness should be injected"""
        
        # Keywords that suggest user is asking about documents
        document_indicators = [
            "my cv", "my resume", "curriculum vitae", 
            "review my", "analyze my", "look at my",
            "uploaded file", "document i sent", "pdf i shared",
            "file i uploaded", "document content", "what's in my"
        ]
        
        content_lower = message_content.lower()
        return any(indicator in content_lower for indicator in document_indicators)
