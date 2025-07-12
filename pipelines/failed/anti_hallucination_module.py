"""
Anti-Hallucination Pipeline Module
==================================

Dedicated module for preventing AI hallucination through various techniques:
1. Confidence scoring
2. Knowledge gap detection
3. Fact verification triggers
4. Response quality assessment

Based on techniques used by OpenAI, Anthropic, and Google DeepMind.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class ConfidenceLevel(Enum):
    """Confidence levels for AI responses."""
    VERY_HIGH = 0.9
    HIGH = 0.7
    MEDIUM = 0.5
    LOW = 0.3
    VERY_LOW = 0.1


@dataclass
class HallucinationRisk:
    """Assessment of hallucination risk for a response."""
    risk_level: str
    confidence_score: float
    triggers: List[str]
    recommendations: List[str]
    should_verify: bool


class AntiHallucinationPipeline:
    """
    Pipeline module for detecting and preventing AI hallucination.
    
    This module analyzes queries and responses to:
    1. Detect when the AI might hallucinate
    2. Trigger fact verification processes
    3. Assess response confidence
    4. Provide guardrails against false information
    """
    
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)
        
        # Hallucination risk indicators
        self.risk_patterns = {
            'high_risk': [
                # Specific claims that could be wrong
                r'\b(exactly|precisely) \d+\b',  # "exactly 47 people"
                r'\b(founded|established|created) (in|on) \d{4}\b',  # Specific dates
                r'\b(costs|priced at|worth) \$[\d,]+\b',  # Specific prices
                r'\baccording to (recent|latest) (study|report)\b',  # Recent studies
                r'\bas of (today|now|currently)\b',  # Current state claims
            ],
            'medium_risk': [
                # General factual claims
                r'\b(the (ceo|president|founder) of \w+ is)\b',
                r'\b(headquarters (is|are) (in|at))\b',
                r'\b(has (approximately|around|about) \d+)\b',
                r'\b(recently (announced|released|launched))\b',
            ],
            'uncertainty_indicators': [
                # Good - AI expressing uncertainty
                r'\b(i believe|i think|it seems|appears to)\b',
                r'\b(likely|probably|possibly|might be)\b',
                r'\b(as far as i know|to my knowledge)\b',
                r'\b(i don\'t have (current|recent|latest))\b',
            ],
            'confidence_boosters': [
                # Concerning - overconfident language
                r'\b(definitely|certainly|absolutely|without doubt)\b',
                r'\b(it is (clear|obvious|evident) that)\b',
                r'\b(there is no question that)\b',
                r'\b(everyone knows that)\b',
            ]
        }
        
        # Knowledge gap indicators
        self.knowledge_gaps = {
            'temporal': [
                'current', 'latest', 'recent', 'today', 'now', '2024', '2025',
                'this year', 'this month', 'breaking', 'live'
            ],
            'dynamic_data': [
                'stock price', 'market value', 'current ceo', 'latest version',
                'real-time', 'up-to-date', 'current status'
            ],
            'specific_facts': [
                'exact number', 'precise date', 'specific location',
                'current address', 'phone number', 'email address'
            ]
        }
    
    def assess_hallucination_risk(self, query: str, response: str) -> HallucinationRisk:
        """
        Assess the risk of hallucination in a response.
        
        Args:
            query: User's original query
            response: AI's response to analyze
            
        Returns:
            HallucinationRisk assessment
        """
        triggers = []
        recommendations = []
        confidence_score = 0.7  # Default medium confidence
        
        # Check for high-risk patterns
        high_risk_count = self._count_pattern_matches(response, 'high_risk')
        if high_risk_count > 0:
            triggers.append(f"High-risk factual claims detected ({high_risk_count})")
            confidence_score -= 0.3
            recommendations.append("Verify specific facts and figures with web search")
        
        # Check for medium-risk patterns  
        medium_risk_count = self._count_pattern_matches(response, 'medium_risk')
        if medium_risk_count > 0:
            triggers.append(f"Medium-risk factual claims detected ({medium_risk_count})")
            confidence_score -= 0.2
            recommendations.append("Consider fact-checking general claims")
        
        # Check for good uncertainty indicators
        uncertainty_count = self._count_pattern_matches(response, 'uncertainty_indicators')
        if uncertainty_count > 0:
            triggers.append(f"Appropriate uncertainty expressed ({uncertainty_count})")
            confidence_score += 0.1
            recommendations.append("Good - AI expressing appropriate uncertainty")
        
        # Check for overconfidence
        overconfident_count = self._count_pattern_matches(response, 'confidence_boosters')
        if overconfident_count > 0:
            triggers.append(f"Overconfident language detected ({overconfident_count})")
            confidence_score -= 0.2
            recommendations.append("Response may be overconfident - verify claims")
        
        # Check if query requires current information
        needs_current_info = self._check_knowledge_gaps(query)
        if needs_current_info:
            triggers.append("Query requires current/dynamic information")
            confidence_score -= 0.3
            recommendations.append("Search for current information before responding")
        
        # Clamp confidence score
        confidence_score = max(0.0, min(1.0, confidence_score))
        
        # Determine risk level
        if confidence_score >= 0.7:
            risk_level = "LOW"
        elif confidence_score >= 0.5:
            risk_level = "MEDIUM"
        elif confidence_score >= 0.3:
            risk_level = "HIGH"
        else:
            risk_level = "VERY_HIGH"
        
        # Decide if verification is needed
        should_verify = (
            confidence_score < 0.6 or 
            high_risk_count > 0 or 
            needs_current_info or
            overconfident_count > 1
        )
        
        return HallucinationRisk(
            risk_level=risk_level,
            confidence_score=confidence_score,
            triggers=triggers,
            recommendations=recommendations,
            should_verify=should_verify
        )
    
    def create_safe_response_guidelines(self, query: str) -> Dict[str, Any]:
        """
        Create guidelines for generating a safe, non-hallucinatory response.
        
        Args:
            query: User's query
            
        Returns:
            Guidelines for safe response generation
        """
        guidelines = {
            "uncertainty_phrases": [
                "Based on my knowledge",
                "As far as I know",
                "I believe",
                "It appears that",
                "According to my training data"
            ],
            "verification_suggestions": [],
            "avoid_patterns": [],
            "safe_alternatives": []
        }
        
        # Analyze query for potential risks
        needs_current_info = self._check_knowledge_gaps(query)
        
        if needs_current_info:
            guidelines["verification_suggestions"].extend([
                "I don't have access to current information",
                "For the most up-to-date information, you might want to check",
                "This information may have changed recently"
            ])
            guidelines["avoid_patterns"].extend([
                "Avoid specific current dates, prices, or statistics",
                "Don't claim current status without verification",
                "Avoid 'as of today' or 'currently' statements"
            ])
        
        # Add query-specific guidelines
        if any(word in query.lower() for word in ['stock', 'price', 'cost', 'value']):
            guidelines["safe_alternatives"].append(
                "For current pricing information, I'd recommend checking the official website or financial sources"
            )
        
        if any(word in query.lower() for word in ['ceo', 'president', 'leader']):
            guidelines["safe_alternatives"].append(
                "Leadership positions can change frequently. For the most current information, check the company's official website"
            )
        
        return guidelines
    
    def _count_pattern_matches(self, text: str, pattern_type: str) -> int:
        """Count matches for a specific pattern type."""
        if pattern_type not in self.risk_patterns:
            return 0
        
        count = 0
        for pattern in self.risk_patterns[pattern_type]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            count += len(matches)
        
        return count
    
    def _check_knowledge_gaps(self, query: str) -> bool:
        """Check if query falls into knowledge gap categories."""
        query_lower = query.lower()
        
        for gap_type, keywords in self.knowledge_gaps.items():
            if any(keyword in query_lower for keyword in keywords):
                if self.debug_mode:
                    self.logger.info(f"Knowledge gap detected: {gap_type}")
                return True
        
        return False
    
    def generate_uncertainty_disclaimer(self, confidence_score: float, query_type: str) -> str:
        """Generate appropriate uncertainty disclaimer based on confidence."""
        if confidence_score >= 0.8:
            return ""  # High confidence, no disclaimer needed
        
        disclaimers = {
            'temporal': "Please note that this information may not reflect the most current situation.",
            'factual': "I recommend verifying specific facts from authoritative sources.",
            'dynamic': "This type of information changes frequently, so please check current sources.",
            'general': "Please verify this information from reliable sources if accuracy is critical."
        }
        
        return disclaimers.get(query_type, disclaimers['general'])


# Integration functions for existing pipeline
def assess_response_safety(query: str, response: str) -> Dict[str, Any]:
    """
    Assess the safety of an AI response and provide recommendations.
    
    Args:
        query: Original user query
        response: AI response to assess
        
    Returns:
        Safety assessment with recommendations
    """
    pipeline = AntiHallucinationPipeline()
    risk_assessment = pipeline.assess_hallucination_risk(query, response)
    guidelines = pipeline.create_safe_response_guidelines(query)
    
    return {
        "risk_assessment": {
            "risk_level": risk_assessment.risk_level,
            "confidence_score": risk_assessment.confidence_score,
            "should_verify": risk_assessment.should_verify,
            "triggers": risk_assessment.triggers,
            "recommendations": risk_assessment.recommendations
        },
        "safety_guidelines": guidelines,
        "suggested_disclaimer": pipeline.generate_uncertainty_disclaimer(
            risk_assessment.confidence_score, 
            "general"
        )
    }


def should_fact_check(query: str, response: str) -> bool:
    """
    Determine if a response should be fact-checked.
    
    Args:
        query: Original user query
        response: AI response
        
    Returns:
        True if fact-checking is recommended
    """
    pipeline = AntiHallucinationPipeline()
    risk_assessment = pipeline.assess_hallucination_risk(query, response)
    return risk_assessment.should_verify
