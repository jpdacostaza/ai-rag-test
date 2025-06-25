import json
import logging

from utilities.ai_tools import chunk_text
from cache_manager import CacheManager
from database_manager import DatabaseManager
from error_handler import MemoryErrorHandler
from error_handler import RedisConnectionHandler
from error_handler import safe_execute

"""
Database management module for the FastAPI LLM backend.
Handles Redis (caching & chat history) and chromadb (semantic memory) operations.
"""


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
    """Get chromadb collection (backward compatibility)."""
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
        error_handler=lambda e: RedisConnectionHandler.handle_redis_error(
            e, "get", cache_key, user_id, request_id
        ),
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
        error_handler=lambda e: RedisConnectionHandler.handle_redis_error(
            e, "set", cache_key, user_id, request_id
        ),
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
        lambda: db_manager.execute_redis_operation(
            _store_chat_operation, f"store_chat_history({user_id})"
        ),
        fallback_value=False,
        error_handler=lambda e: RedisConnectionHandler.handle_redis_error(
            e, "store_chat", f"chat_history:{user_id}", user_id, request_id
        ),
    )


async def store_chat_history_async(db_manager, user_id, message, max_history=20, request_id=""):
    """Store a chat message in Redis for a user (as a capped list) with automatic retry (async version)."""

    def _store_chat_operation(redis_client):
        key = f"chat_history:{user_id}"
        redis_client.rpush(key, json.dumps(message))
        redis_client.ltrim(key, -max_history, -1)
        logging.debug(f"[MEMORY] Stored chat message for user {user_id}")
        return True

    try:
        result = await db_manager.execute_redis_operation(
            _store_chat_operation, f"store_chat_history({user_id})"
        )
        return result
    except Exception as e:
        logging.warning(f"[REDIS] Failed to store chat history for user {user_id}: {e}")
        return False


def get_chat_history(db_manager, user_id, max_history=20, request_id=""):
    """Retrieve recent chat history for a user from Redis with automatic retry."""

    def _get_chat_operation(redis_client):
        key = f"chat_history:{user_id}"
        history = redis_client.lrange(key, -max_history, -1)
        parsed_history = [json.loads(m) for m in history]
        logging.debug(f"[MEMORY] Retrieved {len(parsed_history)} chat messages for user {user_id}")
        return parsed_history

    return safe_execute(
        lambda: db_manager.execute_redis_operation(
            _get_chat_operation, f"get_chat_history({user_id})"
        ),
        fallback_value=[],
        error_handler=lambda e: RedisConnectionHandler.handle_redis_error(
            e, "get_chat", f"chat_history:{user_id}", user_id, request_id
        ),
    )


async def get_chat_history_async(db_manager, user_id, max_history=20, request_id=""):
    """Retrieve recent chat history for a user from Redis with automatic retry (async version)."""

    def _get_chat_operation(redis_client):
        key = f"chat_history:{user_id}"
        history = redis_client.lrange(key, -max_history, -1)
        parsed_history = [json.loads(m) for m in history]
        logging.debug(f"[MEMORY] Retrieved {len(parsed_history)} chat messages for user {user_id}")
        return parsed_history

    try:
        result = await db_manager.execute_redis_operation(
            _get_chat_operation, f"get_chat_history({user_id})"
        )
        return result
    except Exception as e:
        logging.warning(f"[REDIS] Failed to get chat history for user {user_id}: {e}")
        return []


def index_document_chunks(db_manager, user_id, doc_id, name, chunks, request_id=""):
    """Embed and index a list of pre-chunked text documents for a user in chromadb."""

    def _index_op():
        if not db_manager.is_chromadb_available():
            logging.warning("[CHROMADB] chromadb not available, skipping document indexing")
            return False

        if not db_manager.is_embeddings_available():
            logging.warning(
                "[EMBEDDINGS] Embedding model not available, skipping document indexing"
            )
            return False

        try:
            # Set show_progress_bar to False for cleaner logs
            embeddings = db_manager.embedding_model.encode(chunks, show_progress_bar=False).tolist()
            logging.info(f"Generated embeddings for {len(chunks)} chunks for doc_id={doc_id}")
        except Exception as e:
            logging.error(f"Failed to generate embeddings for doc_id={doc_id}: {e}")
            raise e

        chunk_ids = [f"chunk:{doc_id}:{i}" for i in range(len(chunks))]
        metadatas = [
            {"user_id": user_id, "doc_id": doc_id, "source": name, "chunk_index": i}
            for i in range(len(chunks))
        ]

        try:
            db_manager.chroma_collection.add(
                embeddings=embeddings, ids=chunk_ids, metadatas=metadatas, documents=chunks
            )
            logging.info(
                f"Successfully indexed {len(chunks)} chunks for doc_id={doc_id}, user_id={user_id}"
            )
            return True
        except Exception as e:
            logging.error(f"Failed to store chunks in chromadb for doc_id={doc_id}: {e}")
            raise e

    return safe_execute(
        _index_op,
        fallback_value=False,
        error_handler=lambda e: MemoryErrorHandler.handle_memory_error(
            e, "index_chunks", user_id, request_id
        ),
    )


def index_user_document(
    db_manager, user_id, doc_id, name, text, chunk_size=1000, chunk_overlap=200, request_id=""
):
    """
    Chunk, embed, and index a document for a specific user in chromadb.
    Note: This is a convenience wrapper. For pre-chunked data, use index_document_chunks."""
    
    try:
        pass  # Placeholder for try block content
    except ImportError:
        logging.error("[CHUNKING] Failed to import chunk_text from utilities.ai_tools")
        return False

    chunks = chunk_text(text, chunk_size, chunk_overlap)
    if not chunks:
        logging.warning(f"No chunks created for doc_id={doc_id}, user_id={user_id}")
        return False

    return index_document_chunks(db_manager, user_id, doc_id, name, chunks, request_id)


