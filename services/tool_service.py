"""
Tool service for handling tool detection and execution.
"""
import re
import logging
from typing import Tuple, Optional, List, Dict, Any

from utilities.ai_tools import convert_units, get_current_time, get_weather
from error_handler import ToolErrorHandler, safe_execute
from human_logging import log_service_status

class ToolService:
    """Service for handling tool detection and execution."""
    
    def __init__(self):
        pass
    
    def detect_and_execute_tool(self, user_message: str, user_id: str, request_id: str) -> Tuple[bool, Optional[str], Optional[str], List[str]]:
        """
        Detect if a tool should be used and execute it.
        
        Returns:
            (tool_used, tool_response, tool_name, debug_info)
        """
        debug_info = []
        
        # Time query detection (with robust patterns)
        if self._is_time_query(user_message):
            return self._execute_time_tool(user_message, user_id, request_id, debug_info)
        
        # Weather query detection
        elif "weather" in user_message.lower():
            return self._execute_weather_tool(user_message, user_id, request_id, debug_info)
        
        # Unit conversion detection
        elif "convert" in user_message.lower() and "to" in user_message.lower():
            return self._execute_conversion_tool(user_message, user_id, request_id, debug_info)
        
        # Other tool detections...
        elif "news" in user_message.lower():
            return self._execute_news_tool(user_message, user_id, request_id, debug_info)
        
        elif "search" in user_message.lower():
            return self._execute_search_tool(user_message, user_id, request_id, debug_info)
        
        elif "exchange rate" in user_message.lower():
            return self._execute_exchange_rate_tool(user_message, user_id, request_id, debug_info)
        
        elif "system info" in user_message.lower():
            return self._execute_system_info_tool(user_message, user_id, request_id, debug_info)
        
        elif self._is_python_code_query(user_message):
            return self._execute_python_tool(user_message, user_id, request_id, debug_info)
        
        elif "wikipedia" in user_message.lower() or "wiki" in user_message.lower():
            return self._execute_wikipedia_tool(user_message, user_id, request_id, debug_info)
        
        # No tool detected
        return False, None, None, debug_info
    
    def _is_time_query(self, message: str) -> bool:
        """Check if the message is a time query."""
        time_patterns = [
            r"time(?:\s*(?:in|for|at))?\s+([a-zA-Z ]+)",
            r"current time in ([a-zA-Z ]+)",
            r"what(?:'s| is) the time in ([a-zA-Z ]+)",
            r"timeanddate\.com.*([a-zA-Z ]+)",
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        
        return "timeanddate.com" in message.lower() or "time" in message.lower()
    
    def _is_python_code_query(self, message: str) -> bool:
        """Check if the message is a Python code execution request."""
        python_indicators = [
            "run python", "python code", "```python", "execute python"
        ]
        return any(indicator in message.lower() for indicator in python_indicators) or message.lower().startswith("python ")
    
    def _execute_time_tool(self, message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute time query tool."""
        system_msg = f"[TOOL] Robust time lookup (geo+timezone, fallback to timeanddate.com) triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        # Extract country/location from message
        country = self._extract_location_from_message(message)
        
        def get_timezone_time():
            country_timezones = {
                "netherlands": "Europe/Amsterdam",
                "amsterdam": "Europe/Amsterdam",
                "london": "Europe/London",
                "uk": "Europe/London",
                "new york": "America/New_York",
                "tokyo": "Asia/Tokyo",
                "paris": "Europe/Paris",
                "berlin": "Europe/Berlin",
                "moscow": "Europe/Moscow",
                "sydney": "Australia/Sydney",
            }
            
            tz = country_timezones.get(country.lower(), None)
            if tz:
                return get_current_time(tz) + f" (timezone: {tz})", "geo_timezone"
            else:
                return self._get_time_from_timeanddate(country), "timeanddate.com"
        
        result = safe_execute(
            get_timezone_time,
            fallback_value=(
                ToolErrorHandler.handle_tool_error(
                    Exception("Time lookup failed"), "time", user_id, country, request_id
                ),
                "error",
            ),
            error_handler=lambda e: ToolErrorHandler.handle_tool_error(
                e, "time", user_id, country, request_id
            ),
        )
        
        user_response, tool_name = result
        debug_info.append(f"[TOOL] Used {tool_name} for {country}")
        
        return True, user_response, "time", debug_info
    
    def _execute_weather_tool(self, message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute weather query tool."""
        system_msg = f"[TOOL] Weather lookup triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        match = re.search(r"weather in ([a-zA-Z ]+)", message, re.IGNORECASE)
        city = match.group(1).strip() if match else "London"
        
        user_response = safe_execute(
            get_weather,
            city,
            fallback_value=ToolErrorHandler.handle_tool_error(
                Exception("Weather lookup failed"), "weather", user_id, city, request_id
            ),
            error_handler=lambda e: ToolErrorHandler.handle_tool_error(
                e, "weather", user_id, city, request_id
            ),
        )
        
        return True, user_response, "weather", debug_info
    
    def _execute_conversion_tool(self, message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute unit conversion tool."""
        system_msg = f"[TOOL] Unit conversion triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        match = re.search(
            r"convert ([\d\.]+) ([a-zA-Z]+(?:s)?) to ([a-zA-Z]+(?:s)?)", message, re.IGNORECASE
        )
        
        if match:
            value, from_unit, to_unit = float(match.group(1)), match.group(2), match.group(3)
            user_response = safe_execute(
                convert_units,
                value,
                from_unit,
                to_unit,
                fallback_value=ToolErrorHandler.handle_tool_error(
                    Exception("Unit conversion failed"),
                    "unit_conversion",
                    user_id,
                    f"{value} {from_unit} to {to_unit}",
                    request_id,
                ),
                error_handler=lambda e: ToolErrorHandler.handle_tool_error(
                    e,
                    "unit_conversion",
                    user_id,
                    f"{value} {from_unit} to {to_unit}",
                    request_id,
                ),
            )
        else:
            user_response = "Please specify conversion like 'convert 10 km to m'."
        
        return True, user_response, "unit_conversion", debug_info
    
    def _execute_search_tool(self, message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute web search tool."""
        system_msg = f"[TOOL] Web search triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        match = re.search(r"search (.+)", message, re.IGNORECASE)
        query = match.group(1) if match else message
        
        # Placeholder implementation
        user_response = "Web search is currently unavailable."
        
        return True, user_response, "web_search", debug_info
    
    def _execute_news_tool(self, message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute news query tool."""
        system_msg = f"[TOOL] News lookup triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        user_response = "News lookup is currently unavailable."
        
        return True, user_response, "news", debug_info
    
    def _execute_exchange_rate_tool(self, message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute exchange rate tool."""
        system_msg = f"[TOOL] Exchange rate lookup triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        match = re.search(
            r"exchange rate ([a-zA-Z]{3}) to ([a-zA-Z]{3})", message, re.IGNORECASE
        )
        
        if match:
            from_cur, to_cur = match.group(1), match.group(2)
            user_response = f"Exchange rate lookup from {from_cur} to {to_cur} is currently unavailable."
        else:
            user_response = "Exchange rate lookup is currently unavailable."
        
        return True, user_response, "exchange_rate", debug_info
    
    def _execute_system_info_tool(self, message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute system info tool."""
        system_msg = f"[TOOL] System info lookup triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        user_response = "System info lookup is currently unavailable."
        
        return True, user_response, "system_info", debug_info
    
    def _execute_python_tool(self, message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute Python code execution tool."""
        system_msg = f"[TOOL] Python code execution triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        # Extract code from message
        code = self._extract_python_code(message)
        
        if not code:
            user_response = "Please provide Python code to execute."
        else:
            user_response = "Python code execution is currently unavailable."
        
        return True, user_response, "python_code_execution", debug_info
    
    def _execute_wikipedia_tool(self, message: str, user_id: str, request_id: str, debug_info: List[str]) -> Tuple[bool, str, str, List[str]]:
        """Execute Wikipedia search tool."""
        system_msg = f"[TOOL] Wikipedia search triggered for user {user_id}"
        logging.debug(system_msg)
        debug_info.append(system_msg)
        
        # Extract search query
        query = (
            message.lower()
            .replace("wikipedia", "")
            .replace("wiki", "")
            .replace("search", "")
            .strip()
        )
        if not query:
            query = "artificial intelligence"  # default
        
        user_response = "Wikipedia search is currently unavailable."
        
        return True, user_response, "wikipedia", debug_info
    
    def _extract_location_from_message(self, message: str) -> str:
        """Extract location/country from time query message."""
        time_patterns = [
            r"time(?:\s*(?:in|for|at))?\s+([a-zA-Z ]+)",
            r"current time in ([a-zA-Z ]+)",
            r"what(?:'s| is) the time in ([a-zA-Z ]+)",
            r"timeanddate\.com.*([a-zA-Z ]+)",
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                country = match.group(1).strip()
                # Clean up extracted location string
                country = re.sub(
                    r"^(is|what|'s|the|current|now|please|tell|me|show|give|provide|can|you|do|does|in|for|at|on|of|about|time|current time|the time)\s+",
                    "",
                    country,
                    flags=re.IGNORECASE,
                )
                country = country.strip()
                country = re.sub(r"\?$", "", country).strip()
                if country:
                    return country
        
        return "netherlands"  # default
    
    def _extract_python_code(self, message: str) -> str:
        """Extract Python code from message."""
        if "```python" in message:
            # Extract code from code blocks
            code_start = message.find("```python") + 9
            code_end = message.find("```", code_start)
            code = (
                message[code_start:code_end].strip()
                if code_end != -1
                else message[code_start:].strip()
            )
        elif "run python" in message.lower():
            code = message.split("run python", 1)[-1].strip()
        elif message.lower().startswith("python "):
            code = message.split("python ", 1)[-1].strip()
        else:
            # Try to extract any code-like text
            code = message.strip()
        
        return code
    
    def _get_time_from_timeanddate(self, country: str) -> str:
        """Stub function for time from timeanddate.com."""
        return f"Time in {country}: Not available"

# Global tool service instance
tool_service = ToolService()
