#!/usr/bin/env python3
"""
Enhanced Memory API - Complete memory management system
Handles explicit memory commands (remember/forget) with comprehensive storage and retrieval
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
STORAGE_PATH = "storage/memory"
INTERACTIONS_FILE = os.path.join(STORAGE_PATH, "interactions.json")
MEMORIES_FILE = os.path.join(STORAGE_PATH, "memories.json")

# Ensure storage directory exists
os.makedirs(STORAGE_PATH, exist_ok=True)

class MemoryManager:
    def __init__(self):
        self.interactions = self._load_interactions()
        self.memories = self._load_memories()
    
    def _load_interactions(self) -> Dict:
        """Load interactions from storage"""
        if os.path.exists(INTERACTIONS_FILE):
            try:
                with open(INTERACTIONS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading interactions: {e}")
                return {}
        return {}
    
    def _load_memories(self) -> Dict:
        """Load memories from storage"""
        if os.path.exists(MEMORIES_FILE):
            try:
                with open(MEMORIES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading memories: {e}")
                return {}
        return {}
    
    def _save_interactions(self):
        """Save interactions to storage"""
        try:
            with open(INTERACTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.interactions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving interactions: {e}")
    
    def _save_memories(self):
        """Save memories to storage"""
        try:
            with open(MEMORIES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.memories, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving memories: {e}")
    
    def _generate_memory_id(self, content: str, user_id: str) -> str:
        """Generate unique memory ID"""
        combined = f"{user_id}:{content}:{datetime.now().isoformat()}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]
    
    def remember(self, user_id: str, content: str, source: str = "user", metadata: Dict = None) -> Dict:
        """Store a memory for the user"""
        memory_id = self._generate_memory_id(content, user_id)
        timestamp = datetime.now().isoformat()
        
        # Initialize user memories if needed
        if user_id not in self.memories:
            self.memories[user_id] = []
        
        # Create memory entry
        memory_entry = {
            "id": memory_id,
            "content": content,
            "timestamp": timestamp,
            "source": source,
            "metadata": metadata or {},
            "tags": self._extract_tags(content),
            "importance": self._calculate_importance(content)
        }
        
        # Add to memories
        self.memories[user_id].append(memory_entry)
        
        # Also log as interaction
        if user_id not in self.interactions:
            self.interactions[user_id] = []
        
        interaction_entry = {
            "id": memory_id,
            "type": "remember",
            "content": content,
            "timestamp": timestamp,
            "source": source
        }
        
        self.interactions[user_id].append(interaction_entry)
        
        # Save to storage
        self._save_memories()
        self._save_interactions()
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Memory stored successfully",
            "total_memories": self.get_memory_stats(user_id)
        }
    
    def forget(self, user_id: str, memory_id: str = None, query: str = None) -> Dict:
        """Forget specific memory or memories matching query"""
        if user_id not in self.memories:
            return {"success": False, "message": "No memories found for user"}
        
        removed_count = 0
        removed_memories = []
        
        if memory_id:
            # Remove specific memory by ID
            original_count = len(self.memories[user_id])
            self.memories[user_id] = [
                m for m in self.memories[user_id] 
                if m["id"] != memory_id
            ]
            removed_count = original_count - len(self.memories[user_id])
            if removed_count > 0:
                removed_memories.append(memory_id)
        
        elif query:
            # Remove memories matching query
            original_memories = self.memories[user_id][:]
            self.memories[user_id] = [
                m for m in self.memories[user_id]
                if query.lower() not in m["content"].lower()
            ]
            removed_count = len(original_memories) - len(self.memories[user_id])
            removed_memories = [
                m["id"] for m in original_memories
                if query.lower() in m["content"].lower()
            ]
        
        # Log forget interaction
        if removed_count > 0:
            if user_id not in self.interactions:
                self.interactions[user_id] = []
            
            forget_entry = {
                "id": self._generate_memory_id(f"forget_{memory_id or query}", user_id),
                "type": "forget",
                "content": f"Removed {removed_count} memories",
                "timestamp": datetime.now().isoformat(),
                "removed_memories": removed_memories,
                "query": query,
                "memory_id": memory_id
            }
            
            self.interactions[user_id].append(forget_entry)
            
            # Save changes
            self._save_memories()
            self._save_interactions()
        
        return {
            "success": True,
            "removed_count": removed_count,
            "removed_memories": removed_memories,
            "message": f"Removed {removed_count} memories",
            "total_memories": self.get_memory_stats(user_id)
        }
    
    def retrieve_memories(self, user_id: str, query: str = None, limit: int = 10) -> Dict:
        """Retrieve memories for user, optionally filtered by query"""
        if user_id not in self.memories:
            return {
                "success": True,
                "memories": [],
                "total_count": 0,
                "message": "No memories found for user"
            }
        
        memories = self.memories[user_id]
        
        if query:
            # Filter memories by query
            filtered_memories = [
                m for m in memories
                if query.lower() in m["content"].lower() or
                any(query.lower() in tag.lower() for tag in m.get("tags", []))
            ]
        else:
            filtered_memories = memories
        
        # Sort by timestamp (newest first)
        filtered_memories.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Apply limit
        limited_memories = filtered_memories[:limit] if limit else filtered_memories
        
        return {
            "success": True,
            "memories": limited_memories,
            "total_count": len(filtered_memories),
            "query": query,
            "limit": limit
        }
    
    def get_memory_stats(self, user_id: str) -> Dict:
        """Get memory statistics for user"""
        if user_id not in self.memories:
            return {"total": 0, "by_source": {}, "by_tags": {}}
        
        memories = self.memories[user_id]
        stats = {
            "total": len(memories),
            "by_source": {},
            "by_tags": {},
            "oldest": None,
            "newest": None
        }
        
        if memories:
            # Source statistics
            for memory in memories:
                source = memory.get("source", "unknown")
                stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
            
            # Tag statistics
            for memory in memories:
                for tag in memory.get("tags", []):
                    stats["by_tags"][tag] = stats["by_tags"].get(tag, 0) + 1
            
            # Timestamp statistics
            timestamps = [m["timestamp"] for m in memories]
            stats["oldest"] = min(timestamps)
            stats["newest"] = max(timestamps)
        
        return stats
    
    def get_interactions(self, user_id: str, limit: int = 20) -> Dict:
        """Get interaction history for user"""
        if user_id not in self.interactions:
            return {
                "success": True,
                "interactions": [],
                "total_count": 0
            }
        
        interactions = self.interactions[user_id]
        # Sort by timestamp (newest first)
        interactions.sort(key=lambda x: x["timestamp"], reverse=True)
        
        limited_interactions = interactions[:limit] if limit else interactions
        
        return {
            "success": True,
            "interactions": limited_interactions,
            "total_count": len(interactions)
        }
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract relevant tags from content"""
        # Simple tag extraction - can be enhanced with NLP
        tags = []
        content_lower = content.lower()
        
        # Common categories
        if any(word in content_lower for word in ["work", "job", "career", "office", "colleague"]):
            tags.append("work")
        if any(word in content_lower for word in ["hobby", "enjoy", "love", "passion", "interest"]):
            tags.append("personal")
        if any(word in content_lower for word in ["family", "parent", "child", "sibling", "relative"]):
            tags.append("family")
        if any(word in content_lower for word in ["friend", "buddy", "pal", "friendship"]):
            tags.append("social")
        if any(word in content_lower for word in ["learn", "study", "education", "school", "university"]):
            tags.append("learning")
        if any(word in content_lower for word in ["travel", "trip", "vacation", "visit"]):
            tags.append("travel")
        if any(word in content_lower for word in ["food", "eat", "restaurant", "cooking", "recipe"]):
            tags.append("food")
        if any(word in content_lower for word in ["exercise", "gym", "sport", "fitness", "health"]):
            tags.append("health")
        
        return tags
    
    def _calculate_importance(self, content: str) -> float:
        """Calculate importance score for content"""
        # Simple importance calculation - can be enhanced
        score = 0.5  # base score
        
        content_lower = content.lower()
        
        # Boost for personal information
        if any(word in content_lower for word in ["i am", "my name", "i work", "i live"]):
            score += 0.3
        
        # Boost for strong emotions
        if any(word in content_lower for word in ["love", "hate", "passion", "important", "critical"]):
            score += 0.2
        
        # Boost for specific details
        if any(char.isdigit() for char in content):
            score += 0.1
        
        return min(score, 1.0)
    
    def debug_info(self, user_id: str = None) -> Dict:
        """Get debug information about memory system"""
        debug_data = {
            "timestamp": datetime.now().isoformat(),
            "storage_files": {
                "interactions_exists": os.path.exists(INTERACTIONS_FILE),
                "memories_exists": os.path.exists(MEMORIES_FILE),
                "interactions_size": os.path.getsize(INTERACTIONS_FILE) if os.path.exists(INTERACTIONS_FILE) else 0,
                "memories_size": os.path.getsize(MEMORIES_FILE) if os.path.exists(MEMORIES_FILE) else 0
            },
            "total_users": {
                "with_memories": len(self.memories),
                "with_interactions": len(self.interactions)
            }
        }
        
        if user_id:
            debug_data["user_specific"] = {
                "user_id": user_id,
                "memory_count": len(self.memories.get(user_id, [])),
                "interaction_count": len(self.interactions.get(user_id, [])),
                "memory_stats": self.get_memory_stats(user_id)
            }
        
        return debug_data

