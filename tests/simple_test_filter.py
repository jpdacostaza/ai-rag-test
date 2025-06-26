"""
title: Simple Test Filter
author: Backend Team
version: 1.0.0
description: Simple test filter that adds a visible message to every conversation
"""


class Filter:
    """TODO: Add proper docstring for Filter class."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        pass

    def inlet(self, body: dict, user=None) -> dict:
        """Add a visible test message to every conversation"""

        try:
            messages = body.get("messages", [])
            if messages:
                # Add a visible system message
                test_message = {
                    "role": "system",
                    "content": "🧪 TEST FILTER ACTIVE: This message confirms that OpenWebUI filters are working!",
                }

                # Insert at the beginning
                messages.insert(0, test_message)
                body["messages"] = messages

        except Exception as e:
            # If there's any error, add an error message
            messages = body.get("messages", [])
            if messages:
                error_message = {"role": "system", "content": f"❌ FILTER ERROR: {str(e)}"}
                messages.insert(0, error_message)
                body["messages"] = messages

        return body