def retrieve_user_memory(db_manager, user_id, query_embedding, n_results=5, request_id=""):
    """Retrieve relevant memory chunks for a user from chromadb."""
    
    # Add logging for memory retrieval
    logging.debug(f"retrieve_user_memory called with user_id={user_id}")
    
    def _retrieve_memory():
        try:
            # Synchronous check for ChromaDB availability
            if db_manager.chroma_client is None or db_manager.chroma_collection is None:
                logging.warning("[CHROMADB] chromadb not available, returning empty memory")
                return []
        except Exception as e:
            logging.warning(f"[CHROMADB] Error checking availability: {str(e)}, returning empty memory")
            return []

        # Enhanced logging for debugging
        logging.info(f"[MEMORY] 🔍 Starting memory retrieval for user_id={user_id}, n_results={n_results}")
        
        # Ensure query_embedding is properly formatted
        logging.debug(f"[MEMORY] 📊 Query embedding type: {type(query_embedding)}")
        
        if query_embedding is None:
            logging.error("[MEMORY] ❌ Query embedding is None")
            return []
        elif hasattr(query_embedding, 'tolist'):
            embedding_list = query_embedding.tolist()
            logging.debug(f"[MEMORY] 📊 Converted numpy array to list, shape: {query_embedding.shape if hasattr(query_embedding, 'shape') else 'unknown'}")
        elif hasattr(query_embedding, '__iter__') and not isinstance(query_embedding, str):
            embedding_list = list(query_embedding)
            logging.debug(f"[MEMORY] 📊 Converted iterable to list, length: {len(embedding_list)}")
        else:
            logging.error(f"[MEMORY] ❌ Invalid embedding format: {type(query_embedding)}")
            return []

        logging.debug(f"[MEMORY] 📐 Query embedding dimension: {len(embedding_list)}")

        results = db_manager.chroma_collection.query(
            query_embeddings=[embedding_list],
            n_results=n_results,
            where={"user_id": user_id},
            include=["documents", "metadatas", "distances"],
        )

        logging.info(f"[MEMORY] 📊 chromadb query results: {results}")

        docs = results.get("documents", [[]])[0] if results else []
        metadatas = results.get("metadatas", [[]])[0] if results else []
        distances = results.get("distances", [[]])[0] if results else []
        
        logging.info(f"[MEMORY] ✅ Retrieved {len(docs)} memory chunks for user_id={user_id}")

        # Use len() check instead of boolean check to avoid numpy array truth value error
        if len(docs) > 0:
            for i, (doc, metadata, distance) in enumerate(zip(docs, metadatas, distances)):
                similarity = 1 - distance if distance is not None else 0.0
                logging.info(f"[MEMORY] 📄 Chunk {i+1}: similarity={similarity:.4f}, metadata={metadata}")
                logging.debug(f"[MEMORY] 📄 Content: {doc[:100]}...")
        else:
            logging.warning(f"[MEMORY] ⚠️ No relevant memory found for user_id={user_id}")

        # Return formatted results for semantic search
        formatted_results = []
        for i, (doc, metadata, distance) in enumerate(zip(docs, metadatas, distances)):
            similarity = 1 - distance if distance is not None else 0.0
            formatted_results.append({
                "content": doc,
                "metadata": metadata,
                "similarity": similarity,
                "distance": distance,
                "rank": i + 1
            })

        logging.info(f"[MEMORY] 📋 Returning {len(formatted_results)} formatted results")
        return formatted_results

    return safe_execute(
        _retrieve_memory,
        fallback_value=[],
        error_handler=lambda e: MemoryErrorHandler.handle_memory_error(
            e, "retrieve", user_id, request_id
        ),
    )


def get_embedding(db_manager, text, request_id=""):
    """Get embedding for text."""
    import logging
    logging.critical(f"🔍 [DATABASE] get_embedding called with text: '{text[:50]}...'")

    def _get_embedding():
        if not db_manager.is_embeddings_available():
            logging.warning("[EMBEDDINGS] Embedding model not available")
            logging.critical(f"❌ [DATABASE] Embedding model not available")
            return None
            
        logging.critical(f"🔍 [DATABASE] Generating embedding using model: {type(db_manager.embedding_model)}")
        # Get the embedding and return the first element (single text input)
        embedding = db_manager.embedding_model.encode([text])
        logging.critical(f"🔍 [DATABASE] Raw embedding result: type={type(embedding)}, shape={getattr(embedding, 'shape', 'no shape')}")
        
        if embedding is not None:
            logging.critical(f"🔍 [DATABASE] Embedding is not None, length check: {len(embedding) if hasattr(embedding, '__len__') else 'no len'}")
            if hasattr(embedding, '__len__') and len(embedding) > 0:
                result = embedding[0]
                logging.critical(f"🔍 [DATABASE] Returning embedding[0]: type={type(result)}, shape={getattr(result, 'shape', 'no shape')}")
                return result
            else:
                logging.critical(f"❌ [DATABASE] Embedding has no length or is empty")
                return None
        else:
            logging.critical(f"❌ [DATABASE] Embedding is None")
            return None

    return safe_execute(
        _get_embedding,
        fallback_value=None,
        error_handler=lambda e: (
            logging.error(f"[EMBEDDINGS] Failed to generate embedding: {e}"),
            logging.critical(f"❌ [DATABASE] safe_execute caught error: {e}")
        )[0],  # Use first element to avoid tuple return
    )
