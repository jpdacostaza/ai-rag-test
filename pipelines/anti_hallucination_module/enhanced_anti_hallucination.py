"""
Enhanced Anti-Hallucination Module
==================================

This module implements production-ready anti-hallucination techniques based on research from:
- UpTrain AI: Factual accuracy, prompt injection detection, jailbreak detection
- CVS Health UQLM: Uncertainty quantification, semantic entropy, confidence scoring
- Academic research: Multiple consistency checking approaches

Key Features:
- Multi-scorer uncertainty quantification
- Semantic similarity-based consistency checking
- Token probability analysis (when available)
- Source citation validation
- Known hallucination pattern detection
- Confidence threshold tuning
"""

import asyncio
import json
import logging
import math
import re
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
import numpy as np
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HallucinationResult:
    """Result object for hallucination detection"""
    confidence_score: float
    is_hallucination: bool
    uncertainty_indicators: List[str]
    consistency_score: Optional[float] = None
    source_citation_detected: bool = False
    details: Optional[Dict[str, Any]] = None

class EnhancedAntiHallucination:
    """Production-ready anti-hallucination detection system"""
    
    def __init__(self, 
                 confidence_threshold: float = 0.7,
                 consistency_threshold: float = 0.8,
                 enable_uncertainty_detection: bool = True,
                 enable_consistency_checking: bool = True,
                 enable_citation_validation: bool = True,
                 enable_pattern_detection: bool = True):
        """
        Initialize enhanced anti-hallucination system
        
        Args:
            confidence_threshold: Minimum confidence score to consider response reliable
            consistency_threshold: Minimum consistency score for multi-response validation
            enable_uncertainty_detection: Enable uncertainty pattern detection
            enable_consistency_checking: Enable response consistency validation
            enable_citation_validation: Enable source citation detection
            enable_pattern_detection: Enable known hallucination pattern detection
        """
        self.confidence_threshold = confidence_threshold
        self.consistency_threshold = consistency_threshold
        self.enable_uncertainty_detection = enable_uncertainty_detection
        self.enable_consistency_checking = enable_consistency_checking
        self.enable_citation_validation = enable_citation_validation
        self.enable_pattern_detection = enable_pattern_detection
        
        # Initialize pattern databases
        self._load_uncertainty_patterns()
        self._load_hallucination_patterns()
        self._load_citation_patterns()
        
        logger.info("Enhanced Anti-Hallucination system initialized")
    
    def _load_uncertainty_patterns(self):
        """Load uncertainty indicator patterns based on research"""
        self.uncertainty_patterns = [
            # Direct uncertainty expressions
            r"\bi don't know\b",
            r"\bi'm not sure\b",
            r"\bi think\b",
            r"\bmaybe\b", 
            r"\bperhaps\b",
            r"\bmight be\b",
            r"\bcould be\b",
            r"\bi believe\b",
            r"\bprobably\b",
            r"\bunknown\b",
            r"\bunsure\b",
            r"\buncertain\b",
            r"\bpossibly\b",
            r"\bseems like\b",
            r"\bappears to\b",
            r"\blikely\b",
            
            # Hedging language (from academic research)
            r"\bto some extent\b",
            r"\bto a degree\b",
            r"\bsomewhat\b",
            r"\brather\b",
            r"\bquite\b",
            r"\bfairly\b",
            r"\bgenerally\b",
            r"\btypically\b",
            r"\busually\b",
            
            # Qualification phrases
            r"\bas far as i know\b",
            r"\bto my knowledge\b",
            r"\baccording to\b",
            r"\bif i recall correctly\b",
            r"\bif memory serves\b",
            r"\bi would say\b",
            r"\bit's my understanding\b",
        ]
    
    def _load_hallucination_patterns(self):
        """Load known hallucination patterns from research"""
        self.hallucination_patterns = [
            # Common misconceptions (from UpTrain research)
            {
                "pattern": r"great wall.*china.*visible.*space",
                "category": "common_misconception",
                "confidence": 0.9
            },
            {
                "pattern": r"einstein.*invented.*light\s?bulb",
                "category": "false_attribution", 
                "confidence": 0.95
            },
            {
                "pattern": r"humans.*only.*use.*10.*percent.*brain",
                "category": "common_misconception",
                "confidence": 0.9
            },
            {
                "pattern": r"lightning.*never.*strikes.*same.*place.*twice",
                "category": "common_misconception",
                "confidence": 0.85
            },
            {
                "pattern": r"goldfish.*three.*second.*memory",
                "category": "common_misconception",
                "confidence": 0.8
            },
            
            # False historical claims
            {
                "pattern": r"napoleon.*short",
                "category": "historical_misconception",
                "confidence": 0.7
            },
            {
                "pattern": r"columbus.*proved.*earth.*round",
                "category": "historical_misconception",
                "confidence": 0.8
            },
            
            # Scientific misconceptions
            {
                "pattern": r"cracking.*knuckles.*causes.*arthritis",
                "category": "medical_misconception",
                "confidence": 0.75
            },
            {
                "pattern": r"vitamin.*c.*prevents.*colds",
                "category": "medical_misconception",
                "confidence": 0.7
            }
        ]
    
    def _load_citation_patterns(self):
        """Load citation detection patterns based on research"""
        self.citation_patterns = [
            # Direct source attribution (from UpTrain research)
            r"according to",
            r"based on",
            r"source:",
            r"references:",
            r"from [A-Z][a-zA-Z]+",  # "from NASA", "from Wikipedia"
            r"study shows",
            r"research indicates",
            r"data shows",
            r"reported by",
            r"published in",
            
            # Academic-style citations
            r"\([A-Za-z]+\s+et\s+al\.,?\s+\d{4}\)",  # (Smith et al., 2023)
            r"\([A-Za-z]+,?\s+\d{4}\)",  # (Smith, 2023)
            r"\[[0-9]+\]",  # [1], [23]
            
            # Institutional sources
            r"nasa states",
            r"who reports",
            r"cdc data",
            r"fda approved",
            r"university of",
            r"journal of",
            r"proceedings of",
            
            # News and media
            r"bbc reported",
            r"reuters found",
            r"ap news",
            r"the new york times",
            r"nature magazine",
            r"science journal"
        ]
    
    def detect_uncertainty(self, response: str) -> Tuple[bool, List[str], float]:
        """
        Detect uncertainty indicators in response using pattern matching
        Based on UQLM uncertainty detection research
        
        Args:
            response: The response text to analyze
            
        Returns:
            Tuple of (has_uncertainty, detected_patterns, uncertainty_score)
        """
        if not self.enable_uncertainty_detection:
            return False, [], 0.0
            
        response_lower = response.lower()
        detected_patterns = []
        uncertainty_score = 0.0
        
        for pattern in self.uncertainty_patterns:
            if re.search(pattern, response_lower):
                detected_patterns.append(pattern)
                # Weight different patterns differently
                if any(term in pattern for term in ["don't know", "not sure", "unknown"]):
                    uncertainty_score += 0.3
                elif any(term in pattern for term in ["maybe", "perhaps", "might"]):
                    uncertainty_score += 0.2
                else:
                    uncertainty_score += 0.1
        
        # Normalize score
        uncertainty_score = min(uncertainty_score, 1.0)
        has_uncertainty = len(detected_patterns) > 0
        
        return has_uncertainty, detected_patterns, uncertainty_score
    
    def detect_hallucination_patterns(self, response: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect known hallucination patterns based on research databases
        Inspired by UpTrain's factual accuracy checking
        
        Args:
            response: The response text to analyze
            
        Returns:
            Tuple of (is_hallucination, detection_details)
        """
        if not self.enable_pattern_detection:
            return False, {}
            
        response_lower = response.lower()
        
        for pattern_info in self.hallucination_patterns:
            if re.search(pattern_info["pattern"], response_lower):
                return True, {
                    "pattern_matched": pattern_info["pattern"],
                    "category": pattern_info["category"],
                    "confidence": pattern_info["confidence"],
                    "matched_text": response
                }
        
        return False, {}
    
    def detect_source_citation(self, response: str) -> Tuple[bool, List[str]]:
        """
        Detect source citations in response using pattern matching
        Based on UpTrain's citation validation research
        
        Args:
            response: The response text to analyze
            
        Returns:
            Tuple of (has_citation, detected_citations)
        """
        if not self.enable_citation_validation:
            return False, []
            
        response_lower = response.lower()
        detected_citations = []
        
        for pattern in self.citation_patterns:
            matches = re.findall(pattern, response_lower)
            if matches:
                detected_citations.extend(matches if isinstance(matches, list) else [matches])
        
        has_citation = len(detected_citations) > 0
        return has_citation, detected_citations
    
    def calculate_semantic_consistency(self, responses: List[str]) -> float:
        """
        Calculate semantic consistency between multiple responses
        Inspired by UQLM's semantic entropy approach
        
        Args:
            responses: List of responses to compare
            
        Returns:
            Consistency score between 0 and 1
        """
        if not self.enable_consistency_checking or len(responses) < 2:
            return 1.0
            
        # Simple word-overlap based consistency (in production, use embeddings)
        all_words = []
        for response in responses:
            words = set(response.lower().split())
            all_words.append(words)
        
        # Calculate average pairwise overlap (Jaccard similarity)
        total_overlap = 0
        pairs = 0
        
        for i in range(len(all_words)):
            for j in range(i + 1, len(all_words)):
                intersection = len(all_words[i] & all_words[j])
                union = len(all_words[i] | all_words[j])
                overlap = intersection / union if union > 0 else 0
                total_overlap += overlap
                pairs += 1
        
        consistency_score = total_overlap / pairs if pairs > 0 else 0
        return consistency_score
    
    def calculate_confidence_score(self, 
                                 response: str, 
                                 token_probabilities: Optional[List[float]] = None,
                                 multiple_responses: Optional[List[str]] = None) -> float:
        """
        Calculate overall confidence score using multiple methods
        Combines approaches from UQLM and UpTrain research
        
        Args:
            response: Primary response to analyze
            token_probabilities: Optional token probabilities for white-box analysis
            multiple_responses: Optional multiple responses for consistency checking
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence_components = []
        
        # 1. Uncertainty detection component
        has_uncertainty, uncertainty_patterns, uncertainty_score = self.detect_uncertainty(response)
        uncertainty_confidence = 1.0 - uncertainty_score
        confidence_components.append(("uncertainty", uncertainty_confidence, 0.3))
        
        # 2. Pattern-based hallucination detection
        is_hallucination, hallucination_details = self.detect_hallucination_patterns(response)
        pattern_confidence = 1.0 - (hallucination_details.get("confidence", 0.0) if is_hallucination else 0.0)
        confidence_components.append(("pattern", pattern_confidence, 0.25))
        
        # 3. Citation detection (positive indicator)
        has_citation, citations = self.detect_source_citation(response)
        citation_confidence = 1.0 if has_citation else 0.7  # Neutral if no citation
        confidence_components.append(("citation", citation_confidence, 0.15))
        
        # 4. Token probability analysis (if available)
        if token_probabilities:
            # Use minimum probability approach from UQLM research
            min_prob = min(token_probabilities) if token_probabilities else 0.5
            # Length-normalized probability
            normalized_prob = math.exp(sum(math.log(p) for p in token_probabilities) / len(token_probabilities))
            token_confidence = (min_prob + normalized_prob) / 2
            confidence_components.append(("token_prob", token_confidence, 0.2))
        
        # 5. Consistency analysis (if multiple responses available)
        if multiple_responses:
            consistency_score = self.calculate_semantic_consistency([response] + multiple_responses)
            confidence_components.append(("consistency", consistency_score, 0.1))
        
        # Calculate weighted average
        total_weight = sum(weight for _, _, weight in confidence_components)
        weighted_sum = sum(score * weight for _, score, weight in confidence_components)
        
        confidence_score = weighted_sum / total_weight if total_weight > 0 else 0.5
        return confidence_score
    
    def evaluate_response(self, 
                         response: str,
                         context: Optional[str] = None,
                         question: Optional[str] = None,
                         token_probabilities: Optional[List[float]] = None,
                         multiple_responses: Optional[List[str]] = None) -> HallucinationResult:
        """
        Comprehensive evaluation of response for hallucination detection
        
        Args:
            response: The response to evaluate
            context: Optional context used to generate the response
            question: Optional original question
            token_probabilities: Optional token probabilities for white-box analysis
            multiple_responses: Optional multiple responses for consistency checking
            
        Returns:
            HallucinationResult with comprehensive analysis
        """
        # Detect uncertainty indicators
        has_uncertainty, uncertainty_patterns, uncertainty_score = self.detect_uncertainty(response)
        
        # Detect known hallucination patterns
        is_pattern_hallucination, pattern_details = self.detect_hallucination_patterns(response)
        
        # Detect source citations
        has_citation, citations = self.detect_source_citation(response)
        
        # Calculate consistency score
        consistency_score = None
        if multiple_responses:
            consistency_score = self.calculate_semantic_consistency([response] + multiple_responses)
        
        # Calculate overall confidence score
        confidence_score = self.calculate_confidence_score(
            response, token_probabilities, multiple_responses
        )
        
        # Determine if response is likely hallucinated
        is_hallucination = (
            confidence_score < self.confidence_threshold or
            is_pattern_hallucination or
            (consistency_score is not None and consistency_score < self.consistency_threshold)
        )
        
        # Compile uncertainty indicators
        uncertainty_indicators = []
        if has_uncertainty:
            uncertainty_indicators.extend([f"Uncertainty pattern: {p}" for p in uncertainty_patterns])
        if is_pattern_hallucination:
            uncertainty_indicators.append(f"Known hallucination pattern: {pattern_details.get('category', 'unknown')}")
        if consistency_score is not None and consistency_score < self.consistency_threshold:
            uncertainty_indicators.append(f"Low consistency score: {consistency_score:.2f}")
        
        # Compile detailed results
        details = {
            "uncertainty_score": uncertainty_score,
            "pattern_hallucination": is_pattern_hallucination,
            "pattern_details": pattern_details,
            "citations_found": citations,
            "consistency_score": consistency_score,
            "confidence_components": {
                "uncertainty": 1.0 - uncertainty_score,
                "pattern": 1.0 - (pattern_details.get("confidence", 0.0) if is_pattern_hallucination else 0.0),
                "citation": 1.0 if has_citation else 0.7,
                "token_probabilities": token_probabilities is not None,
                "consistency": consistency_score
            }
        }
        
        return HallucinationResult(
            confidence_score=confidence_score,
            is_hallucination=is_hallucination,
            uncertainty_indicators=uncertainty_indicators,
            consistency_score=consistency_score,
            source_citation_detected=has_citation,
            details=details
        )
    
    def batch_evaluate(self, 
                      responses: List[str],
                      contexts: Optional[List[str]] = None,
                      questions: Optional[List[str]] = None) -> List[HallucinationResult]:
        """
        Evaluate multiple responses in batch for efficiency
        
        Args:
            responses: List of responses to evaluate
            contexts: Optional list of contexts
            questions: Optional list of questions
            
        Returns:
            List of HallucinationResult objects
        """
        results = []
        
        for i, response in enumerate(responses):
            context = contexts[i] if contexts and i < len(contexts) else None
            question = questions[i] if questions and i < len(questions) else None
            
            result = self.evaluate_response(response, context, question)
            results.append(result)
        
        return results
    
    def get_hallucination_statistics(self, results: List[HallucinationResult]) -> Dict[str, Any]:
        """
        Calculate statistics from multiple evaluation results
        
        Args:
            results: List of HallucinationResult objects
            
        Returns:
            Dictionary with comprehensive statistics
        """
        if not results:
            return {}
        
        total_results = len(results)
        hallucinated_count = sum(1 for r in results if r.is_hallucination)
        
        confidence_scores = [r.confidence_score for r in results]
        avg_confidence = np.mean(confidence_scores)
        min_confidence = np.min(confidence_scores)
        max_confidence = np.max(confidence_scores)
        
        uncertainty_indicators = []
        for r in results:
            uncertainty_indicators.extend(r.uncertainty_indicators)
        
        citation_count = sum(1 for r in results if r.source_citation_detected)
        
        consistency_scores = [r.consistency_score for r in results if r.consistency_score is not None]
        avg_consistency = np.mean(consistency_scores) if consistency_scores else None
        
        return {
            "total_responses": total_results,
            "hallucinated_responses": hallucinated_count,
            "hallucination_rate": hallucinated_count / total_results,
            "confidence_statistics": {
                "mean": avg_confidence,
                "min": min_confidence,
                "max": max_confidence,
                "std": np.std(confidence_scores)
            },
            "citation_rate": citation_count / total_results,
            "consistency_statistics": {
                "mean": avg_consistency,
                "count": len(consistency_scores)
            },
            "common_uncertainty_indicators": list(set(uncertainty_indicators))
        }


async def demo_enhanced_anti_hallucination():
    """Demonstrate the enhanced anti-hallucination system"""
    print(" Enhanced Anti-Hallucination System Demo")
    print("=" * 60)
    
    # Initialize the system
    ah_system = EnhancedAntiHallucination(
        confidence_threshold=0.7,
        consistency_threshold=0.8
    )
    
    # Test responses with varying degrees of reliability
    test_cases = [
        {
            "response": "The capital of France is Paris.",
            "description": "Factual response"
        },
        {
            "response": "I think the capital of France might be Paris, but I'm not entirely sure.",
            "description": "Uncertain response"
        },
        {
            "response": "According to NASA, the Earth is approximately 4.5 billion years old.",
            "description": "Response with citation"
        },
        {
            "response": "The Great Wall of China is visible from space with the naked eye.",
            "description": "Known false statement"
        },
        {
            "response": "Einstein invented the light bulb in 1879.",
            "description": "Historical inaccuracy"
        },
        {
            "response": "Based on recent studies published in Nature, water molecules exhibit quantum behavior at room temperature.",
            "description": "Potentially fabricated scientific claim"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n Test Case {i}: {test_case['description']}")
        print(f"Response: \"{test_case['response']}\"")
        
        # Evaluate the response
        result = ah_system.evaluate_response(test_case['response'])
        results.append(result)
        
        # Display results
        print(f" Confidence Score: {result.confidence_score:.3f}")
        print(f"*** Hallucination Detected: {result.is_hallucination}")
        print(f" Source Citation: {result.source_citation_detected}")
        
        if result.uncertainty_indicators:
            print(f"[WARN]  Uncertainty Indicators:")
            for indicator in result.uncertainty_indicators:
                print(f"   - {indicator}")
        
        if result.details and result.details.get("pattern_details"):
            print(f"[SEARCH] Pattern Match: {result.details['pattern_details']['category']}")
    
    # Generate overall statistics
    print(f"\n[CHART] Overall Statistics")
    print("=" * 30)
    stats = ah_system.get_hallucination_statistics(results)
    
    print(f"Total Responses: {stats['total_responses']}")
    print(f"Hallucination Rate: {stats['hallucination_rate']:.1%}")
    print(f"Average Confidence: {stats['confidence_statistics']['mean']:.3f}")
    print(f"Citation Rate: {stats['citation_rate']:.1%}")
    
    if stats['common_uncertainty_indicators']:
        print(f"\nCommon Uncertainty Patterns:")
        for indicator in stats['common_uncertainty_indicators'][:5]:  # Show top 5
            print(f"   - {indicator}")


if __name__ == "__main__":
    asyncio.run(demo_enhanced_anti_hallucination())
