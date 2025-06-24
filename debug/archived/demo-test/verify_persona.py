#!/usr/bin/env python3
"""
Persona Verification Script
Verifies that persona.json is up-to-date with actual codebase functionality.
"""

import json
import os
import sys
from pathlib import Path

def load_persona():
    """Load persona.json configuration."""
    persona_path = Path(__file__).parent / "persona.json"
    with open(persona_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify_files_exist():
    """Verify that critical files mentioned in persona exist."""
    base_path = Path(__file__).parent
    critical_files = [
        "main.py",
        "cache_manager.py", 
        "database_manager.py",
        "enhanced_integration.py",
        "feedback_router.py",
        "storage_manager.py",
        "ai_tools.py",
        "error_handler.py"
    ]
    
    missing_files = []
    for file in critical_files:
        if not (base_path / file).exists():
            missing_files.append(file)
    
    return missing_files

def verify_persona_features():
    """Verify persona features against actual codebase."""
    persona = load_persona()
    results = {
        "version_info": {
            "version": persona["system_status"]["version"],
            "last_updated": persona["system_status"]["last_updated"],
            "production_ready": persona["system_status"]["production_readiness"]
        },
        "models": {
            "available": persona["capabilities"]["models"]["available_models"],
            "primary": persona["capabilities"]["models"]["primary_llm"],
            "newest": persona["capabilities"]["models"]["newest_model"]
        },
        "new_features": persona["system_status"]["new_features"],
        "critical_files": verify_files_exist()
    }
    
    return results

def check_implementation_status():
    """Check if new features are actually implemented."""
    base_path = Path(__file__).parent
    
    # Check for streaming features
    main_py_content = (base_path / "main.py").read_text(encoding='utf-8')
    streaming_features = {
        "STREAM_SESSION_STOP": "STREAM_SESSION_STOP" in main_py_content,
        "STREAM_SESSION_METADATA": "STREAM_SESSION_METADATA" in main_py_content,
        "session_cleanup": "cleanup_old_sessions" in main_py_content,
        "retry_mechanisms": (base_path / "utils" / "error_handling.py").exists() and "retry_on_failure" in (base_path / "utils" / "error_handling.py").read_text(encoding='utf-8')
    }
    
    # Check cache management
    cache_manager_content = ""
    if (base_path / "cache_manager.py").exists():
        cache_manager_content = (base_path / "cache_manager.py").read_text(encoding='utf-8')
    
    cache_features = {
        "cache_manager_exists": (base_path / "cache_manager.py").exists(),
        "system_prompt_checking": "check_system_prompt_change" in main_py_content,
        "cache_versioning": "VERSION_KEY" in cache_manager_content
    }
    
    # Check model support
    task_status_path = base_path / "task_completion_status.json"
    model_support = {"mistral_tested": False}
    if task_status_path.exists():
        task_status = json.loads(task_status_path.read_text())
        model_support["mistral_tested"] = "mistral:7b-instruct" in str(task_status)
    
    # Check for enhanced features
    enhanced_features = {
        "enhanced_integration": (base_path / "enhanced_integration.py").exists(),
        "feedback_router": (base_path / "feedback_router.py").exists(),
        "storage_manager": (base_path / "storage_manager.py").exists(),
        "error_handler": (base_path / "error_handler.py").exists()
    }
    
    return {
        "streaming_features": streaming_features,
        "cache_features": cache_features,
        "model_support": model_support,
        "enhanced_features": enhanced_features
    }

def main():
    """Main verification function."""
    print("=== Persona Verification Report ===\n")
    
    try:
        # Load and verify persona
        results = verify_persona_features()
        impl_status = check_implementation_status()
        
        # Print version info
        print("📋 Version Information:")
        print(f"   Version: {results['version_info']['version']}")
        print(f"   Last Updated: {results['version_info']['last_updated']}")
        print(f"   Production Ready: {results['version_info']['production_ready']}")
        
        # Print model info
        print(f"\n🤖 Model Configuration:")
        print(f"   Primary LLM: {results['models']['primary']}")
        print(f"   Newest Model: {results['models']['newest']}")
        print(f"   Available Models: {', '.join(results['models']['available'])}")
        
        # Print new features
        print(f"\n✨ New Features Listed:")
        for feature in results['new_features']:
            print(f"   ✓ {feature}")
        
        # Print implementation status
        print(f"\n🔧 Implementation Status:")
        print(f"   Streaming Features:")
        for feature, status in impl_status['streaming_features'].items():
            status_icon = "✅" if status else "❌"
            print(f"     {status_icon} {feature}: {status}")
          print(f"   Cache Features:")
        for feature, status in impl_status['cache_features'].items():
            status_icon = "✅" if status else "❌"
            print(f"     {status_icon} {feature}: {status}")
        
        print(f"   Model Support:")
        for feature, status in impl_status['model_support'].items():
            status_icon = "✅" if status else "❌"
            print(f"     {status_icon} {feature}: {status}")
        
        print(f"   Enhanced Features:")
        for feature, status in impl_status['enhanced_features'].items():
            status_icon = "✅" if status else "❌"
            print(f"     {status_icon} {feature}: {status}")
        
        # Check for missing files
        print(f"\n📁 Critical Files:")
        if results['critical_files']:
            print(f"   ❌ Missing files: {', '.join(results['critical_files'])}")
        else:
            print(f"   ✅ All critical files present")
        
        # Overall assessment
        missing_files = len(results['critical_files'])
        implemented_features = sum(impl_status['streaming_features'].values()) + \
                             sum(impl_status['cache_features'].values()) + \
                             sum(impl_status['model_support'].values()) + \
                             sum(impl_status['enhanced_features'].values())
        total_features = len(impl_status['streaming_features']) + \
                        len(impl_status['cache_features']) + \
                        len(impl_status['model_support']) + \
                        len(impl_status['enhanced_features'])
        
        print(f"\n📊 Overall Assessment:")
        print(f"   Features Implemented: {implemented_features}/{total_features}")
        print(f"   Implementation Rate: {(implemented_features/total_features)*100:.1f}%")
        
        if missing_files == 0 and implemented_features >= total_features * 0.8:
            print(f"   🎉 Persona is UP-TO-DATE and reflects actual functionality!")
        elif missing_files > 0:
            print(f"   ⚠️  Persona may be outdated - missing critical files")
        else:
            print(f"   ⚠️  Persona may be outdated - some features not fully implemented")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
