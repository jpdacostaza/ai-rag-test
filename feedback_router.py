from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from enhanced_integration import submit_interaction_feedback

feedback_router = APIRouter()

@feedback_router.post("/feedback")
async def feedback_alias(request: Request):
    """Alias for /enhanced/feedback/interaction for OpenWebUI rating integration."""
    data = await request.json()
    # Map OpenWebUI rating fields to backend feedback fields
    user_id = data.get("user_id") or data.get("user")
    conversation_id = data.get("conversation_id") or data.get("conv_id")
    user_message = data.get("user_message") or data.get("input")
    assistant_response = data.get("assistant_response") or data.get("output")
    feedback_type = data.get("feedback_type") or data.get("rating")
    response_time = data.get("response_time", 0)
    tools_used = data.get("tools_used")
    try:
        result = await submit_interaction_feedback(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_response=assistant_response,
            feedback_type=feedback_type,
            response_time=response_time,
            tools_used=tools_used
        )
        return result
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "error": str(e)})
