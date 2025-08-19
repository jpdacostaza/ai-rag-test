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
            default=1, description="Filter priority (runs before other filters for maximum impact)"
        )
        enable_rag_injection: bool = Field(
            default=True, description="Enable automatic RAG content injection"
        )
        search_api_url: str = Field(
            default="http://127.0.0.1:8080/api/v1/retrieval/query/collection",
            description="RAG search API endpoint"
        )
        similarity_threshold: float = Field(
            default=0.2, description="Minimum similarity score for content inclusion"
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
                print(f"[RAG_INJECTION] Context message preview: {context_message[:300]}...")

                # Inject as the FIRST system message to ensure maximum visibility
                system_message = {
                    "role": "system", 
                    "content": context_message
                }

                # Insert at the very beginning to ensure it's seen first
                body["messages"].insert(0, system_message)
                print(f"[RAG_INJECTION] Context injected successfully at position 0")
                print(f"[RAG_INJECTION] Total messages after injection: {len(body['messages'])}")
                
                # Also add a shorter reminder right before the user message
                reminder_message = {
                    "role": "system",
                    "content": "IMPORTANT: The user has uploaded their CV/resume. Use the document context provided above to answer questions about their background, experience, and skills. Do NOT say you cannot access their information."
                }
                body["messages"].insert(-1, reminder_message)
                print(f"[RAG_INJECTION] Added reminder message before user query")
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
        """Search user documents using OpenWebUI's ChromaClient with proper error handling"""
        try:
            # Use OpenWebUI's ChromaClient which is already configured
            from open_webui.retrieval.vector.dbs.chroma import ChromaClient
            
            # Use user-based collection name
            collection_name = f"user-{user_id}-documents"
            
            print(f"[RAG_INJECTION] Searching collection: {collection_name}")
            print(f"[RAG_INJECTION] Query: {query}")
            
            try:
                # Create ChromaClient using OpenWebUI's implementation
                chroma_client = ChromaClient()
                print(f"[RAG_INJECTION] Created OpenWebUI ChromaClient")
                
                # Check if collection exists
                if not chroma_client.has_collection(collection_name):
                    print(f"[RAG_INJECTION] Collection {collection_name} does not exist")
                    return None
                
                print(f"[RAG_INJECTION] Collection {collection_name} exists")
                
                # Get documents from collection using search method
                # This is the working method we've verified before
                try:
                    search_results = chroma_client.search(
                        collection_name=collection_name,
                        query=query,  # Let ChromaClient handle embedding generation
                        k=3
                    )
                    
                    print(f"[RAG_INJECTION] Search completed, results type: {type(search_results)}")
                    
                    # Process results - OpenWebUI ChromaClient returns different format
                    if hasattr(search_results, 'documents') and search_results.documents:
                        documents = search_results.documents[0] if search_results.documents else []
                        distances = search_results.distances[0] if hasattr(search_results, 'distances') and search_results.distances else []
                        metadatas = search_results.metadatas[0] if hasattr(search_results, 'metadatas') and search_results.metadatas else []
                    elif isinstance(search_results, list):
                        # Handle list format if returned
                        documents = search_results
                        distances = [0.5] * len(documents)  # Default distance
                        metadatas = [{}] * len(documents)  # Default metadata
                    else:
                        print(f"[RAG_INJECTION] Unexpected result format: {search_results}")
                        return None
                    
                    print(f"[RAG_INJECTION] Found {len(documents)} documents")
                    
                    relevant_results = []
                    
                    for i, doc in enumerate(documents):
                        distance = distances[i] if i < len(distances) else 0.5
                        metadata = metadatas[i] if i < len(metadatas) else {}
                        
                        # Convert distance to similarity (distance is already in 0-1 range for OpenWebUI)
                        similarity = 1.0 - distance if distance <= 1.0 else distance
                        
                        print(f"[RAG_INJECTION] Document {i}: similarity={similarity:.3f}")
                        print(f"[RAG_INJECTION] Document {i} content preview: {doc[:200]}...")
                        
                        if similarity >= self.valves.similarity_threshold:
                            relevant_results.append({
                                "content": doc,
                                "metadata": metadata or {},
                                "similarity": similarity
                            })
                    
                    print(f"[RAG_INJECTION] Found {len(relevant_results)} relevant results above threshold {self.valves.similarity_threshold}")
                    return relevant_results if relevant_results else None
                    
                except Exception as search_error:
                    print(f"[RAG_INJECTION] Search method error: {search_error}")
                    # Try alternative query method
                    try:
                        print(f"[RAG_INJECTION] Trying direct query method")
                        query_results = chroma_client.query(
                            collection_name=collection_name,
                            query_texts=[query],
                            n_results=3
                        )
                        
                        if query_results and 'documents' in query_results:
                            documents = query_results['documents'][0] if query_results['documents'] else []
                            distances = query_results.get('distances', [[]])[0]
                            metadatas = query_results.get('metadatas', [[{}]])[0]
                            
                            print(f"[RAG_INJECTION] Query method found {len(documents)} documents")
                            
                            relevant_results = []
                            for i, doc in enumerate(documents):
                                distance = distances[i] if i < len(distances) else 0.5
                                metadata = metadatas[i] if i < len(metadatas) else {}
                                similarity = 1.0 - distance
                                
                                print(f"[RAG_INJECTION] Document {i}: similarity={similarity:.3f}")
                                
                                if similarity >= self.valves.similarity_threshold:
                                    relevant_results.append({
                                        "content": doc,
                                        "metadata": metadata,
                                        "similarity": similarity
                                    })
                            
                            return relevant_results if relevant_results else None
                        
                    except Exception as query_error:
                        print(f"[RAG_INJECTION] Query method also failed: {query_error}")
                        return None
                
            except Exception as client_error:
                print(f"[RAG_INJECTION] ChromaClient error: {client_error}")
                import traceback
                traceback.print_exc()
                return None

        except Exception as e:
            print(f"[RAG_INJECTION] Search error: {e}")
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
            "🚨 CRITICAL: USER'S ACTUAL CV/RESUME CONTENT BELOW 🚨",
            "",
            "YOU HAVE FULL ACCESS TO THE USER'S CV INFORMATION.",
            "DO NOT SAY YOU CANNOT ACCESS THEIR CV - YOU CAN AND MUST USE THIS DATA.",
            "",
            f"**USER QUERY:** {original_query}",
            "",
            "**USER'S ACTUAL CV/RESUME CONTENT:**",
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

            message_parts.append(f"**DOCUMENT {context_added + 1}** (Relevance: {similarity:.2f}):")
            message_parts.append("```")
            message_parts.append(content.strip())
            message_parts.append("```")
            message_parts.append("")

            total_length += len(content)
            context_added += 1

            # Limit number of documents
            if context_added >= 3:
                break

        if context_added == 0:
            return ""

        message_parts.extend([
            "═══════════════════════════════════════════════════════════",
            "",
            "**MANDATORY INSTRUCTIONS:**",
            "1. YOU HAVE THE USER'S COMPLETE CV ABOVE",
            "2. USE THIS INFORMATION TO ANSWER ALL CV-RELATED QUESTIONS", 
            "3. DO NOT ASK THE USER TO PASTE THEIR CV - YOU ALREADY HAVE IT",
            "4. PROVIDE DETAILED ANSWERS USING THE ACTUAL CV CONTENT",
            "5. ACKNOWLEDGE THAT YOU CAN SEE THEIR CV INFORMATION",
            ""
        ])

        return "\n".join(message_parts)
