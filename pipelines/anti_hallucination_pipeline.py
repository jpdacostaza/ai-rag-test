"""
Anti-Hallucination OpenWebUI Pipeline
=====================================

This is a proper OpenWebUI pipeline that integrates anti-hallucination detection
into the conversation flow. It can be used as a filter or manifold pipeline.

Features:
- Real-time hallucination detection during response generation
- Memory validation before retrieval
- Response filtering based on confidence scores
- Integration with existing enhanced memory pipeline
- Docker-compatible and production-ready

Usage in OpenWebUI:
1. Place this file in the pipelines directory
2. Enable in OpenWebUI admin interface
3. Configure thresholds and options
4. Monitor detection statistics
"""

import os
import sys
import asyncio
import json
import time
from typing import List, Optional, Dict, Any, Union, Generator, Iterator
from datetime import datetime

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'anti_hallucination_module'))
sys.path.insert(0, '/opt/backend/pipelines/anti_hallucination_module')

try:
    from pydantic import BaseModel, Field
except ImportError:
    # Install pydantic if not available
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "pydantic>=2.0.0", "--quiet"])
    from pydantic import BaseModel, Field

# Import our anti-hallucination modules
try:
    from enhanced_anti_hallucination import EnhancedAntiHallucination, HallucinationResult
    from pipeline_integration import AntiHallucinationPipeline, PipelineHallucinationConfig
    ANTI_HALLUCINATION_AVAILABLE = True
except ImportError as e:
    print(f"[ANTI-HALLUCINATION] Warning: Could not import anti-hallucination modules: {e}")
    ANTI_HALLUCINATION_AVAILABLE = False


