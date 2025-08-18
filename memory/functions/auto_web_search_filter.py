"""
Auto Web Search Filter
Automatically performs a web search and injects results into the conversation context
when the model fails to call web search functionality.

Purpose:
Fallback path for small / non-tool-calling local models (e.g. Qwen3-4B) so that
queries requiring current information still get fresh data.

Strategy:
- Runs in inlet stage.
- If last user message contains trigger phrases and no prior injected results,
  uses zero-configuration web search with ddgs library.
- Appends synthetic system message with results before model reply.

Enhanced Features:
- Zero-configuration deployment (ddgs only)
- Forced invocation for explicit web search requests
- Improved query extraction and result formatting
"""

import re
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

PRINT_PREFIX = "[AutoWebSearchFilter]"
print(f"{PRINT_PREFIX} Imported.")

class Filter:
    class Valves(BaseModel):
        priority: int = Field(default=10, description="Priority for auto web search filter (higher runs earlier)")
        enable_auto_search: bool = Field(default=True, description="Enable automatic fallback web search")
        max_results: int = Field(default=6, ge=1, le=10, description="Results to inject (Orange Pi optimized: 1-10)")
        trigger_keywords: List[str] = Field(
            default=[
                "current", "today", "latest", "news", "headline",
                "date", "time", "update", "trending", "market", "stock", "price", "search the web",
                "web search", "lookup", "recent", "what is happening", "check online",
                "warning", "warnings", "alert", "alerts", "advisory", "advisories", "check if",
                "are there", "any warnings", "specific warnings", "weather", "forecast", "temperature",
                "3 day", "day ahead", "ahead", "tomorrow", "knmi", "knmi.nl", "site", "south holland",
                "north holland", "netherlands", "holland", "dutch"
            ],
            description="Keywords that trigger auto web search"
        )
        force_keywords: List[str] = Field(
            default=[
                "search the web", "web search", "lookup online", "check online", "find online",
                "search for", "look up current", "get latest"
            ],
            description="Keywords that force web search regardless of cooldown"
        )
        cooldown_seconds: int = Field(default=10, description="Minimum seconds before re-searching (Orange Pi optimized)")
        min_chars: int = Field(default=12, description="Minimum user message length to consider")
        use_real_action: bool = Field(default=True, description="Try to call real Action first before fallback")

    def __init__(self):
        self.valves = self.Valves()
        self.type = "filter"
        self.name = "Auto Web Search Fallback"
        self.version = "2.2_weather_enhanced"
        self._recent_hashes: Dict[str, datetime] = {}

    async def inlet(self, body: dict, __user__=None) -> dict:
        print(f"{PRINT_PREFIX} INLET CALLED - body keys: {list(body.keys())}")
        
        if not self.valves.enable_auto_search:
            return body

        messages: List[Dict[str, Any]] = body.get("messages", [])
        if not messages:
            return body

        last = messages[-1]
        if last.get("role") != "user":
            return body

        content: str = last.get("content", "").strip()
        if len(content) < self.valves.min_chars:
            return body

        # Avoid duplicate injection - check for actual search result patterns
        if any("Enhanced Web Search Results" in m.get("content", "") or 
               "WEB_SEARCH_RESULTS" in m.get("content", "") or
               "*** Enhanced Web Search Results" in m.get("content", "") or
               "*** CRITICAL: REAL WEB SEARCH RESULTS" in m.get("content", "") or
               "*** MANDATORY WEB SEARCH RESULTS" in m.get("content", "") for m in messages):
            return body

        # Check triggers
        lowered = content.lower()
        
        # EXCLUDE meta-questions about the assistant's own capabilities
        capability_questions = [
            "do you have", "can you", "are you able", "do you access", "can you access",
            "your capabilities", "your ability", "what can you do", "internet access",
            "real-time access", "real time access", "live access", "data access"
        ]
        
        is_capability_question = any(cap_q in lowered for cap_q in capability_questions)
        if is_capability_question:
            print(f"{PRINT_PREFIX} SKIPPING: Capability question detected - '{content[:100]}'")
            return body
        
        is_forced = any(kw in lowered for kw in self.valves.force_keywords)
        is_triggered = is_forced or any(kw in lowered for kw in self.valves.trigger_keywords)
        
        # Debug what triggered
        if is_triggered:
            matching_trigger_keywords = [kw for kw in self.valves.trigger_keywords if kw in lowered]
            matching_force_keywords = [kw for kw in self.valves.force_keywords if kw in lowered]
            print(f"{PRINT_PREFIX} DEBUG: TRIGGERED! Content='{content[:100]}'")
            print(f"{PRINT_PREFIX} DEBUG: Matching trigger keywords: {matching_trigger_keywords}")
            print(f"{PRINT_PREFIX} DEBUG: Matching force keywords: {matching_force_keywords}")
        
        # Weather queries can be handled by web search
        # Note: Weather tool exists in tools/ folder but web search can supplement it
        weather_keywords = ["weather", "temperature", "forecast", "climate", "hot", "cold", "warm", "cool", 
                           "rain", "raining", "sunny", "cloudy", "wind", "windy", "storm", "snow", "snowing"]
        
        # Debug weather detection
        weather_matches = [weather_kw for weather_kw in weather_keywords if weather_kw in lowered]
        if weather_matches:
            # Always allow web search for weather when explicitly requested
            explicit_web_search = any(kw in lowered for kw in self.valves.force_keywords)
            if explicit_web_search:
                print(f"{PRINT_PREFIX} ALLOWING: Explicit web search request for weather (keywords: {weather_matches})")
            else:
                print(f"{PRINT_PREFIX} ALLOWING: Weather query - web search can provide additional context (keywords: {weather_matches})")
        
        if not is_triggered:
            return body

        # Hash-based cooldown (skip for forced)
        if not is_forced:
            msg_hash = hashlib.sha1(content.encode("utf-8")).hexdigest()[:12]
            now = datetime.utcnow()
            last_time = self._recent_hashes.get(msg_hash)
            if last_time and (now - last_time) < timedelta(seconds=self.valves.cooldown_seconds):
                return body
            self._recent_hashes[msg_hash] = now

        # Perform search
        try:
            query = self._build_query(content)
            print(f"{PRINT_PREFIX} DEBUG: Built query='{query}' from content='{content[:50]}...'")
            results_text = await self._get_search_results(query)
            print(f"{PRINT_PREFIX} DEBUG: Retrieved results length: {len(results_text)} chars")
            print(f"{PRINT_PREFIX} DEBUG: Results preview: {results_text[:200]}...")
            
            # Inject as USER message which models respect more than system messages
            messages.append({
                "role": "user",
                "content": f"""[SYSTEM CONTEXT - WEB SEARCH RESULTS]
Search Query: "{query}"
Search Completed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

{results_text}

IMPORTANT: The above are real web search results. Please use this information to answer the original question. Start your response with "Based on current web search results" and provide specific details from the search data."""
            })
            
            # Also modify the original user message to indicate web search was performed
            last_message = messages[-2]  # Get the user message (before our search results)
            if last_message.get("role") == "user":
                original_content = last_message["content"]
                last_message["content"] = f"""{original_content}

[Note: Web search has been performed - results are provided above]"""
            
            print(f"{PRINT_PREFIX} Injected ENHANCED search results for query='{query}'")
            print(f"{PRINT_PREFIX} DEBUG: Injected system message length: {len(messages[-1]['content'])} chars")
            print(f"{PRINT_PREFIX} DEBUG: Modified user message: {last_message['content'][:100]}...")
            print(f"{PRINT_PREFIX} DEBUG: Total messages now: {len(messages)}")
            
        except Exception as e:
            print(f"{PRINT_PREFIX} Error during auto web search: {e}")

        return body

    async def outlet(self, body: dict, __user__=None) -> dict:
        return body

    async def _get_search_results(self, query: str) -> str:
        if self.valves.use_real_action:
            try:
                # Try to call the zero-conf web search
                import sys
                sys.path.append('/app/utilities')
                from enhanced_web_search import search_web
                
                result_dict = await search_web(query, max_results=self.valves.max_results)
                
                if result_dict and result_dict.get("results"):
                    formatted_results = []
                    for item in result_dict["results"]:
                        title = item.get('title', 'No title')
                        snippet = item.get('snippet', 'No description')
                        link = item.get('link', 'No link')
                        formatted_results.append(f"**{title}**\n{snippet}\nSource: {link}")
                    
                    result = "\n\n".join(formatted_results)
                    print(f"{PRINT_PREFIX} Called zero-conf web search successfully")
                    return result
                    
            except Exception as e:
                print(f"{PRINT_PREFIX} Zero-conf web search failed: {e}, using fallback")
        
        # Fallback to zero-conf search
        return await self._zero_conf_search(query)

    async def _zero_conf_search(self, query: str) -> str:
        """Zero-configuration search using only ddgs library"""
        try:
            from enhanced_web_search import search_web
            
            print(f"{PRINT_PREFIX} Using zero-conf fallback search")
            result_dict = await search_web(query, max_results=self.valves.max_results)
            
            if result_dict and result_dict.get("results"):
                formatted_results = []
                for i, item in enumerate(result_dict["results"]):
                    title = item.get('title', 'No title')
                    snippet = item.get('snippet', 'No description')
                    link = item.get('link', 'No link')
                    formatted_results.append(f"**{i+1}. {title}**\n{snippet}\nSource: {link}")
                
                return "\n\n".join(formatted_results)
            else:
                return "No search results found."
                
        except Exception as e:
            print(f"{PRINT_PREFIX} Zero-conf fallback failed: {e}")
            return f"Search temporarily unavailable: {str(e)}"

    def _build_query(self, content: str) -> str:
        # PRIORITY: Weather queries get optimized targeting
        content_lower = content.lower()
        
        # Detect weather queries first - ENHANCED detection
        weather_keywords = ["weather", "temperature", "forecast", "climate", "rain", "sunny", "cloudy", "wind", "storm", "snow"]
        location_keywords = ["south holland", "noord holland", "utrecht", "amsterdam", "rotterdam", "den haag", "the hague", "netherlands", "dutch", "holland"]
        forecast_keywords = ["3 day", "three day", "today", "tomorrow", "forecast", "ahead", "day ahead", "upcoming"]
        knmi_keywords = ["knmi", "knmi.nl", "site"]
        
        has_weather = any(weather in content_lower for weather in weather_keywords)
        has_location = any(location in content_lower for location in location_keywords)
        has_forecast = any(forecast in content_lower for forecast in forecast_keywords)
        has_knmi = any(knmi in content_lower for knmi in knmi_keywords)
        
        # ENHANCED WEATHER QUERY DETECTION
        # Detect requests for Netherlands weather forecasts
        if (has_forecast or "day" in content_lower) and (has_location or has_knmi):
            # This is clearly a Netherlands weather forecast request
            if "south holland" in content_lower or "zuid holland" in content_lower:
                return "South Holland weather forecast 3 day KNMI site:knmi.nl"
            elif "north holland" in content_lower or "noord holland" in content_lower:
                return "North Holland weather forecast 3 day KNMI site:knmi.nl"
            elif "netherlands" in content_lower or "dutch" in content_lower or "holland" in content_lower:
                return "Netherlands weather forecast 3 day KNMI official site:knmi.nl"
            elif has_knmi:
                return "Netherlands weather forecast KNMI site:knmi.nl"
        
        # Standard weather detection
        if has_weather:
            # Netherlands weather queries - use highly targeted search
            if has_location or has_knmi:
                if "south holland" in content_lower:
                    return "South Holland weather forecast today current conditions KNMI site:knmi.nl"
                elif "netherlands" in content_lower or "dutch" in content_lower or "holland" in content_lower:
                    return "Netherlands weather forecast today current conditions KNMI site:knmi.nl"
                elif has_knmi:
                    return "Netherlands weather KNMI site:knmi.nl"
            
            # Generic weather queries - add location context
            return f"weather forecast today current conditions {content_lower.replace('weather', '').replace('forecast', '').strip()}"
        
        # Special case: KNMI-specific queries (even without explicit weather keywords)
        if has_knmi and (has_forecast or "day" in content_lower or "latest" in content_lower):
            if "south holland" in content_lower:
                return "South Holland weather forecast KNMI site:knmi.nl"
            else:
                return "Netherlands weather forecast KNMI site:knmi.nl"
        
        # Extract meaningful query from user message - ENHANCED  
        cleaned = re.sub(r"\b(please|can you|could you|search|find|look up|web search for|check|get|give me)\b", "", content, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        
        # If too short after cleaning, use original
        if len(cleaned) < 5:
            cleaned = content
            
        # Remove question marks and common filler
        cleaned = re.sub(r"[?!]+$", "", cleaned)
        cleaned = re.sub(r"\b(the|a|an|what|when|where|how|why)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        
        # ENHANCED: Add context keywords for better content retrieval
        final_query = cleaned or content
        
        # For news queries, add specific terms that encourage detailed content
        if any(word in final_query.lower() for word in ['news', 'latest', 'today', 'recent', 'current']):
            if 'news' not in final_query.lower():
                final_query += ' news'
        
        # For weather warnings, add official source terms
        if any(word in final_query.lower() for word in ['warning', 'warnings', 'alert', 'alerts', 'advisory', 'advisories']):
            if 'netherlands' in final_query.lower() or 'dutch' in final_query.lower():
                final_query += ' site:knmi.nl'
            elif not any(official in final_query.lower() for official in ['official', 'site:']):
                final_query += ' official weather warning'
        
        # For technical queries, add terms that encourage detailed explanations
        if any(word in final_query.lower() for word in ['what is', 'how to', 'explain', 'definition']):
            if 'explanation' not in final_query.lower() and 'guide' not in final_query.lower():
                final_query += ' explanation'
        
        return final_query

print(f"{PRINT_PREFIX} Enhanced Filter class defined: Auto Web Search Fallback v2.2_weather_enhanced (KNMI weather query optimization)")
