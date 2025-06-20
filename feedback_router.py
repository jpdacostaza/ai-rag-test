import json

from fastapi import APIRouter
from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse

from enhanced_integration import submit_interaction_feedback
from error_handler import log_error

feedback_router = APIRouter()


@feedback_router.post(
    "/feedback", deprecated=True, summary="Legacy feedback endpoint - Redirects to new endpoint"
)
async def feedback_alias(request: Request):
    """
    Deprecated legacy feedback endpoint that redirects to /enhanced/feedback/interaction.
    This endpoint is maintained for backward compatibility but should not be used for new integrations.

    DEPRECATED: Use /enhanced/feedback/interaction instead.
    This endpoint will be removed in v2.0.0.
    """
    try:
        data = await request.json()
        # Map legacy OpenWebUI rating fields to enhanced feedback fields
        feedback_data = {
            "user_id": data.get("user_id") or data.get("user"),
            "conversation_id": data.get("conversation_id") or data.get("conv_id"),
            "user_message": data.get("user_message") or data.get("input"),
            "assistant_response": data.get("assistant_response") or data.get("output"),
            "feedback_type": data.get("feedback_type") or data.get("rating"),
            "response_time": data.get("response_time", 0),
            "tools_used": data.get("tools_used"),
        }

        # Forward to the enhanced endpoint
        result = await submit_interaction_feedback(**feedback_data)
        # Add deprecation warning to response
        if isinstance(result, JSONResponse):
            # Get the content from the JSONResponse
            content = result.body
            if isinstance(content, (bytes, bytearray)):
                response_data = content.decode("utf-8")
            else:
                response_data = str(content)

            try:
                parsed_data = json.loads(response_data)
                parsed_data["deprecation_warning"] = {
                    "message": "This endpoint is deprecated. Use /enhanced/feedback/interaction instead.",
                    "removal_version": "v2.0.0",
                    "new_endpoint": "/enhanced/feedback/interaction",
                }
                return JSONResponse(content=parsed_data, status_code=result.status_code)
            except json.JSONDecodeError:
                # If we can't parse the JSON, just return the original result
                # with headers
                pass

        return result

    except Exception as e:
        log_error(e, "feedback_alias_endpoint")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error": str(e),
                "deprecation_warning": {
                    "message": "This endpoint is deprecated. Use /enhanced/feedback/interaction instead.",
                    "removal_version": "v2.0.0",
                    "new_endpoint": "/enhanced/feedback/interaction",
                },
            },
        )
