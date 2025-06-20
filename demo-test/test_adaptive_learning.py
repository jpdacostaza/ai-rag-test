#!/usr/bin/env python3
import asyncio
import json
import os
import sys
import traceback
from datetime import datetime

from adaptive_learning import AdaptiveLearningSystem
from adaptive_learning import ConversationAnalyzer
from adaptive_learning import FeedbackType
from adaptive_learning import adaptive_learning_system

"""

Adaptive Learning System Test Suite
===================================

Comprehensive tests for the adaptive learning functionality including:
- Interaction analysis
- Pattern learning
- User insights
- Knowledge expansion
- Error handling
"""


# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:

    print("✅ Successfully imported adaptive learning modules")
except ImportError:
    print("❌ Import error: {e}")
    sys.exit(1)


class AdaptiveLearningTester:
    """Test suite for adaptive learning system."""

    def __init__(self):
        self.test_results = []
        self.test_user_id = "test_adaptive_user"
        self.test_conversation_id = "test_conv_001"

    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log a test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.test_results.append(result)
        print("{status}: {test_name}")
        if details:
            print("   Details: {details}")
        print()

    async def test_conversation_analyzer(self):
        """Test the conversation analyzer functionality."""
        print("🧪 Testing ConversationAnalyzer...")

        analyzer = ConversationAnalyzer()

        # Test 1: Feedback classification
        test_cases = [
            ("That was perfect, thank you!", FeedbackType.POSITIVE),
            ("That's wrong, it should be different", FeedbackType.CORRECTION),
            ("I don't understand, can you explain that more?", FeedbackType.CLARIFICATION),
            ("That was unhelpful and terrible", FeedbackType.NEGATIVE),  # Updated test case
            ("Hello there", FeedbackType.NEUTRAL),
        ]

        for message, expected_type in test_cases:
            actual_type = analyzer._classify_feedback(message)
            if actual_type != expected_type:
                self.log_test_result(
                    "Feedback Classification: '{message[:30]}...'",
                    False,
                    "Expected {expected_type}, got {actual_type}",
                )
            else:
                self.log_test_result("Feedback Classification: '{message[:30]}...'", True)

        # Test 2: Topic extraction
        test_text = "I need help with Python programming and machine learning algorithms"
        topics = await analyzer._extract_topics(test_text)

        expected_topics = ["programming", "python", "machine learning"]
        topics_found = any(topic in topics for topic in expected_topics)

        self.log_test_result("Topic Extraction", topics_found, "Found topics: {topics}")

        # Test 3: Interaction analysis
        try:
            metrics = await analyzer.analyze_interaction(
                user_id=self.test_user_id,
                conversation_id=self.test_conversation_id,
                user_message="Thanks, that was really helpful for my Python project!",
                assistant_response="I'm glad I could help with your Python development.",
                response_time=1.5,
                tools_used=["python_analyzer", "code_helper"],
            )

            analysis_success = (
                metrics is not None
                and metrics.feedback_type == FeedbackType.POSITIVE
                and "python" in [t.lower() for t in (metrics.topics or [])]
            )

            self.log_test_result(
                "Full Interaction Analysis",
                analysis_success,
                "Metrics: {metrics.feedback_type if metrics else 'None'}, Topics: {metrics.topics if metrics else \
                    'None'}",
            )
        except Exception:
            self.log_test_result("Full Interaction Analysis", False, "Exception: {e}")

    async def test_adaptive_learning_system(self):
        """Test the main adaptive learning system."""
        print("🧪 Testing AdaptiveLearningSystem...")

        system = AdaptiveLearningSystem()

        # Test 1: Process interaction
        try:
            result = await system.process_interaction(
                user_id=self.test_user_id,
                conversation_id=self.test_conversation_id,
                user_message="Can you help me understand async programming in Python?",
                assistant_response="Async programming in Python uses asyncio for concurrent execution...",
                response_time=2.1,
                tools_used=["python_docs", "code_examples"],
            )

            process_success = result.get("status") == "success" and "learning_applied" in result

            self.log_test_result(
                "Process Interaction", process_success, "Result: {json.dumps(result, indent=2)}"
            )
        except Exception:
            self.log_test_result("Process Interaction", False, "Exception: {e}")
        # Test 2: Process positive feedback
        try:
            positive_result = await system.process_interaction(
                user_id=self.test_user_id,
                conversation_id=self.test_conversation_id,
                user_message="Perfect! That was exactly what I needed. Thank you!",  # More clearly positive
                assistant_response="Great! I'm happy the async explanation was helpful.",
                response_time=1.2,
                tools_used=["python_docs"],
            )

            positive_success = (
                positive_result.get("status") == "success"
                and positive_result.get("feedback_type") == "positive"
            )

            self.log_test_result(
                "Process Positive Feedback",
                positive_success,
                "Feedback type: {positive_result.get('feedback_type')}",
            )
        except Exception:
            self.log_test_result("Process Positive Feedback", False, "Exception: {e}")

        # Test 3: Process correction
        try:
            correction_result = await system.process_interaction(
                user_id=self.test_user_id,
                conversation_id=self.test_conversation_id,
                user_message="Actually, that's not quite right. The await keyword should be used differently.",
                assistant_response="Thank you for the correction! You're absolutely right about await usage.",
                response_time=1.8,
                tools_used=["python_docs"],
            )

            correction_success = (
                correction_result.get("status") == "success"
                and correction_result.get("feedback_type") == "correction"
            )

            self.log_test_result(
                "Process Correction",
                correction_success,
                "Feedback type: {correction_result.get('feedback_type')}",
            )
        except Exception:
            self.log_test_result("Process Correction", False, "Exception: {e}")

        # Test 4: Get user insights
        try:
            insights = await system.get_user_insights(self.test_user_id)

            insights_success = (
                insights.get("status") == "success"
                and "insights" in insights
                and "total_interactions" in insights["insights"]
            )

            self.log_test_result(
                "Get User Insights",
                insights_success,
                "Interactions: {insights.get('insights', {}).get('total_interactions', 0)}",
            )

            if insights_success:
                print("📊 User Insights Summary:")
                insights["insights"]
                print("   - Total interactions: {user_insights.get('total_interactions', 0)}")
                print("   - Top topics: {user_insights.get('top_topics', {})}")
                print("   - Preferred tools: {user_insights.get('preferred_tools', {})}")
                print("   - Avg context relevance: {user_insights.get('avg_context_relevance', 0)}")
                print("   - Learning trend: {user_insights.get('learning_trend', 'unknown')}")
                print()

        except Exception:
            self.log_test_result("Get User Insights", False, "Exception: {e}")

    async def test_knowledge_expansion(self):
        """Test knowledge expansion functionality."""
        print("🧪 Testing Knowledge Expansion...")

        system = AdaptiveLearningSystem()

        # Test knowledge expansion queue
        try:
            # Simulate an interaction that should trigger knowledge expansion
            await system.process_interaction(
                user_id=self.test_user_id,
                conversation_id=self.test_conversation_id,
                user_message="Please remember that I prefer detailed technical explanations with examples.",
                assistant_response="I'll remember your preference for detailed technical explanations with examples.",
                response_time=1.0,
                tools_used=["memory_system"],
            )

            # Check if item was queued
            queue_has_items = len(system.knowledge_expansion_queue) > 0

            self.log_test_result(
                "Knowledge Expansion Queuing",
                queue_has_items,
                "Queue length: {len(system.knowledge_expansion_queue)}",
            )

            # Test queue processing
            if queue_has_items:
                try:
                    await system.process_knowledge_expansion_queue()
                    self.log_test_result(
                        "Knowledge Expansion Processing", True, "Queue processed without errors"
                    )
                except Exception:
                    self.log_test_result(
                        "Knowledge Expansion Processing", False, "Processing error: {e}"
                    )

        except Exception:
            self.log_test_result("Knowledge Expansion System", False, "Exception: {e}")

    async def test_error_handling(self):
        """Test error handling in the adaptive learning system."""
        print("🧪 Testing Error Handling...")

        system = AdaptiveLearningSystem()

        # Test with invalid user ID
        try:
            result = await system.process_interaction(
                user_id="",  # Invalid empty user ID
                conversation_id="",
                user_message="Test message",
                assistant_response="Test response",
                response_time=-1.0,  # Invalid negative time
                tools_used=None,
            )

            # Should handle gracefully and return error status or success with defaults
            error_handled = result.get("status") in ["success", "error", "failed"]

            self.log_test_result(
                "Invalid Input Handling", error_handled, "Result status: {result.get('status')}"
            )
        except Exception:
            self.log_test_result("Invalid Input Handling", False, "Unhandled exception: {e}")

        # Test insights for non-existent user
        try:
            insights = await system.get_user_insights("non_existent_user_12345")

            no_data_handled = insights.get("status") == "no_data"

            self.log_test_result(
                "Non-existent User Handling", no_data_handled, "Status: {insights.get('status')}"
            )
        except Exception:
            self.log_test_result("Non-existent User Handling", False, "Exception: {e}")

    async def test_global_system_instance(self):
        """Test the global adaptive learning system instance."""
        print("🧪 Testing Global System Instance...")

        # Test that global instance exists and is functional
        try:
            result = await adaptive_learning_system.process_interaction(
                user_id="global_test_user",
                conversation_id="global_test_conv",
                user_message="Testing global instance functionality",
                assistant_response="Global instance is working correctly",
                response_time=1.0,
            )

            global_works = result.get("status") == "success"

            self.log_test_result(
                "Global Instance Functionality", global_works, "Status: {result.get('status')}"
            )

        except Exception:
            self.log_test_result("Global Instance Functionality", False, "Exception: {e}")

    def print_summary(self):
        """Print test summary."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests

        print("=" * 60)
        print("🧪 ADAPTIVE LEARNING TEST SUMMARY")
        print("=" * 60)
        print("Total Tests: {total_tests}")
        print("✅ Passed: {passed_tests}")
        print("❌ Failed: {failed_tests}")
        print(
            "Success Rate: {(passed_tests/total_tests)*100:.1f}%"
            if total_tests > 0
            else "No tests run"
        )
        print()

        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["passed"]:
                    print("   - {result['test']}: {result['details']}")
            print()

        ____________overall_status = (
            "✅ ALL TESTS PASSED" if failed_tests == 0 else "❌ SOME TESTS FAILED"
        )
        print("Overall Status: {overall_status}")
        print("=" * 60)

        return failed_tests == 0

    async def run_all_tests(self):
        """Run all tests."""
        print("🚀 Starting Adaptive Learning System Tests...")
        print("=" * 60)

        await self.test_conversation_analyzer()
        await self.test_adaptive_learning_system()
        await self.test_knowledge_expansion()
        await self.test_error_handling()
        await self.test_global_system_instance()

        return self.print_summary()


async def main():
    """Main test function."""
    print("🧪 Adaptive Learning System Test Suite")
    print("=====================================")
    print()

    tester = AdaptiveLearningTester()

    try:
        success = await tester.run_all_tests()

        # Save test results
        results_file = "adaptive_learning_test_results.json"
        with open(results_file, "w") as f:
            json.dump(
                {
                    "test_run": {
                        "timestamp": datetime.now().isoformat(),
                        "total_tests": len(tester.test_results),
                        "passed": sum(1 for r in tester.test_results if r["passed"]),
                        "failed": sum(1 for r in tester.test_results if not r["passed"]),
                        "success": success,
                    },
                    "results": tester.test_results,
                },
                f,
                indent=2,
            )

        print("📄 Test results saved to: {results_file}")

        if success:
            print("\n🎉 All tests passed! Adaptive learning system is working correctly.")
            sys.exit(0)
        else:
            print("\n⚠️ Some tests failed. Check the details above.")
            sys.exit(1)

    except Exception:
        print("\n💥 Test suite crashed: {e}")

        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
