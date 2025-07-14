"""
Vector Service
=============

Focused service class for vector database operations, replacing direct ChromaDB usage.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import time

from utilities.simple_error_handling import handle_errors


class VectorService:
    """
    Service class for vector database operations with proper error handling.
    """
    
    def __init__(self, chroma_client=None):
        """
        Initialize Vector service.
        
        Args:
            chroma_client: ChromaDB client instance, falls back to db_manager if None
        """
        self.chroma_client = chroma_client
        if not self.chroma_client:
            # Fallback to global db_manager for gradual migration
            try:
                from services.database_manager import db_manager
                self.chroma_client = db_manager.chroma_client if db_manager else None
            except Exception as e:
                logging.warning(f"Could not get ChromaDB client from db_manager: {e}")
                self.chroma_client = None

    @handle_errors("vector_store_embeddings", default_value=False)
    def store_embeddings(
        self, 
        collection_name: str, 
        documents: List[str], 
        embeddings: List[List[float]], 
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Store embeddings in vector database.
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            embeddings: List of embedding vectors
            metadata: Optional metadata for each document
            ids: Optional custom IDs for documents
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.chroma_client:
            logging.error("ChromaDB client not available")
            return False
            
        try:
            collection = self.chroma_client.get_or_create_collection(name=collection_name)
            
            # Generate IDs if not provided
            if not ids:
                ids = [f"doc_{collection_name}_{i}_{int(time.time())}" for i in range(len(documents))]
                
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadata,
                ids=ids
            )
            
            logging.info(f"Stored {len(documents)} embeddings in collection {collection_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to store embeddings in {collection_name}: {e}")
            return False

    @handle_errors("vector_search", default_value=[])
    def search(
        self, 
        collection_name: str, 
        query_embedding: List[float], 
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in the database.
        
        Args:
            collection_name: Name of the collection to search
            query_embedding: Query embedding vector
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            List of search results with documents, distances, and metadata
        """
        if not self.chroma_client:
            logging.error("ChromaDB client not available")
            return []
            
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            
            # Format results
            formatted_results = []
            if results and results.get('documents') and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        'document': doc,
                        'distance': results['distances'][0][i] if results.get('distances') else 0.0,
                        'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
                        'id': results['ids'][0][i] if results.get('ids') else f"result_{i}"
                    }
                    formatted_results.append(result)
                    
            logging.debug(f"Vector search in {collection_name} returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logging.error(f"Vector search failed in {collection_name}: {e}")
            return []

    @handle_errors("vector_get_collection", default_value=None)
    def get_collection(self, collection_name: str):
        """
        Get a ChromaDB collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection object or None if not found
        """
        if not self.chroma_client:
            return None
            
        try:
            return self.chroma_client.get_collection(name=collection_name)
        except Exception as e:
            logging.error(f"Failed to get collection {collection_name}: {e}")
            return None

    @handle_errors("vector_create_collection", default_value=None)
    def create_collection(self, collection_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Create a new ChromaDB collection.
        
        Args:
            collection_name: Name of the collection
            metadata: Optional collection metadata
            
        Returns:
            Collection object or None if creation failed
        """
        if not self.chroma_client:
            return None
            
        try:
            return self.chroma_client.create_collection(
                name=collection_name,
                metadata=metadata
            )
        except Exception as e:
            logging.error(f"Failed to create collection {collection_name}: {e}")
            return None

    @handle_errors("vector_delete_collection", default_value=False)
    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a ChromaDB collection.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.chroma_client:
            return False
            
        try:
            self.chroma_client.delete_collection(name=collection_name)
            logging.info(f"Deleted collection {collection_name}")
            return True
        except Exception as e:
            logging.error(f"Failed to delete collection {collection_name}: {e}")
            return False

    @handle_errors("vector_list_collections", default_value=[])
    def list_collections(self) -> List[str]:
        """
        List all collections in the vector database.
        
        Returns:
            List of collection names
        """
        if not self.chroma_client:
            return []
            
        try:
            collections = self.chroma_client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logging.error(f"Failed to list collections: {e}")
            return []

    @handle_errors("vector_collection_count", default_value=0)
    def get_collection_count(self, collection_name: str) -> int:
        """
        Get the number of documents in a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Number of documents in the collection
        """
        if not self.chroma_client:
            return 0
            
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            return collection.count()
        except Exception as e:
            logging.error(f"Failed to get count for collection {collection_name}: {e}")
            return 0

    @handle_errors("vector_delete_documents", default_value=False)
    def delete_documents(self, collection_name: str, ids: List[str]) -> bool:
        """
        Delete specific documents from a collection.
        
        Args:
            collection_name: Name of the collection
            ids: List of document IDs to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.chroma_client:
            return False
            
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            collection.delete(ids=ids)
            logging.info(f"Deleted {len(ids)} documents from collection {collection_name}")
            return True
        except Exception as e:
            logging.error(f"Failed to delete documents from {collection_name}: {e}")
            return False

    @handle_errors("vector_health_check", default_value=False)
    def health_check(self) -> bool:
        """
        Check vector database health.
        
        Returns:
            bool: True if vector DB is healthy, False otherwise
        """
        if not self.chroma_client:
            return False
            
        try:
            # Simple health check by listing collections
            self.chroma_client.list_collections()
            return True
        except Exception as e:
            logging.error(f"Vector database health check failed: {e}")
            return False

    @handle_errors("vector_get_stats", default_value={})
    def get_stats(self) -> Dict[str, Any]:
        """
        Get vector database statistics.
        
        Returns:
            Dict with vector DB stats
        """
        if not self.chroma_client:
            return {"status": "unavailable", "connected": False}
            
        try:
            collections = self.list_collections()
            total_docs = 0
            
            for col_name in collections:
                total_docs += self.get_collection_count(col_name)
                
            return {
                "status": "connected",
                "connected": True,
                "total_collections": len(collections),
                "total_documents": total_docs,
                "collections": collections
            }
        except Exception as e:
            logging.error(f"Vector stats failed: {e}")
            return {"status": "error", "connected": False, "error": str(e)}
