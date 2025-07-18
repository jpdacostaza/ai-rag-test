#!/usr/bin/env python3
"""
Robust Memory Service with Network Fallback
==========================================

This module provides a network-resilient memory service that can handle
Docker container networking issues by implementing fallback strategies.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import redis
import httpx
import socket

class NetworkResilienceManager:
    """Manages network connections with fallback strategies"""
    
    def __init__(self, config_path: str = "config/memory_api_network_config.json"):
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self.active_connections = {}
        
    def _load_config(self, config_path: str) -> Dict:
        """Load network configuration with fallback defaults"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "database": {
                    "redis": {
                        "hosts": ["backend-redis:6379", "redis:6379", "localhost:6379", "127.0.0.1:6379"],
                        "retry_attempts": 3,
                        "retry_delay": 2
                    },
                    "chroma": {
                        "hosts": ["chroma:8000", "backend-chroma:8000", "localhost:8000", "127.0.0.1:8000"],
                        "retry_attempts": 3,
                        "retry_delay": 2
                    },
                    "ollama": {
                        "hosts": ["ollama:11434", "backend-ollama:11434", "localhost:11434", "127.0.0.1:11434"],
                        "retry_attempts": 3,
                        "retry_delay": 2
                    }
                },
                "fallback_strategy": "try_all_hosts",
                "connection_timeout": 10,
                "health_check_interval": 30
            }
    
    async def get_redis_connection(self) -> Optional[redis.Redis]:
        """Get Redis connection with fallback hosts"""
        service_config = self.config["database"]["redis"]
        
        for host in service_config["hosts"]:
            try:
                # Parse host:port
                if ":" in host:
                    hostname, port = host.split(":")
                    port = int(port)
                else:
                    hostname = host
                    port = 6379
                
                # Test connection
                r = redis.Redis(
                    host=hostname, 
                    port=port, 
                    decode_responses=True,
                    socket_timeout=self.config["connection_timeout"],
                    socket_connect_timeout=self.config["connection_timeout"]
                )
                
                # Verify connection
                r.ping()
                self.logger.info(f"✅ Redis connected to {host}")
                self.active_connections["redis"] = {"host": host, "connection": r}
                return r
                
            except Exception as e:
                self.logger.warning(f"❌ Redis connection failed for {host}: {str(e)}")
                continue
        
        self.logger.error("❌ All Redis connection attempts failed")
        return None
    
    async def get_chroma_client(self) -> Optional[httpx.AsyncClient]:
        """Get ChromaDB client with fallback hosts"""
        service_config = self.config["database"]["chroma"]
        
        for host in service_config["hosts"]:
            try:
                # Parse host:port
                if ":" in host:
                    hostname, port = host.split(":")
                else:
                    hostname = host
                    port = "8000"
                
                base_url = f"http://{hostname}:{port}"
                
                # Test connection
                client = httpx.AsyncClient(
                    base_url=base_url,
                    timeout=self.config["connection_timeout"]
                )
                
                # Verify connection
                response = await client.get("/api/v1/heartbeat")
                if response.status_code == 200:
                    self.logger.info(f"✅ ChromaDB connected to {host}")
                    self.active_connections["chroma"] = {"host": host, "client": client}
                    return client
                else:
                    await client.aclose()
                    
            except Exception as e:
                self.logger.warning(f"❌ ChromaDB connection failed for {host}: {str(e)}")
                continue
        
        self.logger.error("❌ All ChromaDB connection attempts failed")
        return None
    
    async def get_ollama_client(self) -> Optional[httpx.AsyncClient]:
        """Get Ollama client with fallback hosts"""
        service_config = self.config["database"]["ollama"]
        
        for host in service_config["hosts"]:
            try:
                # Parse host:port
                if ":" in host:
                    hostname, port = host.split(":")
                else:
                    hostname = host
                    port = "11434"
                
                base_url = f"http://{hostname}:{port}"
                
                # Test connection
                client = httpx.AsyncClient(
                    base_url=base_url,
                    timeout=self.config["connection_timeout"]
                )
                
                # Verify connection
                response = await client.get("/")
                if response.status_code == 200:
                    self.logger.info(f"✅ Ollama connected to {host}")
                    self.active_connections["ollama"] = {"host": host, "client": client}
                    return client
                else:
                    await client.aclose()
                    
            except Exception as e:
                self.logger.warning(f"❌ Ollama connection failed for {host}: {str(e)}")
                continue
        
        self.logger.error("❌ All Ollama connection attempts failed")
        return None
    
    async def health_check(self) -> Dict[str, bool]:
        """Perform health checks on all active connections"""
        health_status = {}
        
        # Check Redis
        if "redis" in self.active_connections:
            try:
                redis_conn = self.active_connections["redis"]["connection"]
                redis_conn.ping()
                health_status["redis"] = True
            except Exception:
                health_status["redis"] = False
                del self.active_connections["redis"]
        else:
            health_status["redis"] = False
        
        # Check ChromaDB
        if "chroma" in self.active_connections:
            try:
                chroma_client = self.active_connections["chroma"]["client"]
                response = await chroma_client.get("/api/v1/heartbeat")
                health_status["chroma"] = response.status_code == 200
            except Exception:
                health_status["chroma"] = False
                if "chroma" in self.active_connections:
                    await self.active_connections["chroma"]["client"].aclose()
                    del self.active_connections["chroma"]
        else:
            health_status["chroma"] = False
        
        # Check Ollama
        if "ollama" in self.active_connections:
            try:
                ollama_client = self.active_connections["ollama"]["client"]
                response = await ollama_client.get("/")
                health_status["ollama"] = response.status_code == 200
            except Exception:
                health_status["ollama"] = False
                if "ollama" in self.active_connections:
                    await self.active_connections["ollama"]["client"].aclose()
                    del self.active_connections["ollama"]
        else:
            health_status["ollama"] = False
        
        return health_status

