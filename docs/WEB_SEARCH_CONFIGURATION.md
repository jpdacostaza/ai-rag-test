"""
Optimized Web Search Configuration Summary
=========================================
Date: July 24, 2025

OVERVIEW
========
The web search system has been optimized to trigger ONLY when necessary, 
following your requirements:

1. 🤔 Model doesn't know something (uncertainty detection)
2. 🔄 Needs to verify/update current knowledge (currency detection)  
3. 🔍 User explicitly requests web search (explicit triggers)

TRIGGERING CONDITIONS
====================

1. EXPLICIT USER REQUESTS 🔍
---------------------------
Web search triggers when user explicitly asks for search:

✅ TRIGGERS:
- "search the web for..."
- "web search latest news"
- "look up current weather"
- "google the latest AI developments"
- "find online information about..."
- "check online for..."
- "search current information"
- "get latest updates"

❌ DOES NOT TRIGGER:
- "what is Python programming" (general knowledge)
- "tell me about machine learning" (educational request)
- "explain quantum physics" (no search request)

2. MODEL UNCERTAINTY 🤔
-----------------------
Web search triggers when model admits lack of knowledge:

✅ TRIGGERS:
- "I don't know about that topic"
- "I'm not sure about current events"
- "I cannot provide current information"
- "My training data ends in 2023"
- "I need to search for that"
- "I should look that up"
- "As of my last update..."
- "I cannot access recent information"

❌ DOES NOT TRIGGER:
- "Python is a programming language" (confident response)
- "The capital of France is Paris" (factual knowledge)
- General educational responses

3. CURRENT INFORMATION REQUESTS 📰
----------------------------------
Web search triggers for recent/current information WITH context:

✅ TRIGGERS (needs BOTH currency + context):
- "latest news today" (currency: latest + context: news)
- "current events happening now" (currency: current + context: events)
- "recent updates on climate" (currency: recent + context: updates)
- "breaking news reports" (currency: breaking + context: news)
- "2025 election updates" (currency: 2025 + context: updates)

❌ DOES NOT TRIGGER (missing context):
- "current weather" (currency but no news/event context)
- "latest version of Python" (currency but technical, not news)
- "today's temperature" (currency but not news/events)

Currency Keywords: latest, current, today, recent, breaking, now, live, 2025
Context Keywords: news, event, status, happening, announce, report, update

4. VERIFICATION REQUESTS 🔄
---------------------------
Web search triggers when verification is needed:

✅ TRIGGERS:
- "verify if this information is current"
- "can you confirm the latest status"
- "double-check if this has changed"
- "is this information still accurate"
- "make sure this is up to date"
- "check if this is still true"

❌ DOES NOT TRIGGER:
- "what is the capital of France" (no verification needed)
- Basic factual questions without verification context

CONFIGURATION DETAILS
=====================

Pipeline: Enhanced Web Search Pipeline
Location: pipelines/pipeline_web_search/enhanced_web_search_pipeline.py
Type: Filter Pipeline (pre and post-processing)
Priority: 0
Auto Search: Enabled
Max Results: 5

Search Methods (in order):
1. DuckDuckGo instances (primary)
2. Brave Search API (secondary) 
3. DuckDuckGo Instant (fallback)
4. Curated current news (emergency fallback)

TESTING
=======

Run test suite:
```bash
python tests/test_web_search_triggers.py
```

Validate pipeline:
```bash
python pipelines/pipeline_web_search/validate_pipeline.py
```

EXAMPLES OF BEHAVIOR
===================

✅ WILL TRIGGER WEB SEARCH:
- "search for latest AI developments" (explicit request)
- "what's the latest news today?" (current + news context)
- Model responds: "I don't know about recent events" (uncertainty)
- "verify if this company still exists" (verification request)

❌ WILL NOT TRIGGER WEB SEARCH:
- "explain machine learning" (general knowledge)
- "what is Python programming?" (educational, not current)
- "current temperature" (missing news/event context)
- "tell me a joke" (entertainment, not information)

BENEFITS
========

✅ Reduced unnecessary web searches
✅ Faster response times for general knowledge
✅ More focused and relevant search results
✅ Better user experience with selective searching
✅ Lower API usage and costs
✅ Improved system reliability

MONITORING
==========

The system logs search triggers with reasons:
- "🔍 Web search triggered: Explicit user request"
- "🔍 Web search triggered: Model uncertainty detected"
- "🔍 Web search triggered: Current information request"
- "🔍 Web search triggered: Verification request"

Check container logs to monitor web search activity:
```bash
docker logs backend-pipelines | grep "Web search triggered"
```

This optimized configuration ensures web search is used intelligently,
only when truly needed, providing better performance and user experience.
"""
