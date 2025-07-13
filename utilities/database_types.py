"""
Type definitions and interfaces for the database manager.
"""

from typing import Protocol, Optional, Any, Dict, List, TypeVar, Generic
from datetime import datetime
import chromadb
import asyncio

from utilities.connection_factory import get_connection_factory

T = TypeVar("T")


class DatabaseClient(Protocol):
    """Protocol for database clients."""

    def connect(self) -> bool:
        """Connect to the database."""
        ...

    def disconnect(self) -> None:
        """Disconnect from the database."""
        ...

    def is_connected(self) -> bool:
        """Check if connected to the database."""
        ...


class CacheManager(Generic[T]):
    """Generic cache manager with memory-aware caching."""

    def __init__(self, max_size: int = 1000):
        """TODO: Add proper docstring for __init__."""
        self.cache: Dict[str, T] = {}
        self.max_size = max_size
        self.access_times: Dict[str, datetime] = {}

    def get(self, key: str) -> Optional[T]:
        """Get item from cache."""
        if key in self.cache:
            self.access_times[key] = datetime.now()
            return self.cache[key]
        return None

    def set(self, key: str, value: T) -> None:
        """Set item in cache with memory pressure awareness."""
        if len(self.cache) >= self.max_size:
            # Remove oldest item
            oldest_key = min(self.access_times.items(), key=lambda x: x[1])[0]
            del self.cache[oldest_key]
            del self.access_times[oldest_key]

        self.cache[key] = value
        self.access_times[key] = datetime.now()

    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        self.access_times.clear()


class ChromaDBClient:
    """Type-safe ChromaDB client wrapper using DatabaseConnectionFactory."""

    def __init__(self, settings: Optional[chromadb.Settings] = None):
        """Initialize ChromaDB client with DatabaseConnectionFactory."""
        self.settings = settings
        self.client: Optional[chromadb.Client] = None
        self.collections: Dict[str, chromadb.Collection] = {}
        self.connection_factory = get_connection_factory()

    async def connect(self) -> bool:
        """Connect to ChromaDB using DatabaseConnectionFactory."""
        try:
            self.client = await self.connection_factory.create_chroma_connection(connection_name="database_types_client")
            return self.client is not None
        except Exception:
            return False

    def disconnect(self) -> None:
        """Disconnect from ChromaDB."""
        if self.client:
            # ChromaDB doesn't have a close method, but we'll prepare for future
            pass

    def is_connected(self) -> bool:
        """Check if connected to ChromaDB."""
        return self.client is not None

    def get_or_create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> chromadb.Collection:
        """Get or create a ChromaDB collection."""
        if not self.client:
            raise RuntimeError("Not connected to ChromaDB")

        if name not in self.collections:
            self.collections[name] = self.client.get_or_create_collection(name=name, metadata=metadata or {})

        return self.collections[name]

    def list_collections(self) -> List[chromadb.Collection]:
        """List all collections."""
        if not self.client:
            raise RuntimeError("Not connected to ChromaDB")

        return self.client.list_collections()

    @staticmethod
    async def create_client() -> Optional['ChromaDBClient']:
        """Factory method to create a connected ChromaDB client."""
        client = ChromaDBClient()
        if await client.connect():
            return client
        return None


class DatabaseManagerTypes:
    """Type definitions for database manager."""

    ChromaClient = chromadb.Client
    ChromaCollection = chromadb.Collection
    ChromaSettings = chromadb.Settings
