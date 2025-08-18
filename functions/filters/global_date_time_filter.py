"""
title: Global Date Time Context Filter
author: System
version: 1.0.0
license: MIT
requirements:
description: |-
  Global filter that injects current date and time into every conversation.
  Ensures the AI always knows the exact current date and time.
  Runs with highest priority before all other filters.
"""

from datetime import datetime
from pydantic import BaseModel, Field

PRINT_PREFIX = "[GlobalDateTime]"
print(f"{PRINT_PREFIX} Global Date Time Context Filter v1.0 Imported.")

class Filter:
    """Global Date and Time Context Injection"""
    
    class Valves(BaseModel):
        priority: int = Field(
            default=-10, description="Highest priority - runs before all other filters"
        )
        enable_date_injection: bool = Field(
            default=True, description="Enable automatic date/time context injection"
        )
        include_timezone: bool = Field(
            default=True, description="Include timezone information"
        )
        verbose_format: bool = Field(
            default=True, description="Use verbose date format (Monday, January 1, 2024)"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.type = "filter"
        self.name = "Global Date Time Context"
        self.version = "1.0"
        
    async def inlet(self, body: dict, __user__=None) -> dict:
        """
        Inject current date and time into every conversation
        """
        if not self.valves.enable_date_injection:
            return body

        messages = body.get("messages", [])
        if not messages:
            return body

        # Check if we already have a date context message to avoid duplicates
        has_date_context = any(
            msg.get("role") == "system" and 
            "[CURRENT DATE & TIME]" in msg.get("content", "")
            for msg in messages
        )
        
        if has_date_context:
            return body  # Already has date context, skip

        # Get current date and time
        current_datetime = datetime.now()
        
        if self.valves.verbose_format:
            current_date = current_datetime.strftime('%A, %B %d, %Y')
        else:
            current_date = current_datetime.strftime('%Y-%m-%d')
            
        current_time = current_datetime.strftime('%H:%M:%S')
        
        timezone_info = ""
        if self.valves.include_timezone:
            try:
                timezone_name = current_datetime.astimezone().tzname()
                timezone_info = f" ({timezone_name})"
            except (OSError, ValueError, AttributeError) as e:
                # Handle timezone-related errors gracefully
                timezone_info = ""
        
        # Create date/time context message
        date_time_message = {
            "role": "system",
            "content": f"[CURRENT DATE & TIME]\n\n"
                      f"Today's Date: {current_date}\n"
                      f"Current Time: {current_time}{timezone_info}\n\n"
                      f"You are operating on {current_date} at {current_time}. "
                      f"Use this information to provide accurate, timely responses. "
                      f"When discussing dates, times, or current events, reference this timestamp."
        }
        
        # Insert at the beginning of the messages (after any existing system messages)
        insert_position = 0
        for i, msg in enumerate(messages):
            if msg.get("role") != "system":
                insert_position = i
                break
        else:
            insert_position = len(messages)
            
        messages.insert(insert_position, date_time_message)
        body["messages"] = messages
        
        print(f"{PRINT_PREFIX} Date/time context injected: {current_date} at {current_time}")
        
        return body
