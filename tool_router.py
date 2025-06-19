"""
Tool Router for FastAPI LLM Backend
Handles tool detection, routing, and execution for chat interactions
"""

import re
import logging
from typing import Tuple, Optional, Dict, Any, List

from utils.ai_tools import get_current_time, get_weather, convert_units
from error_handler import ToolErrorHandler, safe_execute
from human_logging import log_service_status
from schemas import ToolRequest, ToolResponse

class ToolRouter:
    """Handles tool detection and execution for chat messages."""
    
    def __init__(self):
        self.tools = {
            "time": self._handle_time_query,
            "weather": self._handle_weather_query,
            "conversion": self._handle_conversion_query,
            "news": self._handle_news_query,
            "search": self._handle_search_query,
            "exchange_rate": self._handle_exchange_rate_query,
            "system_info": self._handle_system_info_query,
            "python_code": self._handle_python_code_query,
            "wikipedia": self._handle_wikipedia_query
        }
        
        # Country to timezone mappings for time queries
        self.country_timezones = {
            "netherlands": "Europe/Amsterdam",
            "amsterdam": "Europe/Amsterdam", 
            "london": "Europe/London",
            "uk": "Europe/London",
            "new york": "America/New_York",
            "tokyo": "Asia/Tokyo",
            "paris": "Europe/Paris",
            "berlin": "Europe/Berlin",
            "moscow": "Europe/Moscow",
            "sydney": "Australia/Sydney"
        }

    def detect_and_execute_tool(self, user_message: str, user_id: str, request_id: str) -> Tuple[bool, Optional[str], Optional[str], List[str]]:
        """
        Detect if a tool should be used and execute it.
        
        Returns:
            Tuple of (tool_used, tool_name, response, debug_info)
        """
        debug_info = []
        user_message_lower = user_message.lower()
        
        # Time query detection (most complex, check first)
        if self._is_time_query(user_message):
            return self._execute_time_tool(user_message, user_id, request_id, debug_info)
            
        # Weather query detection
        elif "weather" in user_message_lower:
            return self._execute_weather_tool(user_message, user_id, request_id, debug_info)
            
        # Unit conversion detection
        elif "convert" in user_message_lower and "to" in user_message_lower:
            return self._execute_conversion_tool(user_message, user_id, request_id, debug_info)
            
        # News query detection
        elif "news" in user_message_lower:
            return self._execute_news_tool(user_message, user_id, request_id, debug_info)
            
        # Web search detection
        elif "search" in user_message_lower:
            return self._execute_search_tool(user_message, user_id, request_id, debug_info)
            
        # Exchange rate detection
        elif "exchange rate" in user_message_lower:
            return self._execute_exchange_rate_tool(user_message, user_id, request_id, debug_info)
            
        # System info detection
        elif "system info" in user_message_lower:
            return self._execute_system_info_tool(user_message, user_id, request_id, debug_info)
            
        # Python code execution detection
        elif self._is_python_code_query(user_message):
            return self._execute_python_code_tool(user_message, user_id, request_id, debug_info)
            
        # Wikipedia search detection
        elif "wikipedia" in user_message_lower or "wiki" in user_message_lower:
            return self._execute_wikipedia_tool(user_message, user_id, request_id, debug_info)
        
        # No tool detected
        return False, None, None, debug_info

    def _is_time_query(self, user_message: str) -> bool:
        """Check if the message is a time-related query."""
        time_patterns = [
            r"time(?:\s*(?:in|for|at))?\s+([a-zA-Z ]+)",
            r"current time in ([a-zA-Z ]+)",
            r"what(?:'s| is) the time in ([a-zA-Z ]+)",
            r"timeanddate\.com.*([a-zA-Z ]+)"
        ]
        
        return (
            "timeanddate.com" in user_message.lower() or
            "time" in user_message.lower() or
            any(re.search(pat, user_message, re.IGNORECASE) for pat in time_patterns)
        )

    def _is_python_code_query(self, user_message: str) -> bool:
        """Check if the message is a Python code execution request."""
        return (
            "run python" in user_message.lower() or
            user_message.lower().startswith("python ") or
            "python code" in user_message.lower() or
            "```python" in user_message
        )

    def _execute_time_tool(self, user_message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute time lookup tool."""
        system_msg = f"[TOOL] Time lookup triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        # Extract location from message
        time_patterns = [
            r"time(?:\s*(?:in|for|at))?\s+([a-zA-Z ]+)",
            r"current time in ([a-zA-Z ]+)",
            r"what(?:'s| is) the time in ([a-zA-Z ]+)",
            r"timeanddate\.com.*([a-zA-Z ]+)"
        ]
        
        country = "netherlands"  # default
        for pat in time_patterns:
            match = re.search(pat, user_message, re.IGNORECASE)
            if match:
                country = match.group(1).strip()
                break
        
        # Clean up extracted location string
        country = re.sub(r"^(is|what|'s|the|current|now|please|tell|me|show|give|provide|can|you|do|does|in|for|at|on|to|of|about|time|current time|the time|\s)+", "", country, flags=re.IGNORECASE)
        country = re.sub(r"\?$", "", country).strip()
        if not country:
            country = "netherlands"
            
        def get_timezone_time():
            tz = self.country_timezones.get(country.lower(), None)
            if tz:
                return get_current_time(tz) + f" (timezone: {tz})", "geo_timezone"
            else:
                from utils.ai_tools import get_time_from_timeanddate
                return get_time_from_timeanddate(country), "timeanddate.com"
        
        result = safe_execute(
            get_timezone_time,
            fallback_value=(ToolErrorHandler.handle_tool_error(Exception("Time lookup failed"), "time", user_id, country, request_id), "error"),
            error_handler=lambda e: ToolErrorHandler.handle_tool_error(e, "time", user_id, country, request_id)
        )
        
        user_response, tool_name = result
        debug_info.append(f"[TOOL] Used {tool_name} for {country}")
        
        return True, "time", user_response, debug_info

    def _execute_weather_tool(self, user_message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute weather lookup tool."""
        system_msg = f"[TOOL] Weather lookup triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        match = re.search(r"weather in ([a-zA-Z ]+)", user_message, re.IGNORECASE)
        city = match.group(1).strip() if match else "London"
        
        user_response = safe_execute(
            get_weather,
            city,
            fallback_value=ToolErrorHandler.handle_tool_error(Exception("Weather lookup failed"), "weather", user_id, city, request_id),
            error_handler=lambda e: ToolErrorHandler.handle_tool_error(e, "weather", user_id, city, request_id)
        )
        
        debug_info.append(f"[TOOL] Weather lookup for {city}")
        return True, "weather", user_response, debug_info

    def _execute_conversion_tool(self, user_message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute unit conversion tool."""
        system_msg = f"[TOOL] Unit conversion triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        match = re.search(r"convert ([\d\.]+) ([a-zA-Z]+) to ([a-zA-Z]+)", user_message, re.IGNORECASE)
        if match:
            value, from_unit, to_unit = float(match.group(1)), match.group(2), match.group(3)
            user_response = safe_execute(
                convert_units,
                value, from_unit, to_unit,
                fallback_value=ToolErrorHandler.handle_tool_error(Exception("Unit conversion failed"), "unit_conversion", user_id, f"{value} {from_unit} to {to_unit}", request_id),
                error_handler=lambda e: ToolErrorHandler.handle_tool_error(e, "unit_conversion", user_id, f"{value} {from_unit} to {to_unit}", request_id)
            )
            debug_info.append(f"[TOOL] Converted {value} {from_unit} to {to_unit}")
        else:
            user_response = "Please specify conversion like 'convert 10 km to m'."
            debug_info.append("[TOOL] Invalid conversion format")
        
        return True, "unit_conversion", user_response, debug_info

    def _execute_news_tool(self, user_message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute news lookup tool."""
        system_msg = f"[TOOL] News lookup triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        user_response = "News lookup is currently unavailable."
        debug_info.append("[TOOL] News lookup disabled")
        
        return True, "news", user_response, debug_info

    def _execute_search_tool(self, user_message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute web search tool."""
        system_msg = f"[TOOL] Web search triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        match = re.search(r"search (.+)", user_message, re.IGNORECASE)
        query = match.group(1) if match else user_message
        
        def web_search_safe():
            results = []
            return results[0] if results else "No results found.", results
        
        result = safe_execute(
            web_search_safe,
            fallback_value=(ToolErrorHandler.handle_tool_error(Exception("Web search failed"), "web_search", user_id, query, request_id), []),
            error_handler=lambda e: ToolErrorHandler.handle_tool_error(e, "web_search", user_id, query, request_id)
        )
        
        if isinstance(result, tuple):
            user_response, results = result
        else:
            user_response = result
            results = []
        
        debug_info.append(f"[TOOL] Web search for: {query}")
        return True, "web_search", user_response, debug_info

    def _execute_exchange_rate_tool(self, user_message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute exchange rate lookup tool."""
        system_msg = f"[TOOL] Exchange rate lookup triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        match = re.search(r"exchange rate ([a-zA-Z]{3}) to ([a-zA-Z]{3})", user_message, re.IGNORECASE)
        if match:
            from_cur, to_cur = match.group(1), match.group(2)
            user_response = "Exchange rate lookup is currently unavailable."
            debug_info.append(f"[TOOL] Exchange rate lookup for {from_cur} to {to_cur} (disabled)")
        else:
            user_response = "Please specify exchange rate like 'exchange rate USD to EUR'."
            debug_info.append("[TOOL] Invalid exchange rate format")
        
        return True, "exchange_rate", user_response, debug_info

    def _execute_system_info_tool(self, user_message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute system info lookup tool."""
        system_msg = f"[TOOL] System info lookup triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        user_response = "System info lookup is currently unavailable."
        debug_info.append("[TOOL] System info lookup disabled")
        
        return True, "system_info", user_response, debug_info

    def _execute_python_code_tool(self, user_message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute Python code execution tool."""
        system_msg = f"[TOOL] Python code execution triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        # Extract code from message
        if "```python" in user_message:
            # Extract code from code blocks
            code_start = user_message.find("```python") + 9
            code_end = user_message.find("```", code_start)
            code = user_message[code_start:code_end].strip() if code_end != -1 else user_message[code_start:].strip()
        elif "run python" in user_message.lower():
            code = user_message.split("run python", 1)[-1].strip()
        elif user_message.lower().startswith("python "):
            code = user_message.split("python ", 1)[-1].strip()
        else:
            # Try to extract any code-like text
            code = user_message.strip()
        
        if not code:
            user_response = "Please provide Python code to execute."
            debug_info.append("[TOOL] No Python code found")
        else:
            user_response = "Python code execution is currently unavailable."
            debug_info.append(f"[TOOL] Python code execution disabled (code: {code[:50]}...)")
        
        return True, "python_code_execution", user_response, debug_info

    def _execute_wikipedia_tool(self, user_message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute Wikipedia search tool."""
        system_msg = f"[TOOL] Wikipedia search triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        # Extract search query
        query = user_message.lower().replace("wikipedia", "").replace("wiki", "").replace("search", "").strip()
        if not query:
            query = "artificial intelligence"  # default
        
        user_response = "Wikipedia search is currently unavailable."
        debug_info.append(f"[TOOL] Wikipedia search for: {query} (disabled)")
        
        return True, "wikipedia", user_response, debug_info

    def _handle_time_query(self, request: ToolRequest) -> ToolResponse:
        """Handle time query tool request."""
        # Implementation would go here for API-based tool access
        return ToolResponse(
            tool_name="time",
            success=False,
            result="Not implemented",
            error_message="API-based tool access not implemented",
            execution_time_ms=0.0
        )

    def _handle_weather_query(self, request: ToolRequest) -> ToolResponse:
        """Handle weather query tool request."""
        # Implementation would go here for API-based tool access
        return ToolResponse(
            tool_name="weather",
            success=False,
            result="Not implemented",
            error_message="API-based tool access not implemented",
            execution_time_ms=0.0
        )

    def _handle_conversion_query(self, request: ToolRequest) -> ToolResponse:
        """Handle conversion tool request."""
        # Implementation would go here for API-based tool access
        return ToolResponse(
            tool_name="conversion",
            success=False,
            result="Not implemented",
            error_message="API-based tool access not implemented",
            execution_time_ms=0.0
        )

    def _handle_news_query(self, request: ToolRequest) -> ToolResponse:
        """Handle news query tool request."""
        # Implementation would go here for API-based tool access
        return ToolResponse(
            tool_name="news",
            success=False,
            result="Not implemented",
            error_message="API-based tool access not implemented",
            execution_time_ms=0.0
        )

    def _handle_search_query(self, request: ToolRequest) -> ToolResponse:
        """Handle search tool request."""
        # Implementation would go here for API-based tool access
        return ToolResponse(
            tool_name="search",
            success=False,
            result="Not implemented",
            error_message="API-based tool access not implemented",
            execution_time_ms=0.0
        )

    def _handle_exchange_rate_query(self, request: ToolRequest) -> ToolResponse:
        """Handle exchange rate tool request."""
        # Implementation would go here for API-based tool access
        return ToolResponse(
            tool_name="exchange_rate",
            success=False,
            result="Not implemented",
            error_message="API-based tool access not implemented",
            execution_time_ms=0.0
        )

    def _handle_system_info_query(self, request: ToolRequest) -> ToolResponse:
        """Handle system info tool request."""
        # Implementation would go here for API-based tool access
        return ToolResponse(
            tool_name="system_info",
            success=False,
            result="Not implemented",
            error_message="API-based tool access not implemented",
            execution_time_ms=0.0
        )

    def _handle_python_code_query(self, request: ToolRequest) -> ToolResponse:
        """Handle Python code execution tool request."""
        # Implementation would go here for API-based tool access
        return ToolResponse(
            tool_name="python_code",
            success=False,
            result="Not implemented",
            error_message="API-based tool access not implemented",
            execution_time_ms=0.0
        )

    def _handle_wikipedia_query(self, request: ToolRequest) -> ToolResponse:
        """Handle Wikipedia search tool request."""
        # Implementation would go here for API-based tool access
        return ToolResponse(
            tool_name="wikipedia",
            success=False,
            result="Not implemented",
            error_message="API-based tool access not implemented",
            execution_time_ms=0.0
        )

# Global tool router instance
tool_router = ToolRouter()
