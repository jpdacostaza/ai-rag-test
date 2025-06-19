"""
Database management module for the FastAPI LLM backend.
Handles Redis (caching & chat history) and ChromaDB (semantic memory) operations.
"""

import os
import logging
import chromadb
from chromadb.config import Settings
import redis
from sentence_transformers import SentenceTransformer
import json
from error_handler import RedisConnectionHandler, MemoryErrorHandler, safe_execute
from human_logging import log_service_status
import time
from database_manager import DatabaseManager
from cache_manager import CacheManager

# Global database manager instance
# (all methods and logic now in database_manager.py)
db_manager = DatabaseManager()

# Initialize cache manager
_cache_manager = None

def get_cache_manager():
    """Get or initialize cache manager."""
    global _cache_manager
    if _cache_manager is None:
        redis_client = db_manager.get_redis_client()
        if redis_client:
            _cache_manager = CacheManager(redis_client)
    return _cache_manager

# Convenience functions for backward compatibility
def get_redis_client():
    """Get Redis client (backward compatibility)."""
    return db_manager.get_redis_client()

def get_chroma_collection():
    """Get ChromaDB collection (backward compatibility)."""
    return db_manager.chroma_collection

def get_embedding_model():
    """Get embedding model (backward compatibility)."""
    return db_manager.embedding_model

def get_database_health():
    """Get overall database health status."""
    return db_manager.get_health_status()

# Database operations functions (simplified for better compatibility)

def get_cache(db_manager, cache_key, user_id="", request_id=""):
    """Get cached value from Redis with format validation."""
    cache_manager = get_cache_manager()
    if cache_manager:
        return cache_manager.get_with_validation(cache_key)
    
    # Fallback to direct Redis if cache manager unavailable
    def _get_cache_operation(redis_client):
        cached = redis_client.get(cache_key)
        if cached:
            logging.debug(f"[CACHE] HIT for key: {cache_key}")
            return str(cached)
        else:
            logging.debug(f"[CACHE] MISS for key: {cache_key}")
            return None
    
    return safe_execute(
        lambda: db_manager.execute_redis_operation(_get_cache_operation, f"get_cache({cache_key})"),
        fallback_value=None,
        error_handler=lambda e: RedisConnectionHandler.handle_redis_error(e, "get", cache_key, user_id, request_id)
    )

def set_cache(db_manager, cache_key, value, ttl=600, user_id="", request_id=""):
    """Set cached value in Redis with format validation."""
    cache_manager = get_cache_manager()
    if cache_manager:
        return cache_manager.set_with_validation(cache_key, value, ttl)
    
    # Fallback to direct Redis if cache manager unavailable
    def _set_cache_operation(redis_client):
        redis_client.setex(cache_key, ttl, value)
        logging.debug(f"[CACHE] SET for key: {cache_key}")
        return True
    
    return safe_execute(
        lambda: db_manager.execute_redis_operation(_set_cache_operation, f"set_cache({cache_key})"),
        fallback_value=False,
        error_handler=lambda e: RedisConnectionHandler.handle_redis_error(e, "set", cache_key, user_id, request_id)
    )

def store_chat_history(db_manager, user_id, message, max_history=20, request_id=""):
    """Store a chat message in Redis for a user (as a capped list) with automatic retry."""
    def _store_chat_operation(redis_client):
        key = f"chat_history:{user_id}"
        redis_client.rpush(key, json.dumps(message))
        redis_client.ltrim(key, -max_history, -1)
        logging.debug(f"[MEMORY] Stored chat message for user {user_id}")
        return True
    
    return safe_execute(
        lambda: db_manager.execute_redis_operation(_store_chat_operation, f"store_chat_history({user_id})"),
        fallback_value=False,
        error_handler=lambda e: RedisConnectionHandler.handle_redis_error(e, "store_chat", f"chat_history:{user_id}", user_id, request_id)
    )

def get_chat_history(db_manager, user_id, max_history=20, request_id=""):
    """Retrieve recent chat history for a user from Redis with automatic retry."""
    def _get_chat_operation(redis_client):
        key = f"chat_history:{user_id}"
        history = redis_client.lrange(key, -max_history, -1)
        parsed_history = [json.loads(m) for m in history]
        logging.debug(f"[MEMORY] Retrieved {len(parsed_history)} chat messages for user {user_id}")
        return parsed_history
    
    return safe_execute(
        lambda: db_manager.execute_redis_operation(_get_chat_operation, f"get_chat_history({user_id})"),
        fallback_value=[],
        error_handler=lambda e: RedisConnectionHandler.handle_redis_error(e, "get_chat", f"chat_history:{user_id}", user_id, request_id)
    )

