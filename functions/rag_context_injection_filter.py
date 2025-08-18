"""
RAG Content Injection Filter for OpenWebUI
Automatically searches user documents and injects relevant content into conversations
"""
import sqlite3
import json
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=3, description="Filter priority (runs after document awareness)"
        )
        enable_rag_injection: bool = Field(
            default=True, description="Enable automatic RAG content injection"
        )
        search_api_url: str = Field(
            default="http://127.0.0.1:8080/api/v1/retrieval/query/collection",
            description="RAG search API endpoint"
        )
        similarity_threshold: float = Field(
            default=0.3, description="Minimum similarity score for content inclusion"
        )
        max_context_length: int = Field(
            default=2000, description="Maximum characters of context to inject"
        )
        trigger_keywords: List[str] = Field(
            default=["cv", "resume", "experience", "skills", "work", "job", "education", "background"],
            description="Keywords that trigger RAG search"
        )
        chroma_db_path: str = Field(
            default="/app/backend/data/vector_db",
            description="Path to ChromaDB database"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.db_path = '/app/backend/data/webui.db'

    def _resolve_user_id(self, body: dict, user: dict = None) -> str:
        """
        Resolve user ID from multiple sources:
          1. User object (id, user_id, email, username)
          2. Body (user_id, uid, userId) 
          3. First system message metadata.user_id (if any future schema)
          4. Fallback to valves default (global_user)
        """
        if user:
            for key in ("id", "user_id", "email", "username"):
                val = user.get(key)
                if val:
                    return str(val)
        if isinstance(body, dict):
            for key in ("user_id", "uid", "userId"):
                if key in body and body[key]:
                    return str(body[key])
        # scan messages for embedded user id
        for msg in body.get("messages", []) if isinstance(body, dict) else []:
            if msg.get("role") == "system":
                meta = msg.get("metadata") or {}
                uid = meta.get("user_id") or meta.get("uid")
                if uid:
                    return str(uid)
        return "global_user"

    def _get_actual_user_id(self, resolved_user_id: str) -> str:
        """
        Map resolved user ID to actual database user ID.
        For global_user, look up the actual user ID from the database.
        """
        if resolved_user_id == "global_user":
            try:
                # Try to get the first user ID from the database
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM user LIMIT 1")
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    actual_user_id = result[0]
                    print(f"[RAG_INJECTION] Mapped global_user to actual user ID: {actual_user_id}")
                    return actual_user_id
                else:
                    print(f"[RAG_INJECTION] No users found in database")
                    return resolved_user_id
            except Exception as e:
                print(f"[RAG_INJECTION] Error looking up user ID: {e}")
                return resolved_user_id
        
        return resolved_user_id

    async def inlet(self, body: dict, user: dict = None) -> dict:
        """
        Automatically inject relevant document content via RAG search
        """
        print(f"[RAG_INJECTION] Filter called - enable_rag_injection: {self.valves.enable_rag_injection}")

        if not self.valves.enable_rag_injection:
            print(f"[RAG_INJECTION] Filter disabled, returning body unchanged")
            return body

        # Extract user info - require valid user ID
        resolved_user_id = self._resolve_user_id(body, user)
        actual_user_id = self._get_actual_user_id(resolved_user_id)
        
        if not actual_user_id:
            print(f"[RAG_INJECTION] No user ID found, returning body unchanged")
            return body
        print(f"[RAG_INJECTION] User ID: {resolved_user_id} -> {actual_user_id}")

        # Check if this is a relevant conversation
        messages = body.get("messages", [])
        if not messages:
            return body

        last_message = messages[-1]
        message_content = last_message.get("content", "")

        # Check if conversation would benefit from document context
        if not self._should_search_documents(message_content):
            print(f"[RAG_INJECTION] Query does not match trigger criteria: {message_content[:100]}...")
            return body

        print(f"[RAG_INJECTION] Triggering RAG search for: {message_content[:100]}...")

        try:
            # Perform RAG search
            relevant_content = await self._search_user_documents(actual_user_id, message_content)

            if relevant_content:
                print(f"[RAG_INJECTION] Found {len(relevant_content)} relevant documents")
                # Create context injection message
                context_message = self._create_context_message(relevant_content, message_content)

                # Inject as system message before user message
                system_message = {
                    "role": "system",
                    "content": context_message
                }

                # Insert before the last user message
                body["messages"].insert(-1, system_message)
                print(f"[RAG_INJECTION] Context injected successfully")
            else:
                print(f"[RAG_INJECTION] No relevant content found")

        except Exception as e:
            print(f"[RAG_INJECTION] Error: {e}")
            import traceback
            traceback.print_exc()

        return body

    def _should_search_documents(self, message_content: str) -> bool:
        """Determine if we should search documents for this message"""

        content_lower = message_content.lower()

        # Check for trigger keywords
        keyword_triggered = any(keyword in content_lower for keyword in self.valves.trigger_keywords)

        # Check for document-related questions
        document_questions = [
            "tell me about", "what is my", "review my", "analyze my",
            "what are my", "list my", "show me my", "describe my",
            "what can you find", "what do you know about my"
        ]

        question_triggered = any(phrase in content_lower for phrase in document_questions)

        return keyword_triggered or question_triggered

    async def _search_user_documents(self, user_id: str, query: str) -> Optional[List[Dict]]:
        """Search user documents using OpenWebUI's ChromaClient"""
        try:
            # Use OpenWebUI's ChromaClient to avoid instance conflicts
            from open_webui.retrieval.vector.dbs.chroma import ChromaClient
            
            # Use user-based collection name
            collection_name = f"user-{user_id}-documents"
            
            print(f"[RAG_INJECTION] Searching collection: {collection_name}")
            print(f"[RAG_INJECTION] Query: {query}")
            
            try:
                # Use OpenWebUI's ChromaClient directly
                chroma_client = ChromaClient()
                print(f"[RAG_INJECTION] Created OpenWebUI ChromaClient")
                
                # Query the collection using OpenWebUI's API format
                results = chroma_client.query(
                    collection_name=collection_name,
                    query_texts=[query],
                    n_results=3
                )
                
                print(f"[RAG_INJECTION] ChromaClient query results: {type(results)}")
                
                if results and "documents" in results:
                    documents = results["documents"][0] if results["documents"] else []
                    metadatas = results.get("metadatas", [[]])[0]
                    distances = results.get("distances", [[]])[0]
                    
                    print(f"[RAG_INJECTION] Found {len(documents)} documents")
                    
                    relevant_results = []
                    
                    for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                        # Calculate similarity from distance (lower distance = higher similarity)
                        similarity = max(0.0, 1.0 - distance)
                        
                        print(f"[RAG_INJECTION] Document {i}: similarity={similarity:.3f}, distance={distance:.3f}")
                        
                        if similarity >= self.valves.similarity_threshold:
                            relevant_results.append({
                                "content": doc,
                                "metadata": metadata or {},
                                "similarity": similarity
                            })
                    
                    print(f"[RAG_INJECTION] Found {len(relevant_results)} relevant results above threshold {self.valves.similarity_threshold}")
                    return relevant_results if relevant_results else None
                else:
                    print(f"[RAG_INJECTION] No documents in results: {results}")
                    return None
                
            except Exception as collection_error:
                print(f"[RAG_INJECTION] Collection access error: {collection_error}")
                import traceback
                traceback.print_exc()
                return None

        except Exception as e:
            print(f"[RAG_INJECTION] Search error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _create_context_message(self, search_results: List[Dict], original_query: str) -> str:
        """Create system message with relevant document context"""

        if not search_results:
            return ""

        message_parts = [
            "🔍 **RELEVANT DOCUMENT CONTEXT** for your query:",
            f"Query: \"{original_query}\"",
            ""
        ]

        total_length = 0
        context_added = 0

        # Sort by similarity (highest first)
        sorted_results = sorted(search_results, key=lambda x: x["similarity"], reverse=True)

        for item in sorted_results:
            content = item["content"]
            similarity = item["similarity"]
            
            # Limit context length
            if total_length + len(content) > self.valves.max_context_length:
                remaining_length = self.valves.max_context_length - total_length
                if remaining_length > 100:  # Only add if meaningful content can fit
                    content = content[:remaining_length] + "..."
                else:
                    break

            message_parts.append(f"**Document {context_added + 1}** (similarity: {similarity:.2f}):")
            message_parts.append(content)
            message_parts.append("")

            total_length += len(content)
            context_added += 1

            # Limit number of documents
            if context_added >= 3:
                break

        if context_added == 0:
            return ""

        message_parts.append("---")
        message_parts.append("Please use this context to inform your response when relevant.")

        return "\n".join(message_parts)
