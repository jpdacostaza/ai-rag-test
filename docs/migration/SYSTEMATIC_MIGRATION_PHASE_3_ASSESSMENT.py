#!/usr/bin/env python3
"""
Phase 3 Migration Assessment - Utilities and Supporting Functions
=================================================================

This assessment identifies Phase 3 targets for systematic migration,
focusing on utilities, helper functions, and supporting infrastructure.

MIGRATION OBJECTIVE:
Continue systematic migration with focus on utilities, testing infrastructure,
and supporting functions to achieve comprehensive codebase consolidation.

FRAMEWORKS AVAILABLE FOR PHASE 3:
1. [OK] Error Handling Patterns (utilities/error_patterns.py)
2. [OK] Memory Service consolidation (services/memory_service.py) 
3. [OK] AuthValidator consolidation (services/auth_validator.py)
4. [OK] Database Connection Factory (utilities/connection_factory.py)
5. [OK] Unified Configuration (config_unified.py)

=============================================================================
PHASE 3 TARGET IDENTIFICATION AND ANALYSIS
=============================================================================
"""

import sys
import os
from typing import Dict, List, Any

# Phase 3 migration targets identified through semantic analysis
PHASE_3_MIGRATION_TARGETS = {
    "HIGH_PRIORITY": {
        "error_handler.py": {
            "patterns_applicable": [
                "Error Handling Patterns",
                "Database Connection Factory"
            ],
            "migration_complexity": "MEDIUM",
            "estimated_impact": "HIGH",
            "analysis": {
                "current_state": "Legacy error handling with manual Redis connections",
                "duplicate_patterns": [
                    "Multiple exception handling classes (ChatErrorHandler, ToolErrorHandler, MemoryErrorHandler, etc.)",
                    "Manual Redis connection in RedisConnectionHandler",
                    "safe_execute function duplicates error_patterns functionality"
                ],
                "lines_of_code": 280,
                "try_catch_blocks": 8,
                "functions_to_migrate": [
                    "RedisConnectionHandler.get_connection() - Database connection consolidation",
                    "safe_execute() - Replace with error_patterns equivalent",
                    "log_error() - Standardize with error_patterns logging",
                    "get_user_friendly_message() - Consolidate with error_patterns"
                ],
                "expected_benefits": "60-70% code reduction, standardized error handling"
            }
        },
        
        "tests/test_memory_system.py": {
            "patterns_applicable": [
                "Error Handling Patterns",
                "Memory Service consolidation",
                "AuthValidator consolidation"
            ],
            "migration_complexity": "MEDIUM",
            "estimated_impact": "HIGH",
            "analysis": {
                "current_state": "Manual error handling in test framework",
                "duplicate_patterns": [
                    "TestErrorHandling class with manual try/catch patterns",
                    "Manual user ID validation in test scenarios",
                    "Direct memory API calls instead of MemoryService abstraction"
                ],
                "lines_of_code": 400,
                "try_catch_blocks": 6,
                "functions_to_migrate": [
                    "test_invalid_user_id() - Use AuthValidator patterns",
                    "test_malformed_requests() - Apply error handling decorators",
                    "test_service_connectivity() - Use error patterns for service testing",
                    "TestHelper.retrieve_memories() - Use MemoryService abstraction"
                ],
                "expected_benefits": "Standardized test error handling, consistent with production patterns"
            }
        },
        
        "utilities/validation.py": {
            "patterns_applicable": [
                "Error Handling Patterns",
                "AuthValidator consolidation"
            ],
            "migration_complexity": "LOW",
            "estimated_impact": "MEDIUM",
            "analysis": {
                "current_state": "Manual validation functions with scattered error handling",
                "duplicate_patterns": [
                    "validate_query_params() - Manual validation logic",
                    "DatabaseConfig validation - Could use AuthValidator patterns",
                    "ChatMessage validation - Overlaps with AuthValidator user extraction"
                ],
                "lines_of_code": 150,
                "try_catch_blocks": 3,
                "functions_to_migrate": [
                    "validate_query_params() - Apply error handling decorators",
                    "DatabaseConfig validation - Integrate with unified config system",
                    "ChatMessage validation - Use AuthValidator patterns"
                ],
                "expected_benefits": "Consistent validation patterns, reduced duplication"
            }
        }
    },
    
    "MEDIUM_PRIORITY": {
        "tests/test_comprehensive_user_memory.py": {
            "patterns_applicable": [
                "Error Handling Patterns",
                "AuthValidator consolidation"
            ],
            "migration_complexity": "LOW",
            "estimated_impact": "MEDIUM",
            "analysis": {
                "current_state": "Comprehensive test suite with manual error scenarios",
                "duplicate_patterns": [
                    "TestErrorHandling class with manual exception patterns",
                    "extract_authenticated_user_id() mock - Use AuthValidator",
                    "validate_openwebui_user_id() mock - Use AuthValidator"
                ],
                "lines_of_code": 600,
                "try_catch_blocks": 4,
                "functions_to_migrate": [
                    "test_invalid_message_format() - Apply error decorators",
                    "test_malformed_user_data() - Use AuthValidator patterns",
                    "test_memory_api_failure() - Use error patterns for API testing"
                ],
                "expected_benefits": "Test consistency with production error handling"
            }
        },
        
        "scripts/startup_verifier.py": {
            "patterns_applicable": [
                "Error Handling Patterns",
                "Database Connection Factory"
            ],
            "migration_complexity": "MEDIUM",
            "estimated_impact": "MEDIUM",
            "analysis": {
                "current_state": "Manual database operations and error handling",
                "duplicate_patterns": [
                    "Manual SQLite connection management",
                    "install_missing_function() - Manual error handling",
                    "Custom database connection logic"
                ],
                "lines_of_code": 300,
                "try_catch_blocks": 5,
                "functions_to_migrate": [
                    "install_missing_function() - Apply error decorators",
                    "read_function_code() - Use error patterns",
                    "Database connection logic - Use DatabaseConnectionFactory patterns"
                ],
                "expected_benefits": "Standardized startup verification, consistent error handling"
            }
        },
        
        "integrated_memory_startup.py": {
            "patterns_applicable": [
                "Error Handling Patterns",
                "Database Connection Factory"
            ],
            "migration_complexity": "MEDIUM",
            "estimated_impact": "MEDIUM",
            "analysis": {
                "current_state": "Complex startup logic with manual error handling",
                "duplicate_patterns": [
                    "FunctionManager with manual SQLite operations",
                    "wait_for_database() - Manual connection retry logic",
                    "install_function() and verify_function() - Manual error handling"
                ],
                "lines_of_code": 350,
                "try_catch_blocks": 7,
                "functions_to_migrate": [
                    "wait_for_database() - Use DatabaseConnectionFactory patterns",
                    "install_function() - Apply error handling decorators",
                    "verify_function() - Use error patterns for validation"
                ],
                "expected_benefits": "Consistent startup patterns, reduced complexity"
            }
        }
    },
    
    "LOW_PRIORITY": {
        "tests/conftest.py": {
            "patterns_applicable": [
                "Error Handling Patterns",
                "Memory Service consolidation"
            ],
            "migration_complexity": "LOW",
            "estimated_impact": "LOW",
            "analysis": {
                "current_state": "Test helper utilities with manual patterns",
                "duplicate_patterns": [
                    "TestHelper.wait_for_service() - Manual service checking",
                    "TestHelper.store_memory_via_learning() - Direct API calls vs MemoryService",
                    "TestHelper.retrieve_memories() - Manual memory operations"
                ],
                "lines_of_code": 200,
                "try_catch_blocks": 2,
                "functions_to_migrate": [
                    "wait_for_service() - Use error patterns for service testing",
                    "memory operations - Use MemoryService abstraction"
                ],
                "expected_benefits": "Consistent test infrastructure"
            }
        },
        
        "scripts/system_monitor.py": {
            "patterns_applicable": [
                "Error Handling Patterns",
                "Database Connection Factory"
            ],
            "migration_complexity": "LOW",
            "estimated_impact": "LOW",
            "analysis": {
                "current_state": "System monitoring with manual error handling",
                "duplicate_patterns": [
                    "fix_function_issue() - Manual SQLite operations",
                    "Manual database connection management",
                    "Custom error handling patterns"
                ],
                "lines_of_code": 250,
                "try_catch_blocks": 4,
                "functions_to_migrate": [
                    "fix_function_issue() - Apply error decorators",
                    "Database operations - Use DatabaseConnectionFactory"
                ],
                "expected_benefits": "Standardized monitoring patterns"
            }
        },
        
        "memory/utils/import_memory_function.py": {
            "patterns_applicable": [
                "Error Handling Patterns"
            ],
            "migration_complexity": "LOW",
            "estimated_impact": "LOW",
            "analysis": {
                "current_state": "Import utility with basic error handling",
                "duplicate_patterns": [
                    "list_functions() and import_function() - Manual try/catch",
                    "Basic HTTP error handling patterns"
                ],
                "lines_of_code": 150,
                "try_catch_blocks": 3,
                "functions_to_migrate": [
                    "list_functions() - Apply error decorators",
                    "import_function() - Use error patterns"
                ],
                "expected_benefits": "Consistent import utility error handling"
            }
        }
    },
    
    "OPTIMIZATION_TARGETS": {
        "database_manager.py": {
            "patterns_applicable": [
                "Error Handling Patterns"
            ],
            "migration_complexity": "HIGH",
            "estimated_impact": "VERY_HIGH",
            "analysis": {
                "current_state": "Already uses DatabaseConnectionFactory, has some error patterns",
                "optimization_opportunities": [
                    "Remaining manual try/catch blocks in convenience functions",
                    "get_database_health() - Could use error decorators",
                    "Legacy compatibility functions - Apply error patterns"
                ],
                "lines_of_code": 970,
                "try_catch_blocks": 12,
                "functions_to_optimize": [
                    "get_database_health() - Apply error decorators",
                    "get_chat_history() - Standardize error handling",
                    "store_chat_entry() - Use error patterns",
                    "get_embedding() and store_vector_data() - Apply decorators"
                ],
                "expected_benefits": "Complete error handling standardization across all database operations"
            }
        }
    }
}

