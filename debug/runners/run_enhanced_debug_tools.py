#!/usr/bin/env python3
"""
Enhanced Debug Tools Runner with Better Diagnostics
Addresses the issues identified in Phase 1 and implements Phase 2 improvements.
"""

import subprocess
import sys
import os
import json
import requests
import time
from datetime import datetime
from pathlib import Path

class EnhancedDebugToolsRunner:
    def __init__(self):
        self.reports_dir = Path("../reports/debug-results")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {}
        self.backend_status = None
        self.openwebui_status = None
        
    def check_service_health(self):
        """Phase 2: Check backend and OpenWebUI service availability"""
        print("[TARGET] Phase 2: Checking Service Health")
        print("="*60)
        
        # Check backend (port 8001)
        try:
            response = requests.get('http://localhost:8001/health', timeout=5)
            if response.status_code == 200:
                self.backend_status = "RUNNING"
                print("[OK] Backend service: RUNNING on port 8001")
            else:
                self.backend_status = "ERROR"
                print(f"[FAIL] Backend service: HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.backend_status = "NOT_RUNNING"
            print("[FAIL] Backend service: NOT RUNNING on port 8001")
        except Exception as e:
            self.backend_status = "ERROR"
            print(f"[ERROR] Backend service: {e}")
        
        # Check OpenWebUI (port 3000)
        try:
            response = requests.get('http://localhost:3000/', timeout=5)
            if response.status_code == 200:
                self.openwebui_status = "RUNNING"
                print("[OK] OpenWebUI service: RUNNING on port 3000")
            else:
                self.openwebui_status = "ERROR"
                print(f"[FAIL] OpenWebUI service: HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.openwebui_status = "NOT_RUNNING"
            print("[FAIL] OpenWebUI service: NOT RUNNING on port 3000")
        except Exception as e:
            self.openwebui_status = "ERROR"
            print(f"[ERROR] OpenWebUI service: {e}")
        
        print("="*60)
        
    def categorize_tools_by_requirements(self):
        """Categorize tools based on their service requirements"""
        return {
            "backend_only": [
                {
                    "path": "../utilities/endpoint_validator.py",
                    "name": "Endpoint Validator",
                    "description": "Validates backend API endpoints (backend only)",
                    "requirements": ["backend"]
                },
                {
                    "path": "../utilities/debug_endpoints.py", 
                    "name": "Debug Endpoints",
                    "description": "Debug endpoint testing (backend only)",
                    "requirements": ["backend"]
                },
                {
                    "path": "../utilities/verify_memory_pipeline.py",
                    "name": "Memory Pipeline Verifier",
                    "description": "Verifies memory pipeline (backend only)",
                    "requirements": ["backend"]
                },
                {
                    "path": "../memory-tests/comprehensive_memory_test.py",
                    "name": "Comprehensive Memory Test",
                    "description": "Memory system testing (backend only)",
                    "requirements": ["backend"]
                }
            ],
            "full_stack": [
                {
                    "path": "../memory-tests/test_openwebui_memory.py",
                    "name": "OpenWebUI Memory Test",
                    "description": "OpenWebUI integration testing (needs OpenWebUI + backend)",
                    "requirements": ["backend", "openwebui"]
                },
                {
                    "path": "../memory-tests/test_openwebui_memory_fixed.py",
                    "name": "OpenWebUI Memory Test (Fixed)",
                    "description": "Fixed OpenWebUI testing (needs OpenWebUI + backend)",
                    "requirements": ["backend", "openwebui"]
                },
                {
                    "path": "../archived/demo-test/debug-tools/simplified_memory_diagnostic.py",
                    "name": "Memory Diagnostic Tool",
                    "description": "Advanced memory diagnostic (needs OpenWebUI + backend)",
                    "requirements": ["backend", "openwebui"]
                },
                {
                    "path": "../archived/demo-test/debug-tools/simplified_cross_chat_test.py",
                    "name": "Cross-Chat Memory Test",
                    "description": "Cross-session memory testing (needs OpenWebUI + backend)",
                    "requirements": ["backend", "openwebui"]
                }
            ]
        }
    
    def should_run_tool(self, requirements):
        """Determine if a tool should run based on service availability"""
        if "backend" in requirements and self.backend_status != "RUNNING":
            return False, "Backend service not available"
        if "openwebui" in requirements and self.openwebui_status != "RUNNING":
            return False, "OpenWebUI service not available"
        return True, "All requirements met"
    
    def run_tool_enhanced(self, tool_info):
        """Enhanced tool runner with better diagnostics"""
        tool_path = tool_info["path"]
        tool_name = tool_info["name"]
        description = tool_info["description"]
        requirements = tool_info["requirements"]
        
        print(f"\n{'='*60}")
        print(f"[TOOL] Running: {tool_name}")
        print(f"[NOTE] Description: {description}")
        print(f"[FOLDER] Path: {tool_path}")
        print(f"[DATA] Requirements: {', '.join(requirements)}")
        
        # Check if tool should run
        should_run, reason = self.should_run_tool(requirements)
        if not should_run:
            result = {
                "status": "SKIPPED",
                "reason": reason,
                "requirements": requirements,
                "output": "",
                "stderr": ""
            }
            print(f"[SEARCH] SKIPPED: {reason}")
            print(f"{'='*60}")
            self.results[tool_name] = result
            return result
        
        print(f"{'='*60}")
        
        if not os.path.exists(tool_path):
            result = {
                "status": "ERROR",
                "error": f"Tool not found: {tool_path}",
                "output": "",
                "stderr": ""
            }
            print(f"[FAIL] Tool not found: {tool_path}")
        else:
            try:
                # Run the tool with enhanced output capture
                process = subprocess.run(
                    [sys.executable, tool_path],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    encoding='utf-8',
                    errors='replace'  # Handle encoding issues gracefully
                )
                
                result = {
                    "status": "SUCCESS" if process.returncode == 0 else "FAILED",
                    "return_code": process.returncode,
                    "output": process.stdout,
                    "stderr": process.stderr,
                    "timestamp": datetime.now().isoformat(),
                    "requirements": requirements
                }
                
                if process.returncode == 0:
                    print(f"[OK] {tool_name} completed successfully")
                    # Phase 2: Show actual output for successful tools
                    if process.stdout.strip():
                        print(f"[DATA] Tool output preview:")
                        preview_lines = process.stdout.strip().split('\n')[:5]
                        for line in preview_lines:
                            print(f"      {line}")
                        if len(process.stdout.strip().split('\n')) > 5:
                            print(f"      ... ({len(process.stdout.strip().split('\n')) - 5} more lines)")
                else:
                    print(f"[FAIL] {tool_name} failed with return code {process.returncode}")
                    # Show error preview
                    if process.stderr.strip():
                        print(f"[ERROR] Error preview:")
                        error_lines = process.stderr.strip().split('\n')[:3]
                        for line in error_lines:
                            print(f"       {line}")
                    
            except subprocess.TimeoutExpired:
                result = {
                    "status": "TIMEOUT",
                    "error": "Tool execution timed out after 5 minutes",
                    "output": "",
                    "stderr": "",
                    "requirements": requirements
                }
                print(f"[TIMEOUT] {tool_name} timed out")
                
            except Exception as e:
                result = {
                    "status": "ERROR",
                    "error": str(e),
                    "output": "",
                    "stderr": "",
                    "requirements": requirements
                }
                print(f"[ERROR] {tool_name} crashed: {e}")
        
        # Save individual report (same as before)
        report_file = self.reports_dir / f"{tool_name.replace(' ', '_').lower()}_{self.timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"Debug Tool Report: {tool_name}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Tool Path: {tool_path}\n")
            f.write(f"Description: {description}\n")
            f.write(f"Requirements: {', '.join(requirements)}\n")
            f.write(f"Status: {result['status']}\n")
            f.write("="*80 + "\n\n")
            
            if result.get('output'):
                f.write("STDOUT:\n")
                f.write("-"*40 + "\n")
                f.write(result['output'])
                f.write("\n\n")
                
            if result.get('stderr'):
                f.write("STDERR:\n")
                f.write("-"*40 + "\n")
                f.write(result['stderr'])
                f.write("\n\n")
                
            if result.get('error'):
                f.write("ERROR:\n")
                f.write("-"*40 + "\n")
                f.write(result['error'])
                f.write("\n\n")
        
        self.results[tool_name] = result
        return result
    
    def run_all_tools_enhanced(self):
        """Enhanced version implementing Phase 2 improvements"""
        print(f"[START] Enhanced Debug Tools Test Run - {datetime.now()}")
        print(f"[DATA] Results will be saved to: {self.reports_dir}")
        
        # Phase 2: Check service health first
        self.check_service_health()
        
        # Categorize tools by requirements
        tool_categories = self.categorize_tools_by_requirements()
        
        print(f"\n[TARGET] Phase 2: Running Tools by Category")
        print("="*60)
        
        # Run backend-only tools first
        print(f"\n[BRAIN] CATEGORY 1: Backend-Only Tools")
        print("-"*40)
        for tool_info in tool_categories["backend_only"]:
            self.run_tool_enhanced(tool_info)
        
        # Run full-stack tools
        print(f"\n[BRAIN] CATEGORY 2: Full-Stack Tools (Backend + OpenWebUI)")
        print("-"*40)
        for tool_info in tool_categories["full_stack"]:
            self.run_tool_enhanced(tool_info)
        
        # Generate enhanced summary
        self.generate_enhanced_summary()
    
    def generate_enhanced_summary(self):
        """Generate enhanced summary with Phase 2 improvements"""
        summary_file = self.reports_dir / f"enhanced_debug_summary_{self.timestamp}.json"
        summary_text_file = self.reports_dir / f"enhanced_debug_summary_{self.timestamp}.txt"
        
        # Enhanced JSON summary
        summary_data = {
            "timestamp": datetime.now().isoformat(),
            "service_status": {
                "backend": self.backend_status,
                "openwebui": self.openwebui_status
            },
            "total_tools": len(self.results),
            "successful": len([r for r in self.results.values() if r['status'] == 'SUCCESS']),
            "failed": len([r for r in self.results.values() if r['status'] == 'FAILED']),
            "errors": len([r for r in self.results.values() if r['status'] == 'ERROR']),
            "skipped": len([r for r in self.results.values() if r['status'] == 'SKIPPED']),
            "timeouts": len([r for r in self.results.values() if r['status'] == 'TIMEOUT']),
            "results": self.results
        }
        
        # Save JSON
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)
        
        # Enhanced text summary
        with open(summary_text_file, 'w', encoding='utf-8') as f:
            f.write("ENHANCED DEBUG TOOLS COMPREHENSIVE TEST REPORT\n")
            f.write("="*60 + "\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Backend Status: {self.backend_status}\n")
            f.write(f"OpenWebUI Status: {self.openwebui_status}\n")
            f.write(f"Total Tools Tested: {summary_data['total_tools']}\n")
            f.write(f"[OK] Successful: {summary_data['successful']}\n")
            f.write(f"[FAIL] Failed: {summary_data['failed']}\n")
            f.write(f"[ERROR] Errors: {summary_data['errors']}\n")
            f.write(f"[SEARCH] Skipped: {summary_data['skipped']}\n")
            f.write(f"[TIMEOUT] Timeouts: {summary_data['timeouts']}\n")
            f.write("\n" + "="*60 + "\n\n")
            
            f.write("DETAILED RESULTS BY CATEGORY:\n")
            f.write("-"*40 + "\n")
            
            backend_tools = ["Endpoint Validator", "Debug Endpoints", "Memory Pipeline Verifier", "Comprehensive Memory Test"]
            fullstack_tools = ["OpenWebUI Memory Test", "OpenWebUI Memory Test (Fixed)", "Memory Diagnostic Tool", "Cross-Chat Memory Test"]
            
            f.write("Backend-Only Tools:\n")
            for tool_name in backend_tools:
                if tool_name in self.results:
                    result = self.results[tool_name]
                    status_icon = {'SUCCESS': '[OK]', 'FAILED': '[FAIL]', 'ERROR': '[ERROR]', 'TIMEOUT': '[TIMEOUT]', 'SKIPPED': '[SKIP]'}.get(result['status'], '[?]')
                    f.write(f"  {status_icon} {tool_name}: {result['status']}\n")
                    if result.get('reason'):
                        f.write(f"      Reason: {result['reason']}\n")
            
            f.write("\nFull-Stack Tools:\n")
            for tool_name in fullstack_tools:
                if tool_name in self.results:
                    result = self.results[tool_name]
                    status_icon = {'SUCCESS': '[OK]', 'FAILED': '[FAIL]', 'ERROR': '[ERROR]', 'TIMEOUT': '[TIMEOUT]', 'SKIPPED': '[SKIP]'}.get(result['status'], '[?]')
                    f.write(f"  {status_icon} {tool_name}: {result['status']}\n")
                    if result.get('reason'):
                        f.write(f"      Reason: {result['reason']}\n")
                        
        print(f"\n[DATA] Enhanced summary reports generated:")
        print(f"   [PAGE] JSON: {summary_file}")
        print(f"   [PAGE] Text: {summary_text_file}")
        
        # Enhanced console summary
        print(f"\n{'='*60}")
        print("[TARGET] ENHANCED DEBUG TOOLS SUMMARY")
        print(f"{'='*60}")
        print(f"[BRAIN] Backend Status: {self.backend_status}")
        print(f"[BRAIN] OpenWebUI Status: {self.openwebui_status}")
        print(f"[OK] Successful: {summary_data['successful']}")
        print(f"[FAIL] Failed: {summary_data['failed']}")
        print(f"[ERROR] Errors: {summary_data['errors']}")
        print(f"[SEARCH] Skipped: {summary_data['skipped']}")
        print(f"[TIMEOUT] Timeouts: {summary_data['timeouts']}")
        print(f"[DATA] Total: {summary_data['total_tools']}")
        print(f"{'='*60}")

if __name__ == "__main__":
    runner = EnhancedDebugToolsRunner()
    runner.run_all_tools_enhanced()
