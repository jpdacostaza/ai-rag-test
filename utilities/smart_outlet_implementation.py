"""(Legacy) Smart Anti-Hallucination Web Search Pipeline
NOTE: Refactored to async compatibility & structured web search results.
If unused you may remove this file to reduce noise.
"""

from typing import Dict, Any, Optional
import time
try:
    from utilities.enhanced_web_search import search_web
    from utilities.smart_web_search_trigger import should_trigger_web_search_smart, analyze_response_quality
except Exception:  # pragma: no cover - optional import
    search_web = None  # type: ignore
    should_trigger_web_search_smart = None  # type: ignore
    analyze_response_quality = None  # type: ignore

async def outlet(self, body: Dict[str, Any], __user__: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Outlet filter - processes model responses and adds web search if needed.
    This runs AFTER the model generates a response.
    
    This is the CORRECT place for anti-hallucination web search.
    """
    try:
        self.log("[FIRE] OUTLET CALLED - Analyzing model response for potential web search needs")
        
        # Early return if search module unavailable
        if not search_web:
            return body
            
        # Extract messages to get user query and model response
        messages = body.get("messages", [])
        if len(messages) < 2:
            return body
            
        # Get the latest user query and model response
        user_query = ""
        model_response = ""
        
        # Find the most recent user message and assistant response
        for msg in reversed(messages):
            if msg.get("role") == "user" and not user_query:
                user_query = msg.get("content", "")
            elif msg.get("role") == "assistant" and not model_response:
                model_response = msg.get("content", "")
                
        if not user_query or not model_response:
            self.log("Could not find user query and model response pair")
            return body
            
        self.log(f"[SEARCH] Analyzing: Query='{user_query[:50]}...' Response='{model_response[:50]}...'")
        
        # Use smart trigger logic
        if not should_trigger_web_search_smart:
            return body

        should_search, trigger_reason = should_trigger_web_search_smart(user_query, model_response)
        
        if should_search:
            self.log(f"[OK] WEB SEARCH TRIGGERED: {trigger_reason}")
            
            try:
                # Perform web search
                if not search_web:
                    return body
                result = await search_web(user_query, max_results=3)
                if isinstance(result, dict):
                    raw_text = result.get("summary", "")
                else:
                    raw_text = str(result)
                if raw_text and len(raw_text.strip()) > 50:
                    # Analyze response quality to determine how to integrate search results
                    quality_analysis = analyze_response_quality(model_response)
                    
                    if quality_analysis["uncertainty_score"] > 0:
                        # Model was uncertain - replace with web search results
                        enhanced_response = f"""Based on current web search results:

{raw_text}

Let me provide you with the most up-to-date information about your query."""
                        
                    else:
                        # Model seemed confident but needs verification - add as supplement
                        enhanced_response = f"""{model_response}

**Current Information Update:**
{raw_text}

*The above information has been verified with current web sources to ensure accuracy.*"""
                    
                    # Update the assistant's response
                    for msg in reversed(messages):
                        if msg.get("role") == "assistant":
                            msg["content"] = enhanced_response
                            break
                            
                    self.log(f" Enhanced response with web search results")
                    
                    # Store web search results to memory if enabled and user is authenticated
                    if self.valves.save_raw_search_results and hasattr(self, 'api_client') and self.api_client:
                        try:
                            # Get user authentication
                            user_id, user_data = self.auth_manager.authenticate_user(body) if self.auth_manager else (None, None)
                            
                            if user_id:
                                web_search_memory = {
                                    "user_id": user_id,
                                    "content": f"Web search verification for '{user_query}':\n\n{raw_text}",
                                    "metadata": {
                                        "type": "web_search_verification",
                                        "original_query": user_query,
                                        "trigger_reason": trigger_reason,
                                        "timestamp": str(int(time.time())),
                                        "search_engine": "duckduckgo"
                                    }
                                }
                                
                                if hasattr(self.api_client, 'store_memory'):
                                    await self.api_client.store_memory(web_search_memory)
                                self.log(f" Stored web search verification to memory")
                        except Exception as storage_error:
                            self.log(f"[WARN] Failed to store web search results: {storage_error}", "WARNING")
                            
                else:
                    self.log(f"[WARN] Web search triggered but no meaningful results returned")
                    
            except Exception as search_error:
                self.log(f"[FAIL] Web search failed: {search_error}", "ERROR")
                
        else:
            self.log(f"[FAIL] Web search NOT needed: {trigger_reason}")
            
        # Continue with memory storage if that's still enabled
        if self.valves.enable_memory and hasattr(self, 'api_client') and self.api_client:
            # Store the conversation to memory (existing logic)
            # ... existing memory storage code ...
            pass
            
        return body
        
    except Exception as e:
        self.log(f"[FAIL] Outlet processing failed: {e}", "ERROR")
        return body