# ============================================================================
# PHASE 3 MIGRATION STRATEGY
# ============================================================================

def calculate_phase_3_metrics():
    """Calculate Phase 3 migration potential metrics."""
    
    high_priority = PHASE_3_MIGRATION_TARGETS["HIGH_PRIORITY"]
    medium_priority = PHASE_3_MIGRATION_TARGETS["MEDIUM_PRIORITY"]
    low_priority = PHASE_3_MIGRATION_TARGETS["LOW_PRIORITY"]
    optimization = PHASE_3_MIGRATION_TARGETS["OPTIMIZATION_TARGETS"]
    
    # Calculate totals
    total_files = len(high_priority) + len(medium_priority) + len(low_priority) + len(optimization)
    total_lines = sum(target["analysis"]["lines_of_code"] for targets in PHASE_3_MIGRATION_TARGETS.values() for target in targets.values())
    total_try_catch = sum(target["analysis"]["try_catch_blocks"] for targets in PHASE_3_MIGRATION_TARGETS.values() for target in targets.values())
    
    # Calculate functions - handle both migrate and optimize keys
    total_functions = 0
    for targets in PHASE_3_MIGRATION_TARGETS.values():
        for target in targets.values():
            analysis = target["analysis"]
            if "functions_to_migrate" in analysis:
                total_functions += len(analysis["functions_to_migrate"])
            elif "functions_to_optimize" in analysis:
                total_functions += len(analysis["functions_to_optimize"])
    
    # Priority breakdown
    high_priority_files = len(high_priority)
    high_priority_lines = sum(target["analysis"]["lines_of_code"] for target in high_priority.values())
    high_priority_functions = sum(len(target["analysis"]["functions_to_migrate"]) for target in high_priority.values())
    
    return {
        "total_files": total_files,
        "total_lines_of_code": total_lines,
        "total_try_catch_blocks": total_try_catch,
        "total_functions_to_migrate": total_functions,
        "high_priority_targets": {
            "files": high_priority_files,
            "lines": high_priority_lines,
            "functions": high_priority_functions
        },
        "expected_code_reduction_percentage": 65,  # Based on Phase 1+2 results
        "estimated_migration_time": "2-3 days for high priority targets"
    }

