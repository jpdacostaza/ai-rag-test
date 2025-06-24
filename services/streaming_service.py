"""
Streaming service for managing streaming sessions and session state.
"""
import time
import logging
from typing import Dict
from datetime import datetime
from human_logging import log_service_status

# Global dict to track streaming sessions with enhanced management
STREAM_SESSION_STOP: Dict[str, bool] = {}
STREAM_SESSION_METADATA: Dict[str, dict] = {}

class StreamingService:
    """Service for managing streaming sessions."""
    
    @staticmethod
    def stop_streaming_session(session_id: str):
        """Stop a streaming session and cleanup metadata."""
        STREAM_SESSION_STOP[session_id] = True
        if session_id in STREAM_SESSION_METADATA:
            STREAM_SESSION_METADATA[session_id]["stopped_at"] = time.time()

    @staticmethod
    def cleanup_old_sessions(max_age_seconds: int = 3600):
        """Clean up old streaming sessions to prevent memory leaks."""
        current_time = time.time()
        sessions_to_remove = []
        
        for session_id, metadata in STREAM_SESSION_METADATA.items():
            if current_time - metadata.get("created_at", 0) > max_age_seconds:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            STREAM_SESSION_STOP.pop(session_id, None)
            STREAM_SESSION_METADATA.pop(session_id, None)
        
        if sessions_to_remove:
            log_service_status("SESSION_CLEANUP", "info", f"Cleaned up {len(sessions_to_remove)} old streaming sessions")

    @staticmethod
    def create_session(session_id: str, user_id: str, model: str):
        """Create a new streaming session."""
        STREAM_SESSION_STOP[session_id] = False
        STREAM_SESSION_METADATA[session_id] = {
            "created_at": time.time(),
            "user_id": user_id,
            "model": model
        }

    @staticmethod
    def get_session_status():
        """Get status of all active streaming sessions."""
        current_time = time.time()
        active_sessions = []
        
        for session_id, metadata in STREAM_SESSION_METADATA.items():
            session_info = {
                "session_id": session_id,
                "created_at": metadata.get("created_at"),
                "age_seconds": current_time - metadata.get("created_at", current_time),
                "is_stopped": STREAM_SESSION_STOP.get(session_id, False),
                "stopped_at": metadata.get("stopped_at")
            }
            active_sessions.append(session_info)
        
        return {
            "status": "ok",
            "total_sessions": len(active_sessions),
            "active_sessions": active_sessions,
            "timestamp": datetime.now().isoformat()
        }

# Global streaming service instance
streaming_service = StreamingService()
