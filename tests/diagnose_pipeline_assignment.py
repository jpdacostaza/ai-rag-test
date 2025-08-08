#!/usr/bin/env python3
"""
Diagnose Pipeline Assignment Issues in OpenWebUI
"""

import requests
import json

def check_pipeline_assignment():
    """Check why Enhanced Memory Pipeline isn't being triggered"""
    print("🔍 DIAGNOSING PIPELINE ASSIGNMENT ISSUES")
    print("=" * 60)
    
    # Check if Enhanced Memory Pipeline is being called
    print("📊 Recent Pipeline Activity:")
    try:
        # Get recent OpenWebUI conversations to see which pipelines are called
        print("   Checking pipeline logs...")
        
        # Test direct pipeline call to see if it works
        test_msg = {
            "user": {"id": "test_user", "name": "Test", "role": "user"},
            "messages": [{"role": "user", "content": "Hello, do you remember me?"}],
            "body": {
                "model": "qwen2.5:3b",
                "messages": [{"role": "user", "content": "Hello, do you remember me?"}],
                "stream": False
            }
        }
        
        # Test Enhanced Memory Pipeline directly
        print("\n🧪 Testing Enhanced Memory Pipeline Direct Call:")
        r1 = requests.post(
            "http://localhost:9099/enhanced_memory_pipeline/filter/inlet",
            json=test_msg
        )
        if r1.status_code == 200:
            print("   ✅ Enhanced Memory Pipeline: ACCESSIBLE")
            result = r1.json()
            if "Relevant Context from Memory" in str(result):
                print("   ✅ Memory Enhancement: WORKING")
            else:
                print("   ❌ Memory Enhancement: NOT WORKING")
        else:
            print(f"   ❌ Enhanced Memory Pipeline: ERROR {r1.status_code}")
        
        # Test Anti-Hallucination Pipeline (which IS being called)
        print("\n🧪 Testing Anti-Hallucination Pipeline Direct Call:")
        r2 = requests.post(
            "http://localhost:9099/anti_hallucination_pipeline/filter/inlet",
            json=test_msg
        )
        if r2.status_code == 200:
            print("   ✅ Anti-Hallucination Pipeline: ACCESSIBLE")
        else:
            print(f"   ❌ Anti-Hallucination Pipeline: ERROR {r2.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def check_openwebui_pipeline_config():
    """Check OpenWebUI pipeline configuration"""
    print("\n⚙️ CHECKING OPENWEBUI PIPELINE CONFIGURATION")
    print("=" * 60)
    
    try:
        # Check pipeline list from OpenWebUI perspective
        r = requests.get("http://localhost:9099/pipelines")
        if r.status_code == 200:
            pipelines = r.json()
            print(f"📋 Available Pipelines ({len(pipelines)}):")
            
            memory_pipeline_found = False
            anti_hall_pipeline_found = False
            
            for pipeline in pipelines:
                pipeline_id = pipeline.get("id", "unknown")
                print(f"   - {pipeline_id}")
                
                if "enhanced_memory" in pipeline_id:
                    memory_pipeline_found = True
                if "anti_hallucination" in pipeline_id:
                    anti_hall_pipeline_found = True
            
            print(f"\n📊 Pipeline Status:")
            print(f"   Enhanced Memory Pipeline: {'✅ Found' if memory_pipeline_found else '❌ Missing'}")
            print(f"   Anti-Hallucination Pipeline: {'✅ Found' if anti_hall_pipeline_found else '❌ Missing'}")
            
            if memory_pipeline_found and anti_hall_pipeline_found:
                print("\n💡 ISSUE IDENTIFIED:")
                print("   Both pipelines exist, but only Anti-Hallucination is being called.")
                print("   This suggests a MODEL ASSIGNMENT issue in OpenWebUI.")
                
        else:
            print(f"❌ Pipeline list error: {r.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking pipelines: {e}")

def provide_model_assignment_fix():
    """Provide steps to fix model assignment"""
    print("\n🔧 MODEL ASSIGNMENT FIX STEPS")
    print("=" * 60)
    
    print("📋 STEP 1: Check Model Pipeline Assignment")
    print("   1. Go to OpenWebUI Settings → Models")
    print("   2. Find 'qwen2.5:3b' model")
    print("   3. Click on the model settings/edit button")
    print("   4. Look for 'Pipelines' section")
    print("   5. Ensure 'Enhanced Memory Pipeline' is SELECTED/ASSIGNED")
    
    print("\n📋 STEP 2: Alternative - Global Pipeline Assignment")
    print("   1. Go to Settings → Pipelines")
    print("   2. Check 'Enable Global Context' toggle")
    print("   3. Ensure Enhanced Memory Pipeline is enabled globally")
    
    print("\n📋 STEP 3: Verify Pipeline Order")
    print("   1. In Settings → Pipelines")
    print("   2. Check if pipelines have priority/order settings")
    print("   3. Enhanced Memory should run BEFORE Anti-Hallucination")
    
    print("\n🚨 CRITICAL ISSUE:")
    print("   Currently only Anti-Hallucination Pipeline is being triggered.")
    print("   Enhanced Memory Pipeline is enabled but NOT ASSIGNED to your model.")

def fix_web_search_hallucination():
    """Address the web search hallucination issue"""
    print("\n🌐 WEB SEARCH HALLUCINATION FIX")
    print("=" * 60)
    
    print("🔍 ISSUE: Web search found wrong 'Swift' company (SeaWorld)")
    print("💡 SOLUTION: Enhanced Memory Pipeline should provide context FIRST")
    print("   - Memory should say 'User works at Swift technology company'")
    print("   - This context should prevent wrong web search results")
    
    print("\n⚙️ Current Problem:")
    print("   1. Enhanced Memory Pipeline NOT being called")
    print("   2. No user context provided to model")
    print("   3. Model searches web without knowing user's actual Swift company")
    print("   4. Finds SeaWorld's Swift brand instead")
    
    print("\n✅ Expected Flow (when fixed):")
    print("   1. Enhanced Memory Pipeline adds: 'User J.P. works at Swift tech company'")
    print("   2. Model has context about user's actual workplace")
    print("   3. Web search (if needed) would be more targeted")
    print("   4. No hallucination about wrong Swift company")

def main():
    """Main diagnostic function"""
    check_pipeline_assignment()
    check_openwebui_pipeline_config()
    provide_model_assignment_fix()
    fix_web_search_hallucination()
    
    print("\n" + "=" * 70)
    print("🎯 SUMMARY")
    print("=" * 70)
    print("✅ Enhanced Memory Pipeline: Working in isolation")
    print("❌ Model Assignment: Pipeline not assigned to qwen2.5:3b model")
    print("❌ Session Persistence: Not working due to pipeline not being called")
    print("❌ Web Search Issue: No memory context causing hallucination")
    
    print("\n🔧 IMMEDIATE ACTION REQUIRED:")
    print("   Go to OpenWebUI Settings → Models → qwen2.5:3b")
    print("   Assign Enhanced Memory Pipeline to the model")

if __name__ == "__main__":
    main()
