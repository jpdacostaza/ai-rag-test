#!/usr/bin/env python3
"""
Web Search Flow Demonstration
Shows exactly how your search query flows through the system
"""

print("🔍 WEB SEARCH SYSTEM FLOW EXPLANATION")
print("="*60)

print("\n📋 YOUR SYSTEM HAS 3 WEB SEARCH PATHWAYS:")
print("-"*50)

print("\n1️⃣  DIRECT WEB SEARCH TOOL (Manual)")
print("   • Route: /api/tools/web_search")
print("   • Usage: Direct API calls")
print("   • Input: Your exact query")
print("   • Output: Raw search results")

print("\n2️⃣  AUTO WEB SEARCH FILTER (Automatic)")
print("   • Runs: Automatically on EVERY message")
print("   • Triggers: When keywords detected")
print("   • Process:")
print("     ├─ Detects trigger words in your message")
print("     ├─ Builds optimized search query")
print("     ├─ Performs web search")
print("     └─ Injects results into conversation")

print("\n3️⃣  MANUAL FUNCTION CALLING (Tool Use)")
print("   • Usage: AI model decides to call web search")
print("   • Requires: Tool-calling capable models")
print("   • Process: Model analyzes -> calls function -> gets results")

print("\n" + "="*60)
print("🎯 WHAT HAPPENS WITH YOUR SEARCH QUERY")
print("="*60)

# Simulate the query processing flow
def simulate_query_flow(user_query: str):
    print(f"\n🗣️  USER QUERY: '{user_query}'")
    print("-" * 40)
    
    # Step 1: Trigger Detection
    trigger_keywords = [
        "current", "today", "latest", "news", "headline",
        "search the web", "web search", "lookup", "recent"
    ]
    
    detected_triggers = [kw for kw in trigger_keywords if kw.lower() in user_query.lower()]
    
    if detected_triggers:
        print(f"✅ TRIGGERS DETECTED: {detected_triggers}")
        
        # Step 2: Query Building Process
        print(f"\n🔧 QUERY BUILDING PROCESS:")
        print(f"   📥 Original: '{user_query}'")
        
        # Simulate the _build_query process
        import re
        
        # Remove common words
        cleaned = re.sub(r"\b(please|can you|could you|search|find|look up|web search for|check|get|give me)\b", "", user_query, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        
        if len(cleaned) < 5:
            cleaned = user_query
            
        # Remove question marks and fillers
        cleaned = re.sub(r"[?!]+$", "", cleaned)
        cleaned = re.sub(r"\b(the|a|an|what|when|where|how|why)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        
        final_query = cleaned or user_query
        
        # Add context for news queries
        if any(word in final_query.lower() for word in ['news', 'latest', 'today', 'recent', 'current']):
            if 'news' not in final_query.lower():
                final_query += ' news'
        
        print(f"   🔧 Cleaned: '{cleaned}'")
        print(f"   🎯 Final Search Query: '{final_query}'")
        
        # Step 3: Search Execution
        print(f"\n🌐 SEARCH EXECUTION:")
        print(f"   🔍 Query sent to DuckDuckGo: '{final_query}'")
        print(f"   🌍 Region: eu-en (European English)")
        print(f"   📊 Search Type: NEWS (for news queries)")
        print(f"   📱 Max Results: 5-6")
        
        # Step 4: Result Integration
        print(f"\n💬 RESULT INTEGRATION:")
        print(f"   📥 Search results retrieved")
        print(f"   💉 Results injected into conversation as:")
        print(f"      '[SYSTEM CONTEXT - WEB SEARCH RESULTS]'")
        print(f"   🤖 AI model receives YOUR QUERY + SEARCH RESULTS")
        print(f"   💭 AI generates response using both")
        
    else:
        print("❌ NO TRIGGERS DETECTED - No automatic web search")
        print("   (You can force search by saying 'search the web' or 'web search')")

# Test with different queries
test_queries = [
    "what are the latest headlines for today in europe",
    "tell me about cats",
    "search the web for AI news",
    "what's the current weather in Amsterdam?"
]

for query in test_queries:
    simulate_query_flow(query)
    print("\n" + "🔄" * 20)

print("\n" + "="*60)
print("💡 KEY INSIGHTS:")
print("="*60)
print("✅ Your search DOES use your exact words")
print("✅ But it's cleaned and optimized for better results")
print("✅ European queries get eu-en region for better targeting")
print("✅ News queries automatically use NEWS search type")
print("✅ Results are injected BEFORE the AI responds")
print("✅ You can force search with 'search the web' keywords")