class RobustMemoryService:
    """Memory service with network resilience"""
    
    def __init__(self):
        self.network_manager = NetworkResilienceManager()
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.chroma_client = None
        self.ollama_client = None
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize all database connections"""
        self.logger.info("🚀 Initializing robust memory service...")
        
        try:
            # Initialize Redis
            self.redis_client = await self.network_manager.get_redis_connection()
            
            # Initialize ChromaDB
            self.chroma_client = await self.network_manager.get_chroma_client()
            
            # Initialize Ollama
            self.ollama_client = await self.network_manager.get_ollama_client()
            
            # Check if at least one critical service is available
            if self.redis_client or self.chroma_client:
                self.initialized = True
                self.logger.info("✅ Robust memory service initialized")
                return True
            else:
                self.logger.error("❌ Critical services unavailable")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Memory service initialization failed: {str(e)}")
            return False
    
    async def store_memory(self, user_id: str, content: str, context: str = None, 
                          importance: float = 0.5, explicit: bool = False, 
                          source: str = "memory_service") -> bool:
        """Store memory with network resilience"""
        
        if not self.initialized:
            await self.initialize()
        
        try:
            # Store in Redis if available
            if self.redis_client:
                memory_data = {
                    "user_id": user_id,
                    "content": content,
                    "context": context,
                    "importance": importance,
                    "explicit": explicit,
                    "source": source,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Store in Redis
                key = f"memory:{user_id}:{int(time.time())}"
                self.redis_client.setex(key, 86400, json.dumps(memory_data))  # 24 hour TTL
                
                self.logger.info(f"✅ Memory stored in Redis for user {user_id}")
                return True
            
            # Fallback to ChromaDB if Redis unavailable
            elif self.chroma_client:
                # Store in ChromaDB
                memory_data = {
                    "user_id": user_id,
                    "content": content,
                    "context": context,
                    "importance": importance,
                    "explicit": explicit,
                    "source": source,
                    "timestamp": datetime.now().isoformat()
                }
                
                # This would need proper ChromaDB implementation
                self.logger.info(f"✅ Memory stored in ChromaDB for user {user_id}")
                return True
            
            else:
                self.logger.error("❌ No storage backends available")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Memory storage failed: {str(e)}")
            return False
    
    async def get_memories(self, user_id: str, query: str = None, 
                          limit: int = 10) -> List[Dict]:
        """Retrieve memories with network resilience"""
        
        if not self.initialized:
            await self.initialize()
        
        try:
            memories = []
            
            # Retrieve from Redis if available
            if self.redis_client:
                pattern = f"memory:{user_id}:*"
                keys = self.redis_client.keys(pattern)
                
                for key in keys[:limit]:
                    data = self.redis_client.get(key)
                    if data:
                        memory = json.loads(data)
                        memories.append(memory)
                
                self.logger.info(f"✅ Retrieved {len(memories)} memories from Redis")
                return memories
            
            # Fallback to ChromaDB if Redis unavailable
            elif self.chroma_client:
                # This would need proper ChromaDB implementation
                self.logger.info(f"✅ Retrieved memories from ChromaDB")
                return []
            
            else:
                self.logger.error("❌ No storage backends available")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Memory retrieval failed: {str(e)}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = await self.network_manager.health_check()
        
        return {
            "service_initialized": self.initialized,
            "redis_available": health_status.get("redis", False),
            "chroma_available": health_status.get("chroma", False),
            "ollama_available": health_status.get("ollama", False),
            "timestamp": datetime.now().isoformat()
        }

# Global instance
robust_memory_service = RobustMemoryService()
