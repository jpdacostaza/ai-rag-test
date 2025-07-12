#!/usr/bin/env python3
"""
Debug Duplicate Detection
=========================

Test the duplicate detection function directly.
"""

def calculate_content_similarity(content1: str, content2: str) -> float:
    """
    Calculate similarity between two pieces of content.
    Returns a score between 0.0 and 1.0.
    """
    try:
        # Normalize content
        content1 = content1.strip().lower()
        content2 = content2.strip().lower()
        
        print(f"Comparing:")
        print(f"  Content 1: '{content1}'")
        print(f"  Content 2: '{content2}'")
        
        # Exact match
        if content1 == content2:
            print(f"  Result: 1.0 (exact match)")
            return 1.0
        
        # Length difference check
        len_diff = abs(len(content1) - len(content2))
        max_len = max(len(content1), len(content2))
        if max_len > 0 and len_diff / max_len > 0.5:
            print(f"  Result: 0.0 (very different lengths: {len_diff}/{max_len})")
            return 0.0  # Very different lengths
        
        # Word-based similarity
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        print(f"  Words 1: {words1}")
        print(f"  Words 2: {words2}")
        
        if not words1 or not words2:
            print(f"  Result: 0.0 (empty word sets)")
            return 0.0
        
        # Jaccard similarity (intersection over union)
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        jaccard_score = len(intersection) / len(union) if union else 0.0
        
        print(f"  Intersection: {intersection}")
        print(f"  Union: {union}")
        print(f"  Jaccard score: {jaccard_score}")
        
        # Boost score for name matching
        import re
        name1 = re.search(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b', content1)
        name2 = re.search(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b', content2)
        if name1 and name2 and name1.group(1).lower() == name2.group(1).lower():
            jaccard_score += 0.15
            print(f"  Name match bonus: +0.15")
        
        # Work terms matching
        work_terms = ["engineer", "developer", "programmer", "analyst", "manager", "director", "consultant"]
        work1 = {term for term in work_terms if term in content1}
        work2 = {term for term in work_terms if term in content2}
        if work1 and work2 and work1.intersection(work2):
            jaccard_score += 0.1
            print(f"  Work terms match: {work1.intersection(work2)} (+0.1)")
        
        final_score = min(1.0, jaccard_score)
        print(f"  Final score: {final_score}")
        
        return final_score
        
    except Exception as e:
        print(f"  Error: {e}")
        return 0.0

def main():
    """Test similarity calculations."""
    print("🔧 Testing Content Similarity...\n")
    
    # Test cases from our deduplication test
    test_cases = [
        # Exact duplicates
        ("My name is John Smith and I work as a software engineer at TechCorp", 
         "My name is John Smith and I work as a software engineer at TechCorp"),
        
        # Very similar
        ("My name is John Smith and I work as a software engineer at TechCorp",
         "My name is John Smith and I'm a software engineer at TechCorp"),
        
        # Different content
        ("My name is John Smith and I work as a software engineer at TechCorp",
         "I have 5 years of experience in Python programming and machine learning"),
    ]
    
    for i, (content1, content2) in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        similarity = calculate_content_similarity(content1, content2)
        print(f"Similarity: {similarity:.3f}")
        if similarity >= 0.90:
            print("✅ Would be detected as duplicate (threshold 0.90)")
        elif similarity >= 0.85:
            print("⚠️ Would be detected as duplicate (threshold 0.85)")
        else:
            print("❌ Would NOT be detected as duplicate")
        print()

if __name__ == "__main__":
    main()
