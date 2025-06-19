from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from enhanced_integration import submit_interaction_feedback
from error_handler import log_error

feedback_router = APIRouter()

@feedback_router.post("/feedback", deprecated=True, summary="Legacy feedback endpoint")
async def feedback_alias(request: Request):
    """
    Alias for /enhanced/feedback/interaction for backward compatibility, specifically for OpenWebUI rating integration.
    This endpoint is deprecated and will be removed in a future version.
    """
    try:
        data = await request.json()
        # Map OpenWebUI rating fields to backend feedback fields
        feedback_data = {
            "user_id": data.get("user_id") or data.get("user"),
            "conversation_id": data.get("conversation_id") or data.get("conv_id"),
            "user_message": data.get("user_message") or data.get("input"),
            "assistant_response": data.get("assistant_response") or data.get("output"),
            "feedback_type": data.get("feedback_type") or data.get("rating"),
            "response_time": data.get("response_time", 0),
            "tools_used": data.get("tools_used")
        }
        
        # Forward to the new endpoint
        return await submit_interaction_feedback(**feedback_data)

    except Exception as e:
        log_error(e, "feedback_alias_endpoint")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, 
            content={"success": False, "error": str(e)}
        )