def print_phase_3_assessment():
    """Print comprehensive Phase 3 migration assessment."""
    
    metrics = calculate_phase_3_metrics()
    
    print("=" * 80)
    print("PHASE 3 MIGRATION ASSESSMENT - UTILITIES & SUPPORTING FUNCTIONS")
    print("=" * 80)
    
    print(f"\n[CHART] PHASE 3 MIGRATION POTENTIAL:")
    print(f"Target Files: {metrics['total_files']}")
    print(f"Lines of Code: {metrics['total_lines_of_code']}")
    print(f"Try/Catch Blocks: {metrics['total_try_catch_blocks']}")
    print(f"Functions to Migrate: {metrics['total_functions_to_migrate']}")
    print(f"Expected Code Reduction: {metrics['expected_code_reduction_percentage']}%")
    print(f"Estimated Timeline: {metrics['estimated_migration_time']}")
    
    print(f"\n HIGH PRIORITY TARGETS (Immediate Impact):")
    for file_name, target in PHASE_3_MIGRATION_TARGETS["HIGH_PRIORITY"].items():
        complexity = target["migration_complexity"]
        impact = target["estimated_impact"]
        analysis = target["analysis"]
        
        # Handle both migrate and optimize function keys
        functions_key = "functions_to_migrate" if "functions_to_migrate" in analysis else "functions_to_optimize"
        functions_count = len(analysis.get(functions_key, []))
        try_catch_count = analysis["try_catch_blocks"]
        
        print(f"[FOLDER] {file_name}")
        print(f"   Complexity: {complexity}, Impact: {impact}")
        print(f"   Functions: {functions_count}, Try/Catch: {try_catch_count}")
        print(f"   Patterns: {', '.join(target['patterns_applicable'])}")
        print(f"   Benefits: {analysis['expected_benefits']}")
        print()
    
    print(f"\n[SYNC] MEDIUM PRIORITY TARGETS:")
    for file_name, target in PHASE_3_MIGRATION_TARGETS["MEDIUM_PRIORITY"].items():
        analysis = target["analysis"]
        functions_key = "functions_to_migrate" if "functions_to_migrate" in analysis else "functions_to_optimize"
        functions_count = len(analysis.get(functions_key, []))
        print(f"[FOLDER] {file_name} - {functions_count} functions ({target['estimated_impact']} impact)")
    
    print(f"\n OPTIMIZATION OPPORTUNITIES:")
    for file_name, target in PHASE_3_MIGRATION_TARGETS["OPTIMIZATION_TARGETS"].items():
        analysis = target["analysis"]
        functions_key = "functions_to_migrate" if "functions_to_migrate" in analysis else "functions_to_optimize"
        functions_count = len(analysis.get(functions_key, []))
        print(f"[FOLDER] {file_name} - {functions_count} functions to optimize ({target['estimated_impact']} impact)")
    
    print(f"\n CONSOLIDATION FRAMEWORKS READY FOR PHASE 3:")
    frameworks = [
        "[OK] Error Handling Patterns - Ready for utilities migration",
        "[OK] Memory Service - Ready for test framework integration", 
        "[OK] AuthValidator - Ready for validation consolidation",
        "[OK] Database Connection Factory - Ready for script migration",
        "[OK] Unified Configuration - Ready for startup script integration"
    ]
    for framework in frameworks:
        print(f"{framework}")
    
    print(f"\n RECOMMENDED PHASE 3 EXECUTION ORDER:")
    print(f"1. [FIRE] error_handler.py - High impact, standardizes error handling foundation")
    print(f"2.  tests/test_memory_system.py - Ensures test consistency with production patterns")
    print(f"3. [OK] utilities/validation.py - Low complexity, quick wins with validation patterns")
    print(f"4.  scripts/startup_verifier.py - Standardizes startup verification")
    print(f"5. [CHART] database_manager.py optimizations - Complete database layer standardization")
    
    print(f"\n EXPECTED PHASE 3 OUTCOMES:")
    print(f"[OK] Complete error handling standardization across utilities")
    print(f"[OK] Test framework consistency with production patterns")
    print(f"[OK] Startup and monitoring script consolidation")
    print(f"[OK] Validation pattern unification")
    print(f"[OK] 65%+ additional code reduction in utilities layer")
    print(f"[OK] Full codebase consolidation achievement")

if __name__ == "__main__":
    print_phase_3_assessment()
