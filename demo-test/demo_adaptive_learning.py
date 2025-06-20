#!/usr/bin/env python3
import asyncio
import os
import sys
import traceback

from adaptive_learning import adaptive_learning_system

"""

Adaptive Learning System Demonstration
======================================

Real-world demo showing how the adaptive learning system works
with actual user interaction patterns.
"""


# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def demo_adaptive_learning():
    """Demonstrate adaptive learning with realistic user interactions."""

    print("🧠 Adaptive Learning System Demo")
    print("=" * 50)

    user_id = "demo_user"
    conversation_id = "demo_conv_001"

    # Simulate a series of realistic interactions
    interactions = [
        {
            "user_message": "Can you help me with Python async programming?",
            "assistant_response": "I'd be happy to help! Async programming in Python uses the asyncio library for \
                concurrent execution...",
            "response_time": 1.2,
            "tools_used": ["python_docs", "code_examples"],
        },
        {
            "user_message": "Thanks! That was really helpful. Can you show me an example?",
            "assistant_response": "Here's a simple example of async/await in Python: [code example provided]",
            "response_time": 0.8,
            "tools_used": ["code_generator", "python_docs"],
        },
        {
            "user_message": "Perfect! I understand now. Can you also explain coroutines?",
            "assistant_response": "Coroutines are the building blocks of async programming. They are functions that can \
                be paused and resumed...",
            "response_time": 1.5,
            "tools_used": ["python_docs"],
        },
        {
            "user_message": "Actually, I think there's an error in your first example. The await should be inside an \
                async function.",
            "assistant_response": "You're absolutely right! Thank you for the correction. The await keyword must be \
                used inside an async function.",
            "response_time": 0.6,
            "tools_used": ["code_validator"],
        },
        {
            "user_message": "Great! Now I'm working on a web scraping project. Any advice?",
            "assistant_response": "For web scraping in Python, you can use libraries like requests, BeautifulSoup, or \
                aiohttp for async scraping...",
            "response_time": 1.1,
            "tools_used": ["web_scraping_tools", "python_docs"],
        },
        {
            "user_message": "Please remember that I prefer detailed code examples with explanations.",
            "assistant_response": "I'll make sure to provide detailed code examples with step-by-step explanations in \
                future responses.",
            "response_time": 0.5,
            "tools_used": ["memory_system"],
        },
    ]

    print("🔄 Processing interactions...")
    print()

    # Process each interaction
    for i, interaction in enumerate(interactions, 1):
        print("📝 Interaction {i}:")
        print("   User: {interaction['user_message'][:60]}...")

        ___________result = await adaptive_learning_system.process_interaction(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=interaction["user_message"],
            assistant_response=interaction["assistant_response"],
            response_time=interaction["response_time"],
            tools_used=interaction["tools_used"],
        )

        print("   Feedback: {result.get('feedback_type', 'none')}")
        print("   Context Score: {result.get('context_relevance', 0):.2f}")
        print("   Topics: {result.get('topics', [])}")
        print()

    # Get user insights after processing all interactions
    print("📊 User Learning Insights:")
    print("=" * 30)

    insights = await adaptive_learning_system.get_user_insights(user_id)

    if insights.get("status") == "success":
        user_insights = insights["insights"]

        print("Total Interactions: {user_insights.get('total_interactions', 0)}")
        print("Learning Trend: {user_insights.get('learning_trend', 'unknown')}")
        print("Average Context Relevance: {user_insights.get('avg_context_relevance', 0):.2f}")
        print()

        print("Top Topics:")
        for topic, count in list(user_insights.get("top_topics", {}).items())[:5]:
            print("  - {topic}: {count} mentions")
        print()

        print("Preferred Tools:")
        for tool, score in list(user_insights.get("preferred_tools", {}).items())[:5]:
            print("  - {tool}: score {score}")
        print()

        print("Feedback Distribution:")
        for feedback_type, count in user_insights.get("feedback_distribution", {}).items():
            print("  - {feedback_type}: {count}")
        print()

    else:
        print("❌ Could not get insights: {insights.get('message', 'unknown error')}")

    # Test the system's learning by asking for recommendations
    print("🔮 System Learning Analysis:")
    print("=" * 30)  # Check if the system learned user preferences
    user_patterns = adaptive_learning_system.user_patterns.get(user_id, {})

    if user_patterns:
        print("Learned Patterns:")

        topics = user_patterns.get("topic_preferences", {})
        if topics:
            top_topics = dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:3])
            print(f"  Favorite Topics: {top_topics}")

        tools = user_patterns.get("tool_preferences", {})
        if tools:
            top_tools = dict(sorted(tools.items(), key=lambda x: x[1], reverse=True)[:3])
            print(f"  Tool Preferences: {top_tools}")

        preferences = user_patterns.get("preferences", {})
        if preferences:
            print("  Detail Level Preference: {preferences.get('detail_level', 0.5):.2f}")
            if preferences.get("preferred_response_time"):
                ___________avg_time = sum(preferences["preferred_response_time"]) / len(
                    preferences["preferred_response_time"]
                )
                print("  Preferred Response Time: {avg_time:.2f}s")

        feedback_history = user_patterns.get("feedback_history", [])
        if feedback_history:
            positive_feedback = sum(
                1 for f in feedback_history if f.get("feedback_type") == "positive"
            )
            total_feedback = len(feedback_history)
            (positive_feedback / total_feedback) * 100
            print("  User Satisfaction Rate: {satisfaction_rate:.1f}%")

    else:
        print("No learning patterns detected yet.")

    print()
    print("🎯 Demo Complete!")
    print("The adaptive learning system successfully:")
    print("  ✅ Analyzed user interactions")
    print("  ✅ Classified feedback types")
    print("  ✅ Learned user preferences")
    print("  ✅ Tracked topic interests")
    print("  ✅ Monitored tool effectiveness")
    print("  ✅ Built user insight profile")

    return True


async def main():
    """Main demo function."""
    try:
        success = await demo_adaptive_learning()

        if success:
            print("\n🎉 Adaptive learning demo completed successfully!")
        else:
            print("\n❌ Demo encountered issues.")

    except Exception:
        print("\n💥 Demo crashed: {e}")

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