# Initialize memory manager
memory_manager = MemoryManager()

# API Routes
@app.route('/api/memory/remember', methods=['POST'])
def remember():
    """Store a memory"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        content = data.get('content')
        source = data.get('source', 'api')
        metadata = data.get('metadata', {})
        
        if not user_id or not content:
            return jsonify({
                "success": False,
                "message": "user_id and content are required"
            }), 400
        
        result = memory_manager.remember(user_id, content, source, metadata)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in remember endpoint: {e}")
        return jsonify({
            "success": False,
            "message": f"Internal error: {str(e)}"
        }), 500

@app.route('/api/memory/forget', methods=['POST'])
def forget():
    """Forget a memory"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        memory_id = data.get('memory_id')
        query = data.get('query') or data.get('forget_query')  # Accept both 'query' and 'forget_query'
        
        if not user_id:
            return jsonify({
                "success": False,
                "message": "user_id is required"
            }), 400
        
        if not memory_id and not query:
            return jsonify({
                "success": False,
                "message": "Either memory_id or query/forget_query is required"
            }), 400
        
        result = memory_manager.forget(user_id, memory_id, query)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in forget endpoint: {e}")
        return jsonify({
            "success": False,
            "message": f"Internal error: {str(e)}"
        }), 500

@app.route('/api/memory/retrieve', methods=['GET', 'POST'])
def retrieve():
    """Retrieve memories - supports both GET (query params) and POST (JSON body)"""
    try:
        if request.method == 'GET':
            # GET request with query parameters
            user_id = request.args.get('user_id')
            query = request.args.get('query')
            limit = request.args.get('limit', 10, type=int)
        else:
            # POST request with JSON body
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "message": "JSON body required for POST request"
                }), 400
            
            user_id = data.get('user_id')
            query = data.get('query')
            limit = data.get('limit', 10)
        
        if not user_id:
            return jsonify({
                "success": False,
                "message": "user_id is required"
            }), 400
        
        result = memory_manager.retrieve_memories(user_id, query, limit)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in retrieve endpoint: {e}")
        return jsonify({
            "success": False,
            "message": f"Internal error: {str(e)}"
        }), 500

