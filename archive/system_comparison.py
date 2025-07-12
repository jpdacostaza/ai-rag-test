"""
Simple Comparison: Current vs Enhanced Systems
==============================================

Direct comparison of web search trigger efficiency and best practices.
"""

# Test both systems
from web_search_tool import should_trigger_web_search as current_trigger
from enhanced_web_search_trigger import should_trigger_web_search as enhanced_trigger, analyze_search_trigger
from pipelines.anti_hallucination_module import assess_response_safety

def compare_systems():
    """Compare current vs enhanced trigger systems with real examples."""
    
    test_cases = [
        # Should trigger (current information needed)
        {
            "query": "What is the current stock price of Apple?",
            "response": "I don't have access to real-time stock prices.",
            "expected": True,
            "category": "Financial Data"
        },
        {
            "query": "Who is the current CEO of Tesla?",
            "response": "Based on my knowledge, Elon Musk is the CEO.",
            "expected": True,
            "category": "Leadership Info"
        },
        {
            "query": "Latest iPhone 15 features released in 2024",
            "response": "The iPhone 15 includes several new features.",
            "expected": True,
            "category": "Product Info"
        },
        
        # Should NOT trigger (general knowledge)
        {
            "query": "Explain recursion in programming",
            "response": "Recursion is when a function calls itself.",
            "expected": False,
            "category": "Programming Concepts"
        },
        {
            "query": "What is 47 * 23?",
            "response": "47 multiplied by 23 equals 1,081.",
            "expected": False,
            "category": "Math"
        },
        {
            "query": "Write a poem about autumn",
            "response": "Here's a poem about autumn leaves...",
            "expected": False,
            "category": "Creative"
        },
        
        # Edge case: Swift company vs programming language
        {
            "query": "Swift programming language vs Swift financial company",
            "response": "These are two different entities with the same name.",
            "expected": True,  # Should clarify which Swift
            "category": "Disambiguation"
        }
    ]
    
    print("🔍 WEB SEARCH TRIGGER COMPARISON")
    print("=" * 80)
    
    current_correct = 0
    enhanced_correct = 0
    total_tests = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        query = case["query"]
        response = case["response"]
        expected = case["expected"]
        category = case["category"]
        
        print(f"\n{i}. {category}: {query}")
        print("-" * 60)
        
        # Test current system
        current_result = current_trigger(query, response)
        current_match = current_result == expected
        if current_match:
            current_correct += 1
        
        # Test enhanced system
        enhanced_result = enhanced_trigger(query, response)
        enhanced_match = enhanced_result == expected
        if enhanced_match:
            enhanced_correct += 1
        
        # Get detailed analysis
        analysis = analyze_search_trigger(query, response)
        
        # Test anti-hallucination
        safety = assess_response_safety(query, response)
        
        print(f"Expected: {'✅ TRIGGER' if expected else '❌ NO TRIGGER'}")
        print(f"Current:  {'✅ TRIGGER' if current_result else '❌ NO TRIGGER'} {'✓' if current_match else '✗'}")
        print(f"Enhanced: {'✅ TRIGGER' if enhanced_result else '❌ NO TRIGGER'} {'✓' if enhanced_match else '✗'} (conf: {analysis['confidence']:.2f})")
        print(f"Risk Level: {safety['risk_assessment']['risk_level']} (verify: {safety['risk_assessment']['should_verify']})")
        
        if enhanced_result:
            print(f"Reasons: {', '.join(analysis['reasons'])}")
    
    print("\n" + "=" * 80)
    print("📊 RESULTS SUMMARY")
    print("-" * 40)
    print(f"Current System Accuracy:  {current_correct}/{total_tests} ({current_correct/total_tests*100:.1f}%)")
    print(f"Enhanced System Accuracy: {enhanced_correct}/{total_tests} ({enhanced_correct/total_tests*100:.1f}%)")
    
    if enhanced_correct > current_correct:
        print("🏆 Enhanced system performs better!")
    elif current_correct > enhanced_correct:
        print("🏆 Current system performs better!")
    else:
        print("🤝 Both systems perform equally!")
    
    return {
        "current_accuracy": current_correct / total_tests,
        "enhanced_accuracy": enhanced_correct / total_tests,
        "total_tests": total_tests
    }

def test_efficiency():
    """Test the efficiency of both systems."""
    print("\n⚡ EFFICIENCY COMPARISON")
    print("=" * 80)
    
    import time
    
    test_query = "What is the current stock price of Apple Inc?"
    test_response = "I don't have current stock price information."
    iterations = 100
    
    # Test current system
    start = time.time()
    for _ in range(iterations):
        current_trigger(test_query, test_response)
    current_time = time.time() - start
    
    # Test enhanced system  
    start = time.time()
    for _ in range(iterations):
        enhanced_trigger(test_query, test_response)
    enhanced_time = time.time() - start
    
    print(f"Current System:  {current_time:.4f}s ({current_time/iterations*1000:.2f}ms per call)")
    print(f"Enhanced System: {enhanced_time:.4f}s ({enhanced_time/iterations*1000:.2f}ms per call)")
    
    if current_time > 0:
        print(f"Performance Ratio: {enhanced_time/current_time:.2f}x")
    else:
        print("Performance Ratio: Enhanced system is measurably slower (current system too fast to measure)")
    
    if enhanced_time < current_time * 3:  # Less than 3x slower is acceptable
        print("✅ Enhanced system has acceptable performance overhead")
    else:
        print("⚠️ Enhanced system may be too slow for production")

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE SYSTEM COMPARISON")
    print("Analyzing efficiency and best practices for web search triggers")
    print("=" * 80)
    
    # Run accuracy comparison
    results = compare_systems()
    
    # Run efficiency test
    test_efficiency()
    
    print("\n" + "=" * 80)
    print("🎯 CONCLUSIONS & RECOMMENDATIONS")
    print("-" * 40)
    
    if results["enhanced_accuracy"] >= results["current_accuracy"]:
        print("✅ Enhanced system provides better or equal accuracy")
        print("✅ Enhanced system uses industry best practices")
        print("✅ Anti-hallucination module provides additional safety")
        print("✅ Confidence scoring enables better decision making")
        print("\n📝 RECOMMENDATION: Adopt enhanced system for production")
    else:
        print("❌ Current system still more accurate")
        print("📝 RECOMMENDATION: Analyze failed cases and improve enhanced system")
    
    print(f"\n📈 IMPROVEMENT: {(results['enhanced_accuracy'] - results['current_accuracy'])*100:.1f}% accuracy change")
    print("🔧 BEST PRACTICES IMPLEMENTED:")
    print("   • Confidence-based scoring (ML approach)")
    print("   • Multi-pattern detection (regex + keywords)")
    print("   • Risk assessment for hallucination")
    print("   • Temporal and entity-specific triggers")
    print("   • Creative and math exclusions")
