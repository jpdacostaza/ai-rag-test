"""
Smart Web Search Trigger - Anti-Hallucination Pipeline
======================================================

Implements intelligent web search triggering that only activates when:
1. User explicitly requests web search  
2. Model demonstrates uncertainty or lack of knowledge
3. Model's response contains potential inaccuracies that need verification

This is the CORRECT anti-hallucination approach:
- Let model respond first
- Analyze response for uncertainty patterns
- Only trigger web search when needed
"""

import re
from typing import Tuple, Dict, Any, Optional


def should_trigger_web_search_smart(user_query: str, model_response: str, conversation_context: Optional[Dict] = None) -> Tuple[bool, str]:
    """
    Smart web search trigger using anti-hallucination pattern.
    
    Args:
        user_query: The user's original question
        model_response: The model's response to analyze
        conversation_context: Optional context for better decisions
        
    Returns:
        Tuple[bool, str]: (should_trigger, reason)
    """
    query_lower = user_query.lower()
    response_lower = model_response.lower()
    
    # 1. EXPLICIT USER REQUESTS - Always honor these
    explicit_triggers = [
        "search the web", "web search", "look up", "search for", "find online",
        "check online", "search current", "get latest", "look online", 
        "internet search", "google search", "google it", "search news"
    ]
    
    if any(trigger in query_lower for trigger in explicit_triggers):
        return True, "User explicitly requested web search"
    
    # 2. MODEL UNCERTAINTY DETECTION - Key anti-hallucination feature
    uncertainty_indicators = [
        # Direct admissions of uncertainty
        "i don't know", "i do not know", "i'm not sure", "i am not sure",
        "i don't have", "i do not have", "i cannot provide", "i'm unable to",
        "i am unable to", "no information", "not available to me",
        
        # Knowledge limitations
        "my knowledge cutoff", "training data", "last update", "as of my last",
        "i may not have", "might not be accurate", "cannot access", 
        "don't have access", "do not have access",
        
        # Suggestions to search
        "you might want to search", "you should look up", "recommend searching",
        "suggest checking", "might want to verify", "should verify",
        
        # Temporal uncertainty
        "may have changed", "might have changed", "could be different now",
        "check for updates", "verify current", "confirm current"
    ]
    
    uncertainty_detected = any(indicator in response_lower for indicator in uncertainty_indicators)
    if uncertainty_detected:
        return True, "Model expressed uncertainty or knowledge limitations"
    
    # 3. HALLUCINATION RISK PATTERNS - Check for potentially fabricated info
    risk_patterns = [
        # Vague/generic responses that might be hallucinated
        r"according to (?:my|general) (?:knowledge|understanding)",
        r"(?:typically|usually|generally|often) (?:companies|organizations)",
        r"(?:many|most|some) (?:sources|reports) (?:suggest|indicate)",
        
        # Outdated temporal references that need verification
        r"as of \d{4}", r"in \d{4}", r"since \d{4}",
        r"recently", r"lately", r"currently", r"at this time"
    ]
    
    for pattern in risk_patterns:
        if re.search(pattern, response_lower):
            # Only trigger if combined with factual claims about specific entities
            if _contains_factual_claims(model_response, user_query):
                return True, f"Potential hallucination risk detected: {pattern}"
    
    # 4. CURRENT INFORMATION REQUESTS - But only if user asks for recent data
    current_info_queries = [
        "latest", "current", "recent", "today", "now", "2025", 
        "breaking", "new", "updated", "fresh"
    ]
    
    context_indicators = [
        "news", "events", "status", "happening", "announced", 
        "reported", "developments", "updates"
    ]
    
    has_currency_request = any(term in query_lower for term in current_info_queries)
    has_context = any(term in query_lower for term in context_indicators)
    
    if has_currency_request and has_context:
        # But only if model doesn't confidently provide recent information
        confidence_indicators = [
            "here are the latest", "current status is", "as of today",
            "recent developments include", "breaking news"
        ]
        
        model_seems_confident = any(indicator in response_lower for indicator in confidence_indicators)
        
        if not model_seems_confident:
            return True, "User requested current information but model response lacks recent data"
    
    # 5. VERIFICATION REQUESTS - When user wants to double-check
    verification_keywords = [
        "verify", "confirm", "double-check", "make sure", "check if",
        "is this still", "has this changed", "is this accurate", "fact check"
    ]
    
    if any(keyword in query_lower for keyword in verification_keywords):
        return True, "User requested verification of information"
    
    return False, "No trigger conditions met - model response appears sufficient"


