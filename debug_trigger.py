#!/usr/bin/env python3
"""Debug web search trigger logic"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities.enhanced_web_search import should_trigger_web_search

# Test the problematic query
query = "Hello my name is J.P. I work at swift, can you remember that.. ? I like pizza and sanwiches,"
result = should_trigger_web_search(query, "")

print(f"🧪 Testing Web Search Trigger Logic")
print(f"=" * 50)
print(f"Query: {query}")
print(f"Should trigger: {result}")
print()

# Check individual components
query_lower = query.lower()
print(f"Query lowercase: {query_lower}")
print()

# Check for explicit triggers
explicit_triggers = [
    "search the web", "web search", "look up", "search for", "find online",
    "check online", "search current", "get latest", "look online",
    "internet search", "google", "search news", "current information"
]
explicit_found = [t for t in explicit_triggers if t in query_lower]
print(f"Explicit triggers found: {explicit_found}")

# Check for currency + context
currency_keywords = ["latest", "current", "today", "recent", "breaking", "now", "live", "2025"]
context_keywords = ["news", "event", "status", "happening", "announce", "report", "update"]

currency_found = [k for k in currency_keywords if k in query_lower]
context_found = [k for k in context_keywords if k in query_lower]

print(f"Currency keywords found: {currency_found}")
print(f"Context keywords found: {context_found}")

has_currency = len(currency_found) > 0
has_context = len(context_found) > 0
currency_context_trigger = has_currency and has_context

print(f"Has currency: {has_currency}")
print(f"Has context: {has_context}")
print(f"Currency+Context trigger: {currency_context_trigger}")

# Check verification keywords
verification_keywords = [
    "verify", "confirm", "double-check", "make sure", "check if",
    "is this still", "has this changed", "is this current", "update on"
]
verification_found = [k for k in verification_keywords if k in query_lower]
print(f"Verification keywords found: {verification_found}")

print()
print(f"Final result: {result}")
print("This should be FALSE for a simple introduction!")