def index_document_chunks(db_manager, user_id, doc_id, name, chunks, request_id=""):
    """Embed and index a list of pre-chunked text documents for a user in ChromaDB."""
    def _index_op():
        if not db_manager.is_chromadb_available():
            logging.warning("[CHROMADB] ChromaDB not available, skipping document indexing")
            return False
        
        if not db_manager.is_embeddings_available():
            logging.warning("[EMBEDDINGS] Embedding model not available, skipping document indexing")
            return False

        try:
            # Set show_progress_bar to False for cleaner logs
            embeddings = db_manager.embedding_model.encode(chunks, show_progress_bar=False).tolist()
            logging.info(f"Generated embeddings for {len(chunks)} chunks for doc_id={doc_id}")
        except Exception as e:
            logging.error(f"Failed to generate embeddings for doc_id={doc_id}: {e}")
            raise e

        chunk_ids = [f"chunk:{doc_id}:{i}" for i in range(len(chunks))]
        metadatas = [{"user_id": user_id, "doc_id": doc_id, "source": name, "chunk_index": i} for i in range(len(chunks))]
        
        try:
            db_manager.chroma_collection.add(
                embeddings=embeddings, 
                ids=chunk_ids, 
                metadatas=metadatas, 
                documents=chunks
            )
            logging.info(f"Successfully indexed {len(chunks)} chunks for doc_id={doc_id}, user_id={user_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to store chunks in ChromaDB for doc_id={doc_id}: {e}")
            raise e

    return safe_execute(
        _index_op,
        fallback_value=False,
        error_handler=lambda e: MemoryErrorHandler.handle_memory_error(e, "index_chunks", user_id, request_id)
    )

def index_user_document(db_manager, user_id, doc_id, name, text, chunk_size=1000, chunk_overlap=200, request_id=""):
    """
    Chunk, embed, and index a document for a specific user in ChromaDB.
    Note: This is a convenience wrapper. For pre-chunked data, use index_document_chunks.
    """
    try:
        from ai_tools import chunk_text
    except ImportError:
        logging.error("[CHUNKING] Failed to import chunk_text from ai_tools")
        return False
    
    chunks = chunk_text(text, chunk_size, chunk_overlap)
    if not chunks:
        logging.warning(f"No chunks created for doc_id={doc_id}, user_id={user_id}")
        return False
        
    return index_document_chunks(db_manager, user_id, doc_id, name, chunks, request_id)

def retrieve_user_memory(db_manager, user_id, query_embedding, n_results=5, request_id=""):
    """Retrieve relevant memory chunks for a user from ChromaDB."""
    def _retrieve_memory():
        if not db_manager.is_chromadb_available():
            logging.warning("[CHROMADB] ChromaDB not available, returning empty memory")
            return []
        
        results = db_manager.chroma_collection.query(
            query_embeddings=query_embedding, 
            n_results=n_results, 
            where={"user_id": user_id}, 
            include=["documents", "metadatas", "distances"]
        )
        
        docs = results.get("documents", [[]])[0] if results else []
        metadatas = results.get("metadatas", [[]])[0] if results else []
        distances = results.get("distances", [[]])[0] if results else []
        
        logging.debug(f"Retrieved {len(docs)} memory chunks for user_id={user_id}")
        
        # Format results properly for RAG consumption
        formatted_results = []
        for i, doc in enumerate(docs):
            metadata = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else 1.0
            
            formatted_results.append({
                "content": doc,
                "score": max(0.0, 1.0 - distance),  # Convert distance to similarity score
                "document_id": metadata.get("doc_id", f"unknown_{i}"),
                "metadata": {
                    "source": metadata.get("source", "unknown"),
                    "chunk_index": metadata.get("chunk_index", i),
                    "user_id": metadata.get("user_id", user_id),
                    "distance": distance
                }
            })
            
            logging.debug(f"Chunk {i+1}: {doc[:100]}...")
        
        if not formatted_results:
            logging.debug(f"No relevant memory found for user_id={user_id}")
        
        return formatted_results
    
    return safe_execute(
        _retrieve_memory,
        fallback_value=[],
        error_handler=lambda e: MemoryErrorHandler.handle_memory_error(e, "retrieve", user_id, request_id)
    )

def get_embedding(db_manager, text, request_id=""):
    """Get embedding for text."""
    def _get_embedding():
        if not db_manager.is_embeddings_available():
            logging.warning("[EMBEDDINGS] Embedding model not available")
            return None
        
        return db_manager.embedding_model.encode([text])
    
    return safe_execute(
        _get_embedding,
        fallback_value=None,
        error_handler=lambda e: logging.error(f"[EMBEDDINGS] Failed to generate embedding: {e}")
    )
