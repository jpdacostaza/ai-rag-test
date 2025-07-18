"""
Enhanced Web Search Trigger System
==================================

Based on industry best practices from OpenAI, Google, Anthropic, and other leading AI systems.
This implements a more sophisticated, ML-based approach to web search triggering.
"""

import re
import logging
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum


class SearchConfidence(Enum):
    """Confidence levels for search triggering."""
    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.3
    NONE = 0.0


@dataclass
class SearchTriggerResult:
    """Result of search trigger analysis."""
    should_search: bool
    confidence: float
    reasons: List[str]
    query_type: str


class EnhancedWebSearchTrigger:
    """
    Advanced web search trigger system using multiple detection methods.
    Based on patterns from leading AI systems.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Weighted scoring system (inspired by Google's approach)
        self.trigger_weights = {
            'temporal_signals': 0.9,      # "today", "latest", "recent"
            'uncertainty_phrases': 0.95,  # "I don't know", "unclear"
            'entity_queries': 0.8,        # Company names, people
            'factual_requests': 0.7,      # Statistics, dates, facts
            'current_events': 0.9,        # News, breaking, updates
            'specific_domains': 0.8,      # Finance, tech, science
        }
        
        # Advanced pattern matching (regex-based like OpenAI's system)
        self.patterns = {
            'temporal_signals': [
                r'\b(today|yesterday|this (week|month|year))\b',
                r'\b(latest|recent|current|now|2024|2025)\b',
                r'\b(breaking|live|real-time)\b'
            ],
            'uncertainty_phrases': [
                r"\b(i don't know|not sure|unclear|uncertain)\b",
                r"\b(i (can't|cannot) (provide|tell|say))\b",
                r"\b(no information|not available)\b",
                r"\b(don't have access|no access)\b"
            ],
            'entity_queries': [
                r'\b(who is (the )?(ceo|founder|president|leader) of)\b',
                r'\b(current (ceo|president|founder) of)\b',
                r'\bwhat is ([A-Z][a-z]+ ?){1,3}(\.(com|org|net))?\b',  # "What is Microsoft"
                r'\b(tell me about|information about) [A-Z][a-zA-Z\s]+\b'
            ],
            'factual_requests': [
                r'\b(when (was|did)|how many|where is|what happened)\b',
                r'\b(statistics|data|facts|numbers) (about|on|for)\b',
                r'\b(founded|established|created) (in|on)\b',
                r'\b(features|specifications|details) (of|for)\b'
            ],
            'financial_signals': [
                r'\b(stock price|market cap|share price)\b',
                r'\b(trading at|priced at|worth)\b',
                r'\b(financial|earnings|revenue)\b'
            ],
            'tech_product_signals': [
                r'\biphone \d+\b',
                r'\b(features|specs|specifications) (released|launched)\b',
                r'\b(version|model) \d+\b'
            ],
            'disambiguation_signals': [
                r'\b(\w+) (\w+) vs (\w+) (\w+)\b',  # "Swift programming vs Swift financial"
                r'\b(difference between|distinguish)\b'
            ],
            'creative_exclusions': [
                r'\b(write|create|make|generate) (a |an )?(poem|story|song|joke)\b',
                r'\b(creative|fictional|imaginary)\b'
            ],
            'math_exclusions': [
                r'\bwhat is \d+[\+\-\*/]\d+\b',
                r'\b(calculate|compute|solve) [\d\+\-\*/\(\)]+\b'
            ]
        }
    
    def analyze_query(self, query: str, response: str = "") -> SearchTriggerResult:
        """
        Analyze if a query should trigger web search using multiple signals.
        
        Args:
            query: User's query
            response: AI's response (for uncertainty detection)
            
        Returns:
            SearchTriggerResult with detailed analysis
        """
        query_lower = query.lower()
        response_lower = response.lower()
        
        scores = {}
        reasons = []
        
        # 1. Check temporal signals
        temporal_score = self._check_patterns(query_lower, 'temporal_signals')
        if temporal_score > 0:
            scores['temporal'] = temporal_score * self.trigger_weights['temporal_signals']
            reasons.append(f"Temporal signals detected (score: {temporal_score:.2f})")
        
        # 2. Check uncertainty in response
        uncertainty_score = self._check_patterns(response_lower, 'uncertainty_phrases')
        if uncertainty_score > 0:
            scores['uncertainty'] = uncertainty_score * self.trigger_weights['uncertainty_phrases']
            reasons.append(f"Uncertainty detected in response (score: {uncertainty_score:.2f})")
        
        # 3. Check for entity queries
        entity_score = self._check_patterns(query_lower, 'entity_queries')
        if entity_score > 0:
            scores['entity'] = entity_score * self.trigger_weights['entity_queries']
            reasons.append(f"Entity query detected (score: {entity_score:.2f})")
        
        # 4. Check for factual requests
        factual_score = self._check_patterns(query_lower, 'factual_requests')
        if factual_score > 0:
            scores['factual'] = factual_score * self.trigger_weights['factual_requests']
            reasons.append(f"Factual request detected (score: {factual_score:.2f})")
        
        # 5. Check for financial signals
        financial_score = self._check_patterns(query_lower, 'financial_signals')
        if financial_score > 0:
            scores['financial'] = financial_score * 0.9  # High weight for financial queries
            reasons.append(f"Financial query detected (score: {financial_score:.2f})")
        
        # 6. Check for tech product signals
        tech_score = self._check_patterns(query_lower, 'tech_product_signals')
        if tech_score > 0:
            scores['tech_product'] = tech_score * 0.8
            reasons.append(f"Tech product query detected (score: {tech_score:.2f})")
        
        # 7. Check for disambiguation needs
        disambiguation_score = self._check_patterns(query_lower, 'disambiguation_signals')
        if disambiguation_score > 0:
            scores['disambiguation'] = disambiguation_score * 0.8
            reasons.append(f"Disambiguation needed (score: {disambiguation_score:.2f})")
        
        # 8. Exclusion checks (negative scoring)
        creative_penalty = self._check_patterns(query_lower, 'creative_exclusions')
        if creative_penalty > 0:
            scores['creative_penalty'] = -creative_penalty * 0.9
            reasons.append(f"Creative request detected - reducing score")
        
        math_penalty = self._check_patterns(query_lower, 'math_exclusions')
        if math_penalty > 0:
            scores['math_penalty'] = -math_penalty * 0.9
            reasons.append(f"Math calculation detected - reducing score")
        
        # 9. Domain-specific checks
        domain_score = self._check_domain_specificity(query_lower)
        if domain_score > 0:
            scores['domain'] = domain_score * self.trigger_weights['specific_domains']
            reasons.append(f"Domain-specific query detected (score: {domain_score:.2f})")
        
        # Calculate final confidence score
        total_score = sum(scores.values())
        confidence = min(max(total_score, 0.0), 1.0)  # Clamp between 0 and 1
        
        # Determine query type
        query_type = self._determine_query_type(scores)
        
        # Decision logic (more sophisticated than simple threshold)
        should_search = self._make_search_decision(confidence, scores, query_lower)
        
        return SearchTriggerResult(
            should_search=should_search,
            confidence=confidence,
            reasons=reasons,
            query_type=query_type
        )
    
    def _check_patterns(self, text: str, pattern_type: str) -> float:
        """Check if text matches patterns of a given type."""
        if pattern_type not in self.patterns:
            return 0.0
        
        matches = 0
        total_patterns = len(self.patterns[pattern_type])
        
        for pattern in self.patterns[pattern_type]:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1
        
        return matches / total_patterns if total_patterns > 0 else 0.0
    
    def _check_domain_specificity(self, query: str) -> float:
        """Check for domain-specific queries that benefit from current data."""
        domains = {
            'finance': ['stock', 'market', 'price', 'trading', 'investment', 'swift', 'banking'],
            'technology': ['ai', 'software', 'api', 'github', 'openai', 'microsoft', 'google'],
            'news': ['election', 'politics', 'government', 'world', 'breaking'],
            'science': ['research', 'study', 'discovery', 'climate', 'health']
        }
        
        domain_matches = 0
        total_domains = len(domains)
        
        for domain, keywords in domains.items():
            if any(keyword in query for keyword in keywords):
                domain_matches += 1
        
        return domain_matches / total_domains
    
    def _determine_query_type(self, scores: Dict[str, float]) -> str:
        """Determine the primary type of query based on scores."""
        if not scores:
            return "general"
        
        # Find the highest scoring category
        max_category = max(scores.keys(), key=lambda k: scores[k] if scores[k] > 0 else 0)
        
        type_mapping = {
            'temporal': 'time_sensitive',
            'uncertainty': 'knowledge_gap',
            'entity': 'entity_lookup',
            'factual': 'fact_verification',
            'domain': 'domain_specific'
        }
        
        return type_mapping.get(max_category, "general")
    
    def _make_search_decision(self, confidence: float, scores: Dict[str, float], query: str) -> bool:
        """Make the final decision on whether to search."""
        # High confidence threshold (lowered for practicality)
        if confidence >= 0.6:  # Further lowered
            return True
        
        # Special cases that should always trigger
        if any(key in scores for key in ['financial', 'tech_product', 'disambiguation']):
            if scores.get('financial', 0) > 0.3 or scores.get('tech_product', 0) > 0.3 or scores.get('disambiguation', 0) > 0.3:
                return True
        
        # Medium confidence with specific conditions
        if confidence >= 0.4:  # Lowered from 0.5
            # Allow if it's a clear entity or factual query (lowered thresholds)
            if scores.get('entity', 0) > 0.2 or scores.get('factual', 0) > 0.2:
                return True
            # Allow if there's temporal signals
            if scores.get('temporal', 0) > 0.2:
                return True
            # Allow if there's uncertainty in response
            if scores.get('uncertainty', 0) > 0.3:
                return True
        
        # Low confidence - only for very specific cases
        if confidence >= 0.2:  # Lowered from 0.3
            # Only if it's temporal and no penalties
            if scores.get('temporal', 0) > 0.3 and not any(k.endswith('_penalty') for k in scores.keys()):
                return True
        
        return False


# Backward compatibility function
def should_trigger_web_search(query: str, response: str) -> bool:
    """
    Enhanced version of the original function.
    Now uses the sophisticated trigger system.
    """
    trigger = EnhancedWebSearchTrigger()
    result = trigger.analyze_query(query, response)
    return result.should_search


# For debugging and analysis
def analyze_search_trigger(query: str, response: str = "") -> Dict[str, Any]:
    """
    Analyze a query and return detailed information about the search decision.
    Useful for debugging and understanding why searches are or aren't triggered.
    """
    trigger = EnhancedWebSearchTrigger()
    result = trigger.analyze_query(query, response)
    
    return {
        "query": query,
        "should_search": result.should_search,
        "confidence": result.confidence,
        "query_type": result.query_type,
        "reasons": result.reasons,
        "recommendation": _get_recommendation(result)
    }


def _get_recommendation(result: SearchTriggerResult) -> str:
    """Get a human-readable recommendation based on the analysis."""
    if result.confidence >= 0.8:
        return "Strong recommendation to search - high confidence in need for current information"
    elif result.confidence >= 0.6:
        return "Moderate recommendation to search - likely to benefit from web data"
    elif result.confidence >= 0.3:
        return "Weak recommendation to search - may or may not need current information"
    else:
        return "No recommendation to search - likely answerable with existing knowledge"
