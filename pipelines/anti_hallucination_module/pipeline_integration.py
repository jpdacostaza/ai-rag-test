"""
Production Anti-Hallucination Integration
=========================================

This module integrates research-based anti-hallucination techniques into the existing
OpenWebUI memory pipeline system. It combines approaches from:

1. UpTrain AI (https://github.com/uptrain-ai/uptrain):
   - Factual accuracy evaluation
   - Prompt injection detection
   - Response consistency checking

2. CVS Health UQLM (https://github.com/cvs-health/uqlm):
   - Uncertainty quantification
   - Semantic entropy analysis
   - Black-box and white-box scoring

3. Academic Research:
   - Multi-response consistency validation
   - Citation-based verification
   - Pattern-based hallucination detection

Integration Points:
- Memory retrieval validation
- Response generation filtering
- Context grounding verification
- Real-time hallucination detection
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    from .enhanced_anti_hallucination import EnhancedAntiHallucination, HallucinationResult
except ImportError:
    from enhanced_anti_hallucination import EnhancedAntiHallucination, HallucinationResult

# Configure logging
try:
    from core.unified_logging import setup_logging, get_logger
    setup_logging()
    logger = get_logger(__name__)
except ImportError:
    # Fallback for standalone usage
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

@dataclass
class PipelineHallucinationConfig:
    """Configuration for anti-hallucination pipeline integration"""
    confidence_threshold: float = 0.7
    consistency_threshold: float = 0.8
    enable_real_time_filtering: bool = True
    enable_memory_validation: bool = True
    enable_response_scoring: bool = True
    enable_context_grounding: bool = True
    max_validation_time_ms: int = 500
    fallback_on_timeout: bool = True
    log_detections: bool = True

class AntiHallucinationPipeline:
    """Production anti-hallucination pipeline for OpenWebUI integration"""
    
    def __init__(self, config: Optional[PipelineHallucinationConfig] = None):
        """
        Initialize the anti-hallucination pipeline
        
        Args:
            config: Configuration object for the pipeline
        """
        self.config = config or PipelineHallucinationConfig()
        self.ah_system = EnhancedAntiHallucination(
            confidence_threshold=self.config.confidence_threshold,
            consistency_threshold=self.config.consistency_threshold
        )
        
        # Performance tracking
        self.stats = {
            "total_evaluations": 0,
            "hallucinations_detected": 0,
            "responses_filtered": 0,
            "average_processing_time_ms": 0,
            "timeouts": 0
        }
        
        logger.info("Anti-Hallucination Pipeline initialized")
    
    async def validate_memory_retrieval(self, 
                                      query: str, 
                                      retrieved_memories: List[Dict[str, Any]]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate retrieved memories for relevance and potential hallucination sources
        
        Args:
            query: The original user query
            retrieved_memories: List of retrieved memory objects
            
        Returns:
            Tuple of (is_valid, filtered_memories)
        """
        if not self.config.enable_memory_validation:
            return True, retrieved_memories
        
        start_time = time.time()
        
        try:
            # Extract memory content for evaluation
            memory_contents = []
            for memory in retrieved_memories:
                content = memory.get('content', '')
                if content:
                    memory_contents.append(content)
            
            if not memory_contents:
                return True, retrieved_memories
            
            # Evaluate each memory for potential hallucination patterns
            filtered_memories = []
            for i, memory in enumerate(retrieved_memories):
                if i < len(memory_contents):
                    result = self.ah_system.evaluate_response(memory_contents[i])
                    
                    # Include memory if confidence is above threshold
                    if result.confidence_score >= self.config.confidence_threshold:
                        filtered_memories.append(memory)
                    elif self.config.log_detections:
                        logger.warning(f"Memory filtered due to low confidence: {result.confidence_score:.3f}")
                else:
                    filtered_memories.append(memory)
            
            processing_time = (time.time() - start_time) * 1000
            if processing_time > self.config.max_validation_time_ms:
                logger.warning(f"Memory validation timeout: {processing_time:.1f}ms")
                if self.config.fallback_on_timeout:
                    return True, retrieved_memories
            
            return len(filtered_memories) > 0, filtered_memories
            
        except Exception as e:
            logger.error(f"Error in memory validation: {e}")
            return True, retrieved_memories  # Fallback to original memories on error
    
    async def validate_response_generation(self, 
                                         prompt: str,
                                         response: str,
                                         context: Optional[str] = None) -> HallucinationResult:
        """
        Validate generated response for hallucinations
        
        Args:
            prompt: The input prompt/query
            response: The generated response
            context: Optional context used for generation
            
        Returns:
            HallucinationResult with validation details
        """
        start_time = time.time()
        
        try:
            # Evaluate the response
            result = self.ah_system.evaluate_response(
                response=response,
                context=context,
                question=prompt
            )
            
            # Update statistics
            self.stats["total_evaluations"] += 1
            if result.is_hallucination:
                self.stats["hallucinations_detected"] += 1
            
            processing_time = (time.time() - start_time) * 1000
            self.stats["average_processing_time_ms"] = (
                (self.stats["average_processing_time_ms"] * (self.stats["total_evaluations"] - 1) + processing_time) 
                / self.stats["total_evaluations"]
            )
            
            if processing_time > self.config.max_validation_time_ms:
                self.stats["timeouts"] += 1
                logger.warning(f"Response validation timeout: {processing_time:.1f}ms")
            
            if self.config.log_detections and result.is_hallucination:
                logger.warning(f"Hallucination detected - Confidence: {result.confidence_score:.3f}, "
                             f"Indicators: {', '.join(result.uncertainty_indicators)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in response validation: {e}")
            # Return safe default result
            return HallucinationResult(
                confidence_score=0.5,
                is_hallucination=True,
                uncertainty_indicators=[f"Validation error: {str(e)}"]
            )
    
    async def filter_response_if_needed(self, 
                                      result: HallucinationResult,
                                      original_response: str,
                                      fallback_response: Optional[str] = None) -> str:
        """
        Filter response based on hallucination detection results
        
        Args:
            result: HallucinationResult from validation
            original_response: The original generated response
            fallback_response: Optional fallback response to use
            
        Returns:
            Final response (original, fallback, or generated safety message)
        """
        if not self.config.enable_real_time_filtering:
            return original_response
        
        if not result.is_hallucination:
            return original_response
        
        # Response was flagged as hallucination
        self.stats["responses_filtered"] += 1
        
        if fallback_response:
            logger.info("Using fallback response due to hallucination detection")
            return fallback_response
        
        # Generate safety message
        safety_message = self._generate_safety_message(result)
        logger.info("Generated safety message due to hallucination detection")
        return safety_message
    
    def _generate_safety_message(self, result: HallucinationResult) -> str:
        """
        Generate appropriate safety message based on detection results
        
        Args:
            result: HallucinationResult with detection details
            
        Returns:
            Safety message string
        """
        base_message = "I'm not entirely confident in my response. "
        
        if result.uncertainty_indicators:
            # Analyze the type of uncertainty detected
            if any("uncertainty pattern" in indicator.lower() for indicator in result.uncertainty_indicators):
                base_message += "I detected uncertainty markers in my response. "
            
            if any("known hallucination" in indicator.lower() for indicator in result.uncertainty_indicators):
                base_message += "This response contains patterns associated with common misconceptions. "
            
            if any("consistency" in indicator.lower() for indicator in result.uncertainty_indicators):
                base_message += "There may be inconsistencies in the information. "
        
        base_message += "Please verify this information from reliable sources, or I can try to search for more current information."
        
        return base_message
    
    async def validate_context_grounding(self, 
                                       response: str,
                                       context_chunks: List[str]) -> Tuple[float, List[str]]:
        """
        Validate how well the response is grounded in the provided context
        
        Args:
            response: The generated response
            context_chunks: List of context chunks used for generation
            
        Returns:
            Tuple of (grounding_score, unsupported_claims)
        """
        if not self.config.enable_context_grounding or not context_chunks:
            return 1.0, []
        
        try:
            # Simple approach: check if response content appears in context
            response_lower = response.lower()
            context_combined = " ".join(context_chunks).lower()
            
            # Split response into sentences for individual checking
            sentences = [s.strip() for s in response.split('.') if s.strip()]
            unsupported_claims = []
            supported_count = 0
            
            for sentence in sentences:
                # Simple keyword overlap check (in production, use semantic similarity)
                words = set(sentence.lower().split())
                context_words = set(context_combined.split())
                
                # Calculate overlap ratio
                overlap = len(words & context_words) / len(words) if words else 0
                
                if overlap < 0.3:  # Less than 30% overlap
                    unsupported_claims.append(sentence)
                else:
                    supported_count += 1
            
            grounding_score = supported_count / len(sentences) if sentences else 1.0
            
            return grounding_score, unsupported_claims
            
        except Exception as e:
            logger.error(f"Error in context grounding validation: {e}")
            return 0.5, []
    
    async def comprehensive_pipeline_validation(self, 
                                              query: str,
                                              retrieved_memories: List[Dict[str, Any]],
                                              generated_response: str,
                                              context_chunks: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run comprehensive validation through the entire pipeline
        
        Args:
            query: Original user query
            retrieved_memories: Retrieved memory objects
            generated_response: Generated response
            context_chunks: Optional context chunks used
            
        Returns:
            Comprehensive validation results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "validation_results": {}
        }
        
        try:
            # 1. Validate memory retrieval
            if self.config.enable_memory_validation:
                memory_valid, filtered_memories = await self.validate_memory_retrieval(query, retrieved_memories)
                results["validation_results"]["memory_validation"] = {
                    "is_valid": memory_valid,
                    "original_count": len(retrieved_memories),
                    "filtered_count": len(filtered_memories),
                    "memories_removed": len(retrieved_memories) - len(filtered_memories)
                }
            
            # 2. Validate response generation
            if self.config.enable_response_scoring:
                response_result = await self.validate_response_generation(query, generated_response)
                results["validation_results"]["response_validation"] = {
                    "confidence_score": response_result.confidence_score,
                    "is_hallucination": response_result.is_hallucination,
                    "uncertainty_indicators": response_result.uncertainty_indicators,
                    "source_citation_detected": response_result.source_citation_detected,
                    "details": response_result.details
                }
            
            # 3. Validate context grounding
            if self.config.enable_context_grounding and context_chunks:
                grounding_score, unsupported_claims = await self.validate_context_grounding(generated_response, context_chunks)
                results["validation_results"]["context_grounding"] = {
                    "grounding_score": grounding_score,
                    "unsupported_claims": unsupported_claims,
                    "claims_count": len(unsupported_claims)
                }
            
            # 4. Overall assessment
            overall_confidence = self._calculate_overall_confidence(results["validation_results"])
            results["overall_assessment"] = {
                "confidence_score": overall_confidence,
                "recommendation": self._get_recommendation(overall_confidence),
                "should_filter": overall_confidence < self.config.confidence_threshold
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive validation: {e}")
            results["error"] = str(e)
        
        return results
    
    def _calculate_overall_confidence(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall confidence from validation results"""
        confidence_components = []
        
        # Response validation confidence
        if "response_validation" in validation_results:
            confidence_components.append(validation_results["response_validation"]["confidence_score"])
        
        # Context grounding confidence
        if "context_grounding" in validation_results:
            confidence_components.append(validation_results["context_grounding"]["grounding_score"])
        
        # Memory validation confidence (binary to score)
        if "memory_validation" in validation_results:
            memory_confidence = 1.0 if validation_results["memory_validation"]["is_valid"] else 0.3
            confidence_components.append(memory_confidence)
        
        if confidence_components:
            return sum(confidence_components) / len(confidence_components)
        else:
            return 0.5  # Default neutral confidence
    
    def _get_recommendation(self, confidence_score: float) -> str:
        """Get recommendation based on confidence score"""
        if confidence_score >= 0.9:
            return "High confidence - response appears reliable"
        elif confidence_score >= 0.7:
            return "Medium confidence - response is likely accurate"
        elif confidence_score >= 0.5:
            return "Low confidence - verify information from additional sources"
        else:
            return "Very low confidence - response may contain inaccuracies"
    
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Get comprehensive pipeline statistics"""
        return {
            "performance_stats": self.stats.copy(),
            "configuration": asdict(self.config),
            "hallucination_rate": (
                self.stats["hallucinations_detected"] / self.stats["total_evaluations"] 
                if self.stats["total_evaluations"] > 0 else 0
            ),
            "filter_rate": (
                self.stats["responses_filtered"] / self.stats["total_evaluations"]
                if self.stats["total_evaluations"] > 0 else 0
            ),
            "timeout_rate": (
                self.stats["timeouts"] / self.stats["total_evaluations"]
                if self.stats["total_evaluations"] > 0 else 0
            )
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the anti-hallucination system"""
        start_time = time.time()
        
        try:
            # Test basic functionality
            test_response = "The capital of France is Paris."
            result = await self.validate_response_generation("What is the capital of France?", test_response)
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "processing_time_ms": processing_time,
                "test_confidence": result.confidence_score,
                "components": {
                    "enhanced_ah_system": True,
                    "memory_validation": self.config.enable_memory_validation,
                    "response_scoring": self.config.enable_response_scoring,
                    "context_grounding": self.config.enable_context_grounding,
                    "real_time_filtering": self.config.enable_real_time_filtering
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "components": {
                    "enhanced_ah_system": False
                }
            }


async def demo_pipeline_integration():
    """Demonstrate the integrated anti-hallucination pipeline"""
    print(" Anti-Hallucination Pipeline Integration Demo")
    print("=" * 60)
    
    # Initialize pipeline
    config = PipelineHallucinationConfig(
        confidence_threshold=0.7,
        enable_real_time_filtering=True,
        log_detections=True
    )
    
    pipeline = AntiHallucinationPipeline(config)
    
    # Simulate pipeline usage
    test_scenarios = [
        {
            "query": "What is the capital of France?",
            "memories": [
                {"content": "France is a country in Europe", "id": "mem_1"},
                {"content": "Paris is the capital city of France", "id": "mem_2"}
            ],
            "response": "The capital of France is Paris.",
            "context": ["France is a European country.", "Paris is the capital."]
        },
        {
            "query": "Tell me about the Great Wall of China",
            "memories": [
                {"content": "The Great Wall of China is an ancient fortification", "id": "mem_3"}
            ],
            "response": "The Great Wall of China is visible from space with the naked eye.",
            "context": ["The Great Wall is an ancient Chinese fortification."]
        },
        {
            "query": "Who invented the light bulb?",
            "memories": [
                {"content": "Thomas Edison was an American inventor", "id": "mem_4"}
            ],
            "response": "Einstein invented the light bulb in 1879.",
            "context": ["Thomas Edison was known for his inventions."]
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n Scenario {i}: {scenario['query']}")
        print("-" * 40)
        
        # Run comprehensive validation
        results = await pipeline.comprehensive_pipeline_validation(
            query=scenario["query"],
            retrieved_memories=scenario["memories"],
            generated_response=scenario["response"],
            context_chunks=scenario["context"]
        )
        
        # Display results
        print(f"Query: {scenario['query']}")
        print(f"Response: {scenario['response']}")
        
        if "response_validation" in results["validation_results"]:
            rv = results["validation_results"]["response_validation"]
            print(f" Confidence: {rv['confidence_score']:.3f}")
            print(f"*** Hallucination: {rv['is_hallucination']}")
            
            if rv["uncertainty_indicators"]:
                print(f"[WARN]  Indicators: {', '.join(rv['uncertainty_indicators'])}")
        
        if "context_grounding" in results["validation_results"]:
            cg = results["validation_results"]["context_grounding"]
            print(f" Grounding Score: {cg['grounding_score']:.3f}")
            
            if cg["unsupported_claims"]:
                print(f" Unsupported Claims: {len(cg['unsupported_claims'])}")
        
        print(f"[CHART] Overall Confidence: {results['overall_assessment']['confidence_score']:.3f}")
        print(f" Recommendation: {results['overall_assessment']['recommendation']}")
        
        if results["overall_assessment"]["should_filter"]:
            print("  Response would be filtered/flagged")
    
    # Show pipeline statistics
    print(f"\n Pipeline Statistics")
    print("=" * 30)
    stats = pipeline.get_pipeline_statistics()
    
    print(f"Total Evaluations: {stats['performance_stats']['total_evaluations']}")
    print(f"Hallucinations Detected: {stats['performance_stats']['hallucinations_detected']}")
    print(f"Hallucination Rate: {stats['hallucination_rate']:.1%}")
    print(f"Average Processing Time: {stats['performance_stats']['average_processing_time_ms']:.1f}ms")
    
    # Health check
    print(f"\n Health Check")
    print("=" * 20)
    health = await pipeline.health_check()
    print(f"Status: {health['status']}")
    print(f"Processing Time: {health.get('processing_time_ms', 0):.1f}ms")


if __name__ == "__main__":
    asyncio.run(demo_pipeline_integration())