def _contains_factual_claims(response: str, query: str) -> bool:
    """Check if response contains specific factual claims that could be hallucinated."""
    # Look for specific data, dates, numbers, company details, etc.
    factual_patterns = [
        r"\$[\d,.]+ (?:million|billion|trillion)",  # Financial figures
        r"\d{1,2}/\d{1,2}/\d{4}",  # Dates
        r"\d+,?\d* employees",  # Employee counts
        r"founded in \d{4}",  # Company founding dates
        r"(?:CEO|president|founder) (?:is|was) \w+",  # Leadership claims
        r"\d+% (?:of|increase|decrease)",  # Percentage claims
        r"(?:located|based) in \w+",  # Location claims
    ]
    
    for pattern in factual_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            return True
    
    return False


def analyze_response_quality(response: str) -> Dict[str, Any]:
    """
    Analyze the quality and confidence level of a model response.
    
    Returns:
        Dict with analysis metrics including confidence_score, uncertainty_level, etc.
    """
    response_lower = response.lower()
    
    # Calculate confidence indicators
    confident_phrases = [
        "i know", "according to", "the company is", "it is", "they are",
        "specifically", "exactly", "definitely", "certainly"
    ]
    
    uncertain_phrases = [
        "i think", "probably", "likely", "might", "could be", "seems to",
        "appears to", "possibly", "perhaps", "maybe"
    ]
    
    confidence_score = len([p for p in confident_phrases if p in response_lower])
    uncertainty_score = len([p for p in uncertain_phrases if p in response_lower])
    
    # Calculate information density (factual content vs fluff)
    factual_patterns = [
        r"\d+", r"[A-Z][a-z]+ [A-Z][a-z]+",  # Numbers, proper nouns
        r"(?:founded|established|created) in", r"(?:based|located) in"
    ]
    
    factual_content = sum(len(re.findall(pattern, response)) for pattern in factual_patterns)
    
    return {
        "confidence_score": confidence_score,
        "uncertainty_score": uncertainty_score,
        "factual_content_level": factual_content,
        "response_length": len(response.split()),
        "quality_rating": "high" if confidence_score > uncertainty_score and factual_content > 2 else "low"
    }


# Test cases for validation
def test_smart_trigger():
    """Test cases to validate the smart trigger logic."""
    test_cases = [
        # Should NOT trigger - confident response
        {
            "query": "What does Swift company do?",
            "response": "Swift is a financial technology company that provides banking platforms and solutions. They offer various services that enable banks, fintech companies, and other financial institutions to streamline their operations.",
            "expected": False,
            "reason": "Confident response with specific information"
        },
        
        # SHOULD trigger - uncertainty
        {
            "query": "What does Swift company do?", 
            "response": "I don't have current information about Swift company. You might want to search for the latest details about their services.",
            "expected": True,
            "reason": "Model expressed uncertainty"
        },
        
        # SHOULD trigger - explicit request
        {
            "query": "Search the web for Swift company information",
            "response": "I'll search for information about Swift company.",
            "expected": True,
            "reason": "Explicit search request"
        },
        
        # SHOULD trigger - current info request without confidence
        {
            "query": "What are the latest news about Swift company?",
            "response": "Swift is a technology company, but I may not have the most recent updates about their current developments.",
            "expected": True,
            "reason": "Current info requested but model lacks recent data"
        },
        
        # Should NOT trigger - current info with confidence
        {
            "query": "What are the latest news about Swift company?",
            "response": "Here are the latest developments: Swift company announced major partnerships and continues to expand their financial services platform as of today.",
            "expected": False,
            "reason": "Model confidently provided current information"
        }
    ]
    
    print(" Testing Smart Web Search Trigger Logic\n")
    
    for i, test in enumerate(test_cases, 1):
        should_trigger, reason = should_trigger_web_search_smart(test["query"], test["response"])
        status = "[OK] PASS" if should_trigger == test["expected"] else "[FAIL] FAIL"
        
        print(f"Test {i}: {status}")
        print(f"Query: {test['query']}")
        print(f"Response: {test['response'][:100]}...")
        print(f"Expected: {test['expected']} | Got: {should_trigger}")
        print(f"Reason: {reason}")
        print(f"Expected Reason: {test['reason']}\n")


if __name__ == "__main__":
    test_smart_trigger()
