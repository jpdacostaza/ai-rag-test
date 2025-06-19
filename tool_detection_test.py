#!/usr/bin/env python3
"""
Test script to check if our test messages trigger tool detection
"""
import re

test_messages = [
    "Tell me about artificial intelligence. This message should trigger comprehensive debug logging.",
    "Please explain quantum computing in simple terms. This is a unique test message after the syntax fix.",
    "Can you explain machine learning? This is the final debug test after fixing all syntax issues.",
    "Debug test: what is 2+2? This should show debug info.",
    "What are the three laws of robotics? This is after the indentation fix.",
]


def check_tool_triggers(message):
    triggers = []

    # Weather detection
    if "weather" in message.lower():
        triggers.append("WEATHER TOOL")

    # News detection
    if "news" in message.lower():
        triggers.append("NEWS TOOL")

    # Time detection (broad pattern)
    if re.search(r"\b(current|what).*time\b", message, re.IGNORECASE):
        triggers.append("TIME TOOL")

    # Wikipedia detection
    if "wikipedia" in message.lower() or "wiki" in message.lower():
        triggers.append("WIKIPEDIA TOOL")

    # Search detection (if it existed)
    if "search" in message.lower():
        triggers.append("SEARCH TOOL")

    return triggers


print("TOOL DETECTION ANALYSIS")
print("=" * 50)

for i, message in enumerate(test_messages, 1):
    print(f"\nTEST MESSAGE {i}:")
    print(f"Message: {message}")
    triggers = check_tool_triggers(message)
    if triggers:
        print(f"🚨 TRIGGERS: {', '.join(triggers)}")
        print("❌ This message would NOT reach LLM path!")
    else:
        print("✅ No tool triggers - would reach LLM path")

print("\n" + "=" * 50)
print("CONCLUSION: Check if any test messages incorrectly trigger tools")