@app.route('/api/memory/stats', methods=['GET'])
def stats():
    """Get memory statistics"""
    try:
        user_id = request.args.get('user_id')
        
        if user_id:
            # User-specific stats
            result = memory_manager.get_memory_stats(user_id)
            return jsonify({
                "success": True,
                "user_id": user_id,
                "stats": result
            })
        else:
            # System-wide stats
            all_interactions = memory_manager.interactions
            all_memories = memory_manager.memories
            
            total_users = len(all_memories)
            total_memories = sum(len(user_memories) for user_memories in all_memories.values())
            total_interactions = sum(len(user_interactions) for user_interactions in all_interactions.values())
            
            return jsonify({
                "success": True,
                "system_stats": {
                    "total_users": total_users,
                    "total_memories": total_memories,
                    "total_interactions": total_interactions,
                    "memory_files": {
                        "interactions": os.path.exists(INTERACTIONS_FILE),
                        "memories": os.path.exists(MEMORIES_FILE)
                    }
                }
            })
        
    except Exception as e:
        logger.error(f"Error in stats endpoint: {e}")
        return jsonify({
            "success": False,
            "message": f"Internal error: {str(e)}"
        }), 500

@app.route('/api/memory/interactions', methods=['GET'])
def interactions():
    """Get interaction history"""
    try:
        user_id = request.args.get('user_id')
        limit = request.args.get('limit', 20, type=int)
        
        if user_id:
            # User-specific interactions
            result = memory_manager.get_interactions(user_id, limit)
            return jsonify(result)
        else:
            # System-wide interaction summary
            all_interactions = memory_manager.interactions
            summary = []
            
            for uid, user_interactions in all_interactions.items():
                if user_interactions:
                    latest = max(user_interactions, key=lambda x: x.get('timestamp', ''))
                    summary.append({
                        "user_id": uid,
                        "interaction_count": len(user_interactions),
                        "latest_timestamp": latest.get('timestamp', 'unknown')
                    })
            
            return jsonify({
                "success": True,
                "system_interactions": {
                    "total_users": len(summary),
                    "users": summary[:limit]
                }
            })
        
    except Exception as e:
        logger.error(f"Error in interactions endpoint: {e}")
        return jsonify({
            "success": False,
            "message": f"Internal error: {str(e)}"
        }), 500

@app.route('/api/memory/debug', methods=['GET'])
def debug():
    """Get debug information"""
    try:
        user_id = request.args.get('user_id')
        result = memory_manager.debug_info(user_id)
        return jsonify({
            "success": True,
            "debug": result
        })
        
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return jsonify({
            "success": False,
            "message": f"Internal error: {str(e)}"
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "enhanced_memory_api",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        "service": "Enhanced Memory API",
        "version": "1.0.0",
        "endpoints": {
            "remember": "POST /api/memory/remember",
            "forget": "POST /api/memory/forget",
            "retrieve": "GET /api/memory/retrieve",
            "stats": "GET /api/memory/stats",
            "interactions": "GET /api/memory/interactions",
            "debug": "GET /api/memory/debug",
            "health": "GET /health"
        },
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))  # Changed from 8003 to 8000 for Docker
    print(f"🧠 Enhanced Memory API starting on port {port}")
    print(f"📁 Storage path: {STORAGE_PATH}")
    print(f"🔗 Available endpoints:")
    print(f"   - POST /api/memory/remember")
    print(f"   - POST /api/memory/forget") 
    print(f"   - GET /api/memory/retrieve")
    print(f"   - GET /api/memory/stats")
    print(f"   - GET /api/memory/interactions")
    print(f"   - GET /api/memory/debug")
    print(f"   - GET /health")
    
    app.run(host='0.0.0.0', port=port, debug=False)
