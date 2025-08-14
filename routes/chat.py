"""Chat endpoints and logic (refactored).

Provides legacy /chat/completions_legacy endpoint and memory storage helper.
"""

import logging
import time
import uuid
import hashlib
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends, Body

from core.unified_logging import log_service_status
from services.user_identity import resolve_user_id
from services.auth_validator import AuthValidator
from services.chat_service import ChatService
from services.dependencies import get_chat_service
from services.database_manager import (
    get_cache,
    index_user_document,
)
from utilities.simple_error_handling import handle_api_errors, handle_errors
from models.models import ChatRequest

# Memory service (optional)
try:
    from services.memory_service import MemoryService  # noqa: F401
    MEMORY_SERVICE_AVAILABLE = True
except ImportError:  # pragma: no cover
    MemoryService = None  # type: ignore
    MEMORY_SERVICE_AVAILABLE = False

chat_router = APIRouter()


def get_memory_service():
    from core.main import get_memory_service_or_legacy
    return get_memory_service_or_legacy()


@handle_errors("get_user_memories", default_value=[])
async def get_user_memories(user_id: Optional[str], query: str, memory_service=None, n_results: int = 3):
    """Retrieve user memories (compat shim for legacy imports)."""
    if not user_id:
        return []
    if not memory_service:
        memory_service = get_memory_service()
    if not memory_service:
        return []
    try:
        memories = await memory_service.get_relevant_memories(
            user_id=user_id,
            context=query,
            max_memories=n_results
        )
    except Exception:
        return []
    out = []
    for m in memories:
        out.append({
            "document": getattr(m, 'content', ''),
            "metadata": getattr(m, 'metadata', {}) or {},
            "distance": 1.0 - (getattr(m, 'relevance_score', 0.0) or 0.0)
        })
    return out


@handle_errors("get_cache_manager", default_value=None)
def get_cache_manager():
    return get_cache()


def generate_cache_key(user_id: str, message: str) -> str:
    message_hash = hashlib.md5(message.encode()).hexdigest()[:8]
    return f"chat:{user_id}:{message_hash}"


def validate_openwebui_user_id(user_id: str) -> bool:
    auth_validator = AuthValidator()
    return auth_validator.is_valid_user_id(user_id)


@chat_router.post("/chat/completions_legacy")
@handle_api_errors("chat_endpoint")
async def chat_endpoint(
    request: Request,
    body: dict = Body(...),
    chat_service: ChatService = Depends(get_chat_service),
):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.time()

    if "model" in body and "messages" in body:
        from core.main import openai_chat_completions
        return await openai_chat_completions(request, body)

    try:
        chat = ChatRequest(**body)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid request format: {e}")

    if not chat.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    response = await chat_service.process_chat(chat)

    duration = (time.time() - start_time) * 1000
    log_service_status(
        "api",
        "info",
        f"[REQUEST] Info - [{request_id}] POST /chat - Completed 200 in {duration:.2f}ms",
    )

    return response


async def store_conversation_memory(
    user_id: str,
    user_message: str,
    assistant_response: str,
    debug_info: list,
) -> bool:
    try:
        memory_service = get_memory_service()
        if memory_service and MEMORY_SERVICE_AVAILABLE:
            memory_content = f"User: {user_message}\nAssistant: {assistant_response}"
            success = await memory_service.store_conversation_memory(
                user_id=user_id,
                content=memory_content,
                metadata={
                    "type": "chat_conversation",
                    "timestamp": time.time(),
                    "user_message": user_message,
                    "assistant_response": assistant_response,
                },
            )
            if success:
                debug_info.append("Stored via unified memory service")
                return True

        conversation_doc = (
            f"User said: {user_message}\nAssistant replied: {assistant_response}"[:2000]
        )
        try:
            index_user_document(user_id, conversation_doc)
            debug_info.append("Indexed conversation via legacy path")
            return True
        except Exception as e:  # pragma: no cover
            log_service_status("CHAT", "warning", f"Legacy memory indexing failed: {e}")
            debug_info.append(f"Legacy indexing failed: {e}")
            return False
    except Exception as e:  # pragma: no cover
        log_service_status("CHAT", "error", f"Failed to store conversation memory: {e}")
        debug_info.append(f"Error storing memory: {e}")
        return False
