"""
Migration script to upgrade to the improved database manager.
"""

import asyncio
import shutil
from pathlib import Path
from typing import Optional
import json

from database_manager_improved import ImprovedDatabaseManager
from human_logging import log_service_status

async def migrate_database_manager():
    """Migrate to the improved database manager implementation."""
    
    log_service_status(
        "migration",
        "info",
        "Starting database manager migration"
    )
    
    # Backup existing data
    backup_dir = Path("backups") / "database_migration"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize new manager
        new_manager = ImprovedDatabaseManager()
        await new_manager.initialize()
        
        # Migrate Redis data
        await migrate_redis_data(new_manager)
        
        # Migrate ChromaDB data
        await migrate_chromadb_data(new_manager)
        
        log_service_status(
            "migration",
            "info",
            "Successfully migrated to improved database manager"
        )
        
        return True
        
    except Exception as e:
        log_service_status(
            "migration",
            "error",
            f"Migration failed: {str(e)}"
        )
        return False
        
async def migrate_redis_data(new_manager: ImprovedDatabaseManager):
    """Migrate Redis data to new format."""
    try:
        # Connect to old Redis
        old_redis = redis.Redis(
            host=new_manager.config.redis_host,
            port=new_manager.config.redis_port,
            db=0,
            decode_responses=True
        )
        
        # Get all keys
        keys = old_redis.keys("chat:*")
        
        for key in keys:
            # Get data from old Redis
            data = old_redis.lrange(key, 0, -1)
            
            # Migrate each chat history entry
            for entry in data:
                try:
                    entry_data = json.loads(entry)
                    await new_manager.store_chat_history(
                        chat_id=key.split(":")[1],
                        message=entry_data,
                        metadata=entry_data.get("metadata", {})
                    )
                except json.JSONDecodeError:
                    log_service_status(
                        "migration",
                        "warning",
                        f"Skipping invalid chat entry: {entry}"
                    )
                    continue
                    
        log_service_status(
            "migration",
            "info",
            f"Migrated {len(keys)} chat histories"
        )
        
    except Exception as e:
        log_service_status(
            "migration",
            "error",
            f"Redis migration error: {str(e)}"
        )
        raise
        
async def migrate_chromadb_data(new_manager: ImprovedDatabaseManager):
    """Migrate ChromaDB data to new format."""
    try:
        if not new_manager.chroma_db or not new_manager.chroma_db.is_connected():
            raise RuntimeError("New ChromaDB client not connected")
            
        # Get collections from old ChromaDB
        collections = new_manager.chroma_db.list_collections()
        
        for collection in collections:
            # Create collection in new format
            new_collection = new_manager.chroma_db.get_or_create_collection(
                collection.name,
                metadata=collection.metadata
            )
            
            # Get all documents from old collection
            documents = collection.get()
            if documents and documents['documents']:
                # Add documents to new collection
                new_collection.add(
                    documents=documents['documents'],
                    metadatas=documents['metadatas'],
                    ids=documents['ids']
                )
                
        log_service_status(
            "migration",
            "info",
            f"Migrated {len(collections)} ChromaDB collections"
        )
        
    except Exception as e:
        log_service_status(
            "migration",
            "error",
            f"ChromaDB migration error: {str(e)}"
        )
        raise

if __name__ == "__main__":
    asyncio.run(migrate_database_manager())
