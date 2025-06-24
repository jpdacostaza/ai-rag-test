#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows-compatible debug tool with Unicode fixes applied
"""
import sys
import os

# Set UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except AttributeError:
        pass  # Already wrapped or not available

"""
Comprehensive Debug Tools Runner
Runs all debug tools and captures their output for investigation.
"""

import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path

class DebugToolsRunner:
    def __init__(self):
        self.reports_dir = Path("reports/debug-results")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {}
        
    def run_tool(self, tool_path, tool_name, description=""):
        """Run a debug tool and capture its output"""
        print(f"\n{'='*60}")
        print(f"[TOOL] Running: {tool_name}")
        print(f"[NOTE] Description: {description}")
        print(f"[FOLDER] Path: {tool_path}")
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
                # Run the tool
                process = subprocess.run(
                    [sys.executable, tool_path],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                result = {
                    "status": "SUCCESS" if process.returncode == 0 else "FAILED",
                    "return_code": process.returncode,
                    "output": process.stdout,
                    "stderr": process.stderr,
                    "timestamp": datetime.now().isoformat()
                }
                
                if process.returncode == 0:
                    print(f"[OK] {tool_name} completed successfully")
                else:
                    print(f"[FAIL] {tool_name} failed with return code {process.returncode}")
                    
            except subprocess.TimeoutExpired:
                result = {
                    "status": "TIMEOUT",
                    "error": "Tool execution timed out after 5 minutes",
                    "output": "",
                    "stderr": ""
                }
                print(f"[TIMEOUT] {tool_name} timed out")
                
            except Exception as e:
                result = {
                    "status": "ERROR",
                    "error": str(e),
                    "output": "",
                    "stderr": ""
                }
                print(f"[ERROR] {tool_name} crashed: {e}")
        
        # Save individual report
        report_file = self.reports_dir / f"{tool_name.replace(' ', '_').lower()}_{self.timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"Debug Tool Report: {tool_name}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Tool Path: {tool_path}\n")
            f.write(f"Description: {description}\n")
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
        
    def run_all_tools(self):
        """Run all available debug tools"""
        print(f"[START] Starting comprehensive debug tools test run at {datetime.now()}")
        print(f"[DATA] Results will be saved to: {self.reports_dir}")
        
        # Define all debug tools to run
        tools = [
            {
                "path": "debug/utilities/endpoint_validator.py",
                "name": "Endpoint Validator",
                "description": "Validates backend API endpoints and connectivity"
            },
            {
                "path": "debug/utilities/debug_endpoints.py", 
                "name": "Debug Endpoints",
                "description": "Debug endpoint testing and validation"
            },
            {
                "path": "debug/utilities/verify_memory_pipeline.py",
                "name": "Memory Pipeline Verifier",
                "description": "Verifies memory pipeline functionality"
            },
            {
                "path": "debug/memory-tests/comprehensive_memory_test.py",
                "name": "Comprehensive Memory Test",
                "description": "Comprehensive memory system testing"
            },
            {
                "path": "debug/memory-tests/test_openwebui_memory.py",
                "name": "OpenWebUI Memory Test",
                "description": "OpenWebUI memory integration testing"
            },
            {
                "path": "debug/memory-tests/test_openwebui_memory_fixed.py",
                "name": "OpenWebUI Memory Test (Fixed)",
                "description": "Fixed version of OpenWebUI memory testing"
            },
            {
                "path": "debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py",
                "name": "Memory Diagnostic Tool",
                "description": "Advanced memory diagnostic and troubleshooting"
            },
            {
                "path": "debug/archived/demo-test/debug-tools/test_memory_cross_chat.py",
                "name": "Cross-Chat Memory Test",
                "description": "Tests memory persistence across chat sessions"
            }
        ]
        
        # Run each tool
        for tool in tools:
            self.run_tool(tool["path"], tool["name"], tool["description"])
            
        # Generate summary report
        self.generate_summary_report()
        
    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        summary_file = self.reports_dir / f"debug_tools_summary_{self.timestamp}.json"
        summary_text_file = self.reports_dir / f"debug_tools_summary_{self.timestamp}.txt"
        
        # JSON summary
        summary_data = {
            "timestamp": datetime.now().isoformat(),
            "total_tools": len(self.results),
            "successful": len([r for r in self.results.values() if r['status'] == 'SUCCESS']),
            "failed": len([r for r in self.results.values() if r['status'] == 'FAILED']),
            "errors": len([r for r in self.results.values() if r['status'] == 'ERROR']),
            "timeouts": len([r for r in self.results.values() if r['status'] == 'TIMEOUT']),
            "results": self.results
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)
            
        # Text summary
        with open(summary_text_file, 'w', encoding='utf-8') as f:
            f.write("DEBUG TOOLS COMPREHENSIVE TEST REPORT\n")
            f.write("="*50 + "\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Total Tools Tested: {summary_data['total_tools']}\n")
            f.write(f"[OK] Successful: {summary_data['successful']}\n")
            f.write(f"[FAIL] Failed: {summary_data['failed']}\n")
            f.write(f"[ERROR] Errors: {summary_data['errors']}\n")
            f.write(f"[TIMEOUT] Timeouts: {summary_data['timeouts']}\n")
            f.write("\n" + "="*50 + "\n\n")
            
            f.write("DETAILED RESULTS:\n")
            f.write("-"*30 + "\n")
            for tool_name, result in self.results.items():
                status_icon = {
                    'SUCCESS': '[OK]',
                    'FAILED': '[FAIL]', 
                    'ERROR': '[ERROR]',
                    'TIMEOUT': '[TIMEOUT]'
                }.get(result['status'], '❓')
                
                f.write(f"{status_icon} {tool_name}: {result['status']}\n")
                if result.get('error'):
                    f.write(f"   Error: {result['error']}\n")
                f.write("\n")
                
        print(f"\n[DATA] Summary reports generated:")
        print(f"   [PAGE] JSON: {summary_file}")
        print(f"   [PAGE] Text: {summary_text_file}")
        
        # Print console summary
        print(f"\n{'='*60}")
        print("[TARGET] DEBUG TOOLS TEST SUMMARY")
        print(f"{'='*60}")
        print(f"[OK] Successful: {summary_data['successful']}")
        print(f"[FAIL] Failed: {summary_data['failed']}")
        print(f"[ERROR] Errors: {summary_data['errors']}")
        print(f"[TIMEOUT] Timeouts: {summary_data['timeouts']}")
        print(f"[DATA] Total: {summary_data['total_tools']}")
        print(f"{'='*60}")

if __name__ == "__main__":
    runner = DebugToolsRunner()
    runner.run_all_tools()
