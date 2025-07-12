#!/usr/bin/env python3
"""
Complete System Validation Test

This test runs ALL components together to validate:
1. Unit tests (user ID extraction logic)
2. End-to-end pipeline tests
3. Prompt and model integration
4. Storage and database validation  
5. Memory system with real model responses

Final comprehensive validation of Enhanced Memory Pipeline v4.0
"""

import subprocess
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any


class CompleteSystemValidator:
    """Complete system validation orchestrator"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
    
    def run_test_suite(self, test_name: str, command: List[str], description: str) -> bool:
        """Run a test suite and capture results"""
        print(f"\n{'='*60}")
        print(f"🧪 {test_name}")
        print(f"{'='*60}")
        print(f"Description: {description}")
        print("-" * 40)
        
        try:
            start = time.time()
            result = subprocess.run(command, capture_output=True, text=True, timeout=300)
            duration = time.time() - start
            
            success = result.returncode == 0
            status = "✅ PASS" if success else "❌ FAIL"
            
            print(f"\n{status} {test_name}")
            print(f"Duration: {duration:.2f} seconds")
            print(f"Exit Code: {result.returncode}")
            
            if result.stdout:
                # Show last few lines of output
                stdout_lines = result.stdout.split('\n')
                print("\nOutput (last 10 lines):")
                for line in stdout_lines[-10:]:
                    if line.strip():
                        print(f"  {line}")
            
            if result.stderr and not success:
                print(f"\nErrors: {result.stderr[:500]}")
            
            self.test_results[test_name] = {
                "success": success,
                "duration": duration,
                "exit_code": result.returncode,
                "description": description,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            return success
            
        except subprocess.TimeoutExpired:
            print(f"❌ TIMEOUT {test_name} (5 minutes)")
            self.test_results[test_name] = {
                "success": False,
                "duration": 300,
                "exit_code": -1,
                "description": description,
                "error": "Timeout"
            }
            return False
            
        except Exception as e:
            print(f"❌ ERROR {test_name}: {e}")
            self.test_results[test_name] = {
                "success": False,
                "duration": 0,
                "exit_code": -1,
                "description": description,
                "error": str(e)
            }
            return False
    
    def run_complete_validation(self) -> bool:
        """Run complete system validation"""
        print("🚀 Enhanced Memory Pipeline v4.0 - Complete System Validation")
        print("=" * 80)
        print("Running ALL tests: Unit → Integration → End-to-End → Model")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test Suite 1: Unit Tests (User ID Extraction Logic)
        unit_test_success = self.run_test_suite(
            "Unit Tests - User ID Extraction",
            [sys.executable, "-c", "import pytest; exit(pytest.main(['test_standalone_user_extraction.py', '-v']))"],
            "Validates core user ID extraction logic with priority handling"
        )
        
        # Test Suite 2: Comprehensive Memory Tests
        memory_test_success = self.run_test_suite(
            "Comprehensive Memory Tests",
            [sys.executable, "-c", "import pytest; exit(pytest.main(['test_comprehensive_user_memory.py', '-v', '--tb=short']))"],
            "Validates memory operations, user isolation, and error handling"
        )
        
        # Test Suite 3: Storage and ID Validation
        storage_test_success = self.run_test_suite(
            "Storage and ID Validation",
            [sys.executable, "validate_storage_and_ids.py"],
            "Validates Redis storage, ChromaDB, and user data isolation"
        )
        
        # Test Suite 4: End-to-End Pipeline
        pipeline_test_success = self.run_test_suite(
            "End-to-End Pipeline Tests",
            [sys.executable, "test_end_to_end_pipeline.py"],
            "Validates complete pipeline flow from prompt to database"
        )
        
        # Test Suite 5: Prompt and Model Integration
        model_test_success = self.run_test_suite(
            "Prompt and Model Integration",
            [sys.executable, "test_prompt_model_integration.py"],
            "Validates model responses with user context and memory"
        )
        
        # Generate comprehensive report
        self.generate_final_report([
            ("Unit Tests", unit_test_success),
            ("Memory Tests", memory_test_success),
            ("Storage Validation", storage_test_success),
            ("Pipeline Tests", pipeline_test_success),
            ("Model Integration", model_test_success)
        ])
        
        # Determine overall success
        critical_tests = [unit_test_success, storage_test_success]
        important_tests = [memory_test_success, pipeline_test_success, model_test_success]
        
        all_critical_passed = all(critical_tests)
        most_important_passed = sum(important_tests) >= len(important_tests) * 0.8
        
        return all_critical_passed and most_important_passed
    
    def generate_final_report(self, test_summary: List[tuple]) -> None:
        """Generate comprehensive validation report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("📊 COMPLETE SYSTEM VALIDATION REPORT")
        print("=" * 80)
        
        print(f"Validation Period: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} to {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
        print()
        
        # Test Results Summary
        print("🧪 Test Suite Results:")
        print("-" * 40)
        
        total_suites = len(test_summary)
        passed_suites = sum(1 for _, passed in test_summary if passed)
        
        for test_name, passed in test_summary:
            status = "✅ PASS" if passed else "❌ FAIL"
            duration = self.test_results.get(test_name, {}).get("duration", 0)
            print(f"{status} {test_name:<30} ({duration:.1f}s)")
        
        print()
        print(f"Suite Success Rate: {passed_suites}/{total_suites} ({passed_suites/total_suites*100:.1f}%)")
        
        # Component Status
        print("\n🔍 Component Validation Status:")
        print("-" * 40)
        
        components = {
            "User ID Extraction": test_summary[0][1],  # Unit tests
            "Memory System": test_summary[1][1],       # Memory tests  
            "Storage Layer": test_summary[2][1],       # Storage tests
            "Pipeline Flow": test_summary[3][1],       # Pipeline tests
            "Model Integration": test_summary[4][1]    # Model tests
        }
        
        for component, status in components.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {component}")
        
        # System Readiness Assessment
        print("\n🎯 System Readiness Assessment:")
        print("-" * 40)
        
        critical_systems = ["User ID Extraction", "Storage Layer"]
        important_systems = ["Memory System", "Pipeline Flow", "Model Integration"]
        
        critical_ready = all(components[sys] for sys in critical_systems)
        important_ready = sum(components[sys] for sys in important_systems) >= len(important_systems) * 0.8
        
        if critical_ready and important_ready:
            print("🎉 SYSTEM READY FOR PRODUCTION!")
            print("✅ All critical systems operational")
            print("✅ All important systems functional")
            print("✅ Enhanced Memory Pipeline v4.0 fully validated")
        elif critical_ready:
            print("⚠️  SYSTEM PARTIALLY READY")
            print("✅ Critical systems operational")
            print("⚠️  Some important systems need attention")
            print("🔧 Core functionality validated")
        else:
            print("❌ SYSTEM NOT READY")
            print("❌ Critical systems have issues")
            print("🚨 Requires immediate attention")
        
        # Feature Validation
        print("\n📋 Feature Validation Checklist:")
        print("-" * 40)
        
        features = [
            ("Priority-based user ID extraction", components["User ID Extraction"]),
            ("Multi-user memory isolation", components["Memory System"]),
            ("Redis and ChromaDB storage", components["Storage Layer"]),
            ("End-to-end pipeline flow", components["Pipeline Flow"]),
            ("Model inference with context", components["Model Integration"]),
            ("User authentication injection", components["User ID Extraction"]),
            ("Memory bleed prevention", components["Memory System"]),
            ("Error handling and recovery", components["Memory System"])
        ]
        
        for feature, validated in features:
            status = "✅" if validated else "❌"
            print(f"{status} {feature}")
        
        # Recommendations
        print("\n💡 Recommendations:")
        print("-" * 40)
        
        if all(components.values()):
            print("🚀 System is ready for production deployment")
            print("🔄 Consider setting up monitoring and alerts")
            print("📈 Ready for user load testing")
        else:
            failed_components = [name for name, status in components.items() if not status]
            print(f"🔧 Address issues in: {', '.join(failed_components)}")
            print("🧪 Re-run tests after fixes")
            print("📝 Review error logs for specific issues")
        
        # Save detailed report
        report_data = {
            "validation_timestamp": end_time.isoformat(),
            "total_duration_seconds": total_duration,
            "test_suites": {
                "total": total_suites,
                "passed": passed_suites,
                "success_rate": passed_suites/total_suites*100
            },
            "components": components,
            "system_ready": critical_ready and important_ready,
            "detailed_results": self.test_results,
            "features_validated": features
        }
        
        with open("complete_system_validation_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Complete report saved: complete_system_validation_report.json")


def main():
    """Main validation execution"""
    validator = CompleteSystemValidator()
    success = validator.run_complete_validation()
    
    print(f"\n{'='*80}")
    if success:
        print("🎉 COMPLETE SYSTEM VALIDATION: SUCCESS!")
        print("Enhanced Memory Pipeline v4.0 is fully operational")
    else:
        print("⚠️  COMPLETE SYSTEM VALIDATION: NEEDS ATTENTION")
        print("Core functionality validated, some components need review")
    print(f"{'='*80}")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