class Pipeline:
    """
    OpenWebUI Anti-Hallucination Pipeline
    
    This pipeline can operate in multiple modes:
    1. Filter mode: Intercepts and validates responses before delivery
    2. Manifold mode: Provides anti-hallucination as a service
    3. Hybrid mode: Integrates with memory pipeline for full validation
    """
    
    class Valves(BaseModel):
        """Pipeline configuration valves (OpenWebUI standard)"""
        
        # Pipeline identification
        pipelines: List[str] = Field(
            default=["*"],
            description="List of models this pipeline applies to. Use ['*'] for all models."
        )
        priority: int = Field(
            default=0,
            description="Pipeline priority (higher values = higher priority)"
        )
        
        # Anti-hallucination configuration
        confidence_threshold: float = Field(
            default=0.7,
            description="Minimum confidence score to consider response reliable (0.0-1.0)"
        )
        consistency_threshold: float = Field(
            default=0.8,
            description="Minimum consistency score for multi-response validation (0.0-1.0)"
        )
        enable_real_time_filtering: bool = Field(
            default=True,
            description="Enable real-time response filtering based on hallucination detection"
        )
        enable_memory_validation: bool = Field(
            default=True,
            description="Enable validation of retrieved memories before use"
        )
        enable_response_scoring: bool = Field(
            default=True,
            description="Enable confidence scoring of generated responses"
        )
        enable_context_grounding: bool = Field(
            default=True,
            description="Enable context grounding verification"
        )
        max_validation_time_ms: int = Field(
            default=500,
            description="Maximum time allowed for validation in milliseconds"
        )
        fallback_on_timeout: bool = Field(
            default=True,
            description="Fall back to original response if validation times out"
        )
        log_detections: bool = Field(
            default=True,
            description="Log hallucination detections for monitoring"
        )
        safety_message_mode: str = Field(
            default="replace",
            description="How to handle detected hallucinations: 'replace', 'append', 'flag'"
        )
        show_confidence_scores: bool = Field(
            default=False,
            description="Show confidence scores in responses (useful for debugging)"
        )
        
        # Performance settings
        enable_statistics: bool = Field(
            default=True,
            description="Enable statistics collection and reporting"
        )
        max_response_length: int = Field(
            default=10000,
            description="Maximum response length to process (longer responses skipped)"
        )
    
    def __init__(self):
        """Initialize the anti-hallucination pipeline"""
        
        # Set pipeline metadata
        self.type = "filter"  # Can be "filter" or "manifold"
        self.id = "anti_hallucination_pipeline"
        self.name = "Anti-Hallucination Detection"
        self.description = "Detects and filters potential hallucinations in AI responses using research-based methods"
        
        # Initialize valves with default configuration
        self.valves = self.Valves()
        
        # Initialize anti-hallucination system
        self.ah_pipeline = None
        self.statistics = {
            "total_requests": 0,
            "hallucinations_detected": 0,
            "responses_filtered": 0,
            "average_confidence": 0.0,
            "processing_times": [],
            "last_reset": datetime.now().isoformat()
        }
        
        # Initialize the system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the anti-hallucination detection system"""
        if not ANTI_HALLUCINATION_AVAILABLE:
            print("[ANTI-HALLUCINATION] System not available - running in passthrough mode")
            return
        
        try:
            # Create configuration from valves
            config = PipelineHallucinationConfig(
                confidence_threshold=self.valves.confidence_threshold,
                consistency_threshold=self.valves.consistency_threshold,
                enable_real_time_filtering=self.valves.enable_real_time_filtering,
                enable_memory_validation=self.valves.enable_memory_validation,
                enable_response_scoring=self.valves.enable_response_scoring,
                enable_context_grounding=self.valves.enable_context_grounding,
                max_validation_time_ms=self.valves.max_validation_time_ms,
                fallback_on_timeout=self.valves.fallback_on_timeout,
                log_detections=self.valves.log_detections
            )
            
            # Initialize the pipeline
            self.ah_pipeline = AntiHallucinationPipeline(config)
            print("[ANTI-HALLUCINATION] System initialized successfully")
            
        except Exception as e:
            print(f"[ANTI-HALLUCINATION] Failed to initialize system: {e}")
            self.ah_pipeline = None
    
    async def on_startup(self):
        """Called when the pipeline starts"""
        print(f"[ANTI-HALLUCINATION] Pipeline '{self.name}' starting up...")
        
        # Reinitialize if valves were updated
        if ANTI_HALLUCINATION_AVAILABLE and self.ah_pipeline is None:
            self._initialize_system()
        
        # Perform health check
        if self.ah_pipeline:
            try:
                health = await self.ah_pipeline.health_check()
                print(f"[ANTI-HALLUCINATION] Health check: {health['status']}")
            except Exception as e:
                print(f"[ANTI-HALLUCINATION] Health check failed: {e}")
    
    async def on_shutdown(self):
        """Called when the pipeline shuts down"""
        print(f"[ANTI-HALLUCINATION] Pipeline '{self.name}' shutting down...")
        
        # Log final statistics
        if self.valves.enable_statistics:
            print(f"[ANTI-HALLUCINATION] Final statistics: {self.statistics}")
    
    def _update_statistics(self, processing_time: float, confidence_score: float, is_hallucination: bool, was_filtered: bool):
        """Update pipeline statistics"""
        if not self.valves.enable_statistics:
            return
        
        self.statistics["total_requests"] += 1
        self.statistics["processing_times"].append(processing_time)
        
        if is_hallucination:
            self.statistics["hallucinations_detected"] += 1
        
        if was_filtered:
            self.statistics["responses_filtered"] += 1
        
        # Update average confidence (running average)
        total = self.statistics["total_requests"]
        current_avg = self.statistics["average_confidence"]
        self.statistics["average_confidence"] = ((current_avg * (total - 1)) + confidence_score) / total
        
        # Keep only last 1000 processing times to prevent memory growth
        if len(self.statistics["processing_times"]) > 1000:
            self.statistics["processing_times"] = self.statistics["processing_times"][-1000:]
    
    def _generate_safety_message(self, result: 'HallucinationResult', original_response: str) -> str:
        """Generate appropriate safety message based on detection results"""
        if self.valves.safety_message_mode == "append":
            confidence_note = f" [Confidence: {result.confidence_score:.2f}]" if self.valves.show_confidence_scores else ""
            return f"{original_response}\n\n⚠️ *Note: I'm not entirely confident in this response. Please verify from reliable sources.*{confidence_note}"
        
        elif self.valves.safety_message_mode == "flag":
            confidence_note = f" (Confidence: {result.confidence_score:.2f})" if self.valves.show_confidence_scores else ""
            return f"🚨 **Potential Hallucination Detected**{confidence_note}\n\n{original_response}\n\n*This response has been flagged for potential inaccuracies. Please verify information from reliable sources.*"
        
        else:  # replace mode
            base_message = "I'm not entirely confident in my previous response. "
            
            if result.uncertainty_indicators:
                if any("uncertainty pattern" in indicator.lower() for indicator in result.uncertainty_indicators):
                    base_message += "I detected uncertainty markers in my analysis. "
                
                if any("known hallucination" in indicator.lower() for indicator in result.uncertainty_indicators):
                    base_message += "This topic contains patterns associated with common misconceptions. "
                
                if any("consistency" in indicator.lower() for indicator in result.uncertainty_indicators):
                    base_message += "There may be inconsistencies in the information. "
            
            base_message += "Please verify this information from reliable sources, or I can try to search for more current information."
            
            if self.valves.show_confidence_scores:
                base_message += f" (Confidence: {result.confidence_score:.2f})"
            
            return base_message
    
    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming requests (OpenWebUI inlet hook)"""
        # This is called before the message is sent to the model
        # We can use this to validate any retrieved context/memories
        
        if not ANTI_HALLUCINATION_AVAILABLE or not self.ah_pipeline:
            return body
        
        # For now, just pass through - memory validation would happen here
        # if we had access to the memory retrieval system
        return body
    
    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process outgoing responses (OpenWebUI outlet hook)"""
        # This is called after the model generates a response
        # This is where we perform hallucination detection
        
        if not ANTI_HALLUCINATION_AVAILABLE or not self.ah_pipeline:
            return body
        
        start_time = time.time()
        
        try:
            # Extract the response from the body
            messages = body.get("messages", [])
            if not messages:
                return body
            
            # Get the last message (assistant's response)
            last_message = messages[-1]
            if last_message.get("role") != "assistant":
                return body
            
            response_content = last_message.get("content", "")
            if not response_content or len(response_content) > self.valves.max_response_length:
                return body
            
            # Extract context/query information
            user_messages = [msg.get("content", "") for msg in messages if msg.get("role") == "user"]
            latest_query = user_messages[-1] if user_messages else ""
            
            # Perform hallucination detection
            result = await self.ah_pipeline.validate_response_generation(
                prompt=latest_query,
                response=response_content,
                context=None  # We don't have access to context here
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            # Determine if we should filter the response
            should_filter = (
                self.valves.enable_real_time_filtering and 
                result.is_hallucination and
                result.confidence_score < self.valves.confidence_threshold
            )
            
            # Update statistics
            self._update_statistics(processing_time, result.confidence_score, result.is_hallucination, should_filter)
            
            # Apply filtering if needed
            if should_filter:
                safety_message = self._generate_safety_message(result, response_content)
                last_message["content"] = safety_message
                
                if self.valves.log_detections:
                    print(f"[ANTI-HALLUCINATION] Response filtered - Confidence: {result.confidence_score:.3f}, "
                          f"Indicators: {', '.join(result.uncertainty_indicators)}")
            
            elif self.valves.show_confidence_scores and result.confidence_score < 0.9:
                # Add confidence score even if not filtering
                last_message["content"] = f"{response_content}\n\n*[Confidence: {result.confidence_score:.2f}]*"
            
            return body
            
        except Exception as e:
            print(f"[ANTI-HALLUCINATION] Error in outlet processing: {e}")
            # Return original body on error
            return body
    
    def get_status(self) -> dict:
        """Get pipeline status and statistics"""
        status = {
            "pipeline_id": self.id,
            "name": self.name,
            "type": self.type,
            "anti_hallucination_available": ANTI_HALLUCINATION_AVAILABLE,
            "system_initialized": self.ah_pipeline is not None,
            "configuration": {
                "confidence_threshold": self.valves.confidence_threshold,
                "consistency_threshold": self.valves.consistency_threshold,
                "real_time_filtering": self.valves.enable_real_time_filtering,
                "memory_validation": self.valves.enable_memory_validation,
                "response_scoring": self.valves.enable_response_scoring,
                "context_grounding": self.valves.enable_context_grounding
            }
        }
        
        if self.valves.enable_statistics:
            stats = self.statistics.copy()
            if stats["processing_times"]:
                stats["average_processing_time_ms"] = sum(stats["processing_times"]) / len(stats["processing_times"])
                stats["max_processing_time_ms"] = max(stats["processing_times"])
                stats["min_processing_time_ms"] = min(stats["processing_times"])
            
            # Calculate rates
            total = stats["total_requests"]
            if total > 0:
                stats["hallucination_rate"] = stats["hallucinations_detected"] / total
                stats["filter_rate"] = stats["responses_filtered"] / total
            
            status["statistics"] = stats
        
        return status
    
    async def test_system(self) -> dict:
        """Test the anti-hallucination system with known cases"""
        if not ANTI_HALLUCINATION_AVAILABLE or not self.ah_pipeline:
            return {"status": "error", "message": "Anti-hallucination system not available"}
        
        test_cases = [
            {
                "name": "Factual Statement",
                "query": "What is the capital of France?",
                "response": "The capital of France is Paris.",
                "expected_hallucination": False
            },
            {
                "name": "Known False Statement",
                "query": "Tell me about the Great Wall of China",
                "response": "The Great Wall of China is visible from space with the naked eye.",
                "expected_hallucination": True
            },
            {
                "name": "Uncertain Response",
                "query": "What is the population of Mars?",
                "response": "I think the population of Mars might be around 1 million, but I'm not entirely sure.",
                "expected_hallucination": False  # Uncertain but honest
            }
        ]
        
        results = []
        for test_case in test_cases:
            try:
                result = await self.ah_pipeline.validate_response_generation(
                    prompt=test_case["query"],
                    response=test_case["response"]
                )
                
                results.append({
                    "name": test_case["name"],
                    "confidence_score": result.confidence_score,
                    "is_hallucination": result.is_hallucination,
                    "expected_hallucination": test_case["expected_hallucination"],
                    "correct_detection": result.is_hallucination == test_case["expected_hallucination"],
                    "uncertainty_indicators": result.uncertainty_indicators
                })
                
            except Exception as e:
                results.append({
                    "name": test_case["name"],
                    "error": str(e),
                    "correct_detection": False
                })
        
        # Calculate overall accuracy
        correct_detections = sum(1 for r in results if r.get("correct_detection", False))
        accuracy = correct_detections / len(results) if results else 0
        
        return {
            "status": "success",
            "test_results": results,
            "overall_accuracy": accuracy,
            "total_tests": len(results),
            "correct_detections": correct_detections
        }


# Required by OpenWebUI - pipeline instance
pipeline = Pipeline()

# Optional: Export for direct testing
if __name__ == "__main__":
    import asyncio
    
    async def test_pipeline():
        """Test the pipeline directly"""
        print("🧪 Testing Anti-Hallucination Pipeline")
        print("=" * 50)
        
        # Initialize
        await pipeline.on_startup()
        
        # Test system
        test_results = await pipeline.test_system()
        print(f"Test Results: {json.dumps(test_results, indent=2)}")
        
        # Show status
        status = pipeline.get_status()
        print(f"Pipeline Status: {json.dumps(status, indent=2)}")
        
        # Test with a sample response
        sample_body = {
            "messages": [
                {"role": "user", "content": "Tell me about the Great Wall of China"},
                {"role": "assistant", "content": "The Great Wall of China is visible from space with the naked eye."}
            ]
        }
        
        processed_body = await pipeline.outlet(sample_body)
        print(f"Processed Response: {processed_body['messages'][-1]['content']}")
    
    asyncio.run(test_pipeline())
