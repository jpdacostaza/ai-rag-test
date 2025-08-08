#!/usr/bin/env python3
"""
Debug the v5.0 identity fact extraction to see why it's storing 0 memories
"""

def debug_identity_extraction():
    """Test the identity extraction logic"""
    
    # Test messages that should extract facts
    test_messages = [
        "Hello my name is J.P. I work at swift, can you remember that?",
        "My name is J.P. and I work at Swift",
        "hello, what do you know about me ?",
        "Search the web https://www.swift.com/ to check where i work and remember this"
    ]
    
    def extract_identity_facts(content: str):
        """Extract clear factual statements from content"""
        facts = []
        
        print(f"\n🔍 Testing: '{content}'")
        
        # Look for identity patterns
        if "my name is" in content.lower():
            print("  ✅ Found 'my name is' pattern")
            # Extract name
            parts = content.lower().split("my name is")
            if len(parts) > 1:
                name_part = parts[1].split(".")[0].split(",")[0].strip()
                print(f"  📝 Name part extracted: '{name_part}'")
                if name_part:
                    fact = f"User's name is {name_part}"
                    facts.append(fact)
                    print(f"  ✅ Added fact: '{fact}'")
        else:
            print("  ❌ No 'my name is' pattern found")
        
        # Look for work/company patterns
        if "i work at" in content.lower():
            print("  ✅ Found 'i work at' pattern")
            parts = content.lower().split("i work at")
            if len(parts) > 1:
                work_part = parts[1].split(".")[0].split(",")[0].strip()
                print(f"  📝 Work part extracted: '{work_part}'")
                if work_part:
                    fact = f"User works at {work_part}"
                    facts.append(fact)
                    print(f"  ✅ Added fact: '{fact}'")
        else:
            print("  ❌ No 'i work at' pattern found")
        
        # Look for other identity information
        identity_keywords = ["i am", "i'm a", "i do", "my job", "my role", "my company"]
        found_keywords = []
        for keyword in identity_keywords:
            if keyword in content.lower():
                found_keywords.append(keyword)
        
        if found_keywords:
            print(f"  ✅ Found identity keywords: {found_keywords}")
            # Extract the relevant sentence
            sentences = content.split(".")
            for sentence in sentences:
                for keyword in found_keywords:
                    if keyword in sentence.lower():
                        clean_sentence = sentence.strip()
                        print(f"  📝 Sentence with '{keyword}': '{clean_sentence}'")
                        if len(clean_sentence) > 10 and len(clean_sentence) < 200:
                            facts.append(clean_sentence)
                            print(f"  ✅ Added sentence as fact: '{clean_sentence}'")
        else:
            print("  ❌ No identity keywords found")
        
        print(f"  🎯 Total facts extracted: {len(facts)}")
        for i, fact in enumerate(facts, 1):
            print(f"     {i}. {fact}")
        
        return facts
    
    print("🧪 DEBUGGING IDENTITY FACT EXTRACTION")
    print("=" * 50)
    
    for msg in test_messages:
        facts = extract_identity_facts(msg)
        print()
    
    print("=" * 50)
    print("🎯 SUMMARY:")
    print("If facts are being extracted here but 0 memories stored,")
    print("the issue is likely in the HTTP request to memory API")

if __name__ == "__main__":
    debug_identity_extraction()
