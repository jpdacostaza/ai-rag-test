#!/usr/bin/env python3
"""
Comprehensive Test Suite for Unified Memory Installer
==================================================

This script tests all installation methods to ensure reliability.
"""

import asyncio
import time
import json
import os
import shutil
import requests
import subprocess
from pathlib import Path

class InstallerTester:
    def __init__(self):
        self.test_results = {
            "function_methods": {},
            "pipeline_methods": {},
            "overall_status": "PENDING"
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp and color coding."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        emoji = {
            "INFO": "📝",
            "SUCCESS": "✅", 
            "ERROR": "❌",
            "WARNING": "⚠️",
            "TEST": "🧪"
        }.get(level, "📝")
        print(f"[{timestamp}] {emoji} [{level}] [InstallerTest] {message}")
    
    def test_function_volume_mount(self) -> bool:
        """Test Method 1: Direct volume mount installation for functions."""
        self.log("Testing Function Method 1: Direct volume mount installation...", "TEST")
        
        try:
            # Create test function content
            test_content = '''# Test Enhanced Memory Function
print("Function installed successfully via volume mount")
'''
            
            # Test directory access
            test_dir = "/app/backend/data/functions"
            if os.path.exists(test_dir):
                test_file = os.path.join(test_dir, "test_function_volume.py")
                
                # Write test file
                with open(test_file, "w", encoding='utf-8') as f:
                    f.write(test_content)
                
                # Verify file exists and has content
                if os.path.exists(test_file) and os.path.getsize(test_file) > 0:
                    self.log("✅ Function Volume Mount: PASS", "SUCCESS")
                    # Cleanup
                    os.remove(test_file)
                    return True
            else:
                self.log(f"⚠️ Function Volume Mount: Directory {test_dir} not accessible", "WARNING")
                
        except Exception as e:
            self.log(f"❌ Function Volume Mount: FAIL - {e}", "ERROR")
        
        return False
    
    def test_function_docker_cp(self) -> bool:
        """Test Method 2: Docker cp installation for functions."""
        self.log("Testing Function Method 2: Docker cp installation...", "TEST")
        
        try:
            # Create test function content
            test_content = '''# Test Enhanced Memory Function
print("Function installed successfully via docker cp")
'''
            
            # Write to temporary location
            temp_file = "/tmp/test_function_docker.py"
            with open(temp_file, "w", encoding='utf-8') as f:
                f.write(test_content)
            
            # Test docker cp command
            copy_cmd = [
                "docker", "cp", 
                temp_file, 
                "backend-openwebui:/app/backend/data/functions/test_function_docker.py"
            ]
            
            result = subprocess.run(copy_cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                self.log("✅ Function Docker CP: PASS", "SUCCESS")
                
                # Cleanup - remove test file from container
                cleanup_cmd = ["docker", "exec", "backend-openwebui", "rm", "-f", "/app/backend/data/functions/test_function_docker.py"]
                subprocess.run(cleanup_cmd, capture_output=True, text=True, timeout=10)
                
                # Cleanup local temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                return True
            else:
                self.log(f"❌ Function Docker CP: FAIL - {result.stderr}", "ERROR")
                
        except subprocess.TimeoutExpired:
            self.log("❌ Function Docker CP: FAIL - Timeout", "ERROR")
        except Exception as e:
            self.log(f"❌ Function Docker CP: FAIL - {e}", "ERROR")
        
        return False
    
    def test_function_api(self) -> bool:
        """Test Method 3: API-based installation for functions."""
        self.log("Testing Function Method 3: API-based installation...", "TEST")
        
        try:
            import httpx
            
            # Try different API endpoints
            api_endpoints = [
                "http://openwebui:8080/api/v1/functions",
                "http://openwebui:8080/api/functions",
                "http://localhost:8080/api/v1/functions"
            ]
            
            test_function_data = {
                "id": "test_function_api",
                "name": "Test Function API",
                "type": "filter",
                "content": "# Test function for API installation",
                "is_active": True,
                "is_global": True
            }
            
            with httpx.Client(timeout=10.0) as client:
                for endpoint in api_endpoints:
                    try:
                        response = client.post(endpoint, json=test_function_data)
                        if response.status_code in [200, 201]:
                            self.log("✅ Function API: PASS", "SUCCESS")
                            return True
                    except Exception as e:
                        continue
            
            self.log("⚠️ Function API: Not available (expected for current OpenWebUI version)", "WARNING")
            return False
            
        except Exception as e:
            self.log(f"❌ Function API: FAIL - {e}", "ERROR")
            return False
    
    def test_pipeline_volume_mount(self) -> bool:
        """Test Method 1: Direct volume mount installation for pipelines."""
        self.log("Testing Pipeline Method 1: Direct volume mount installation...", "TEST")
        
        try:
            # Create test pipeline content
            test_content = '''# Test Enhanced Memory Pipeline
class Pipeline:
    def __init__(self):
        self.id = "test_pipeline"
        self.name = "Test Pipeline"
    
    def pipe(self, user_message, model_id, messages, body):
        return body
'''
            
            # Test directory access
            test_dir = "/app/pipelines"
            os.makedirs(test_dir, exist_ok=True)
            
            test_file = os.path.join(test_dir, "test_pipeline_volume.py")
            
            # Write test file
            with open(test_file, "w", encoding='utf-8') as f:
                f.write(test_content)
            
            # Verify file exists and has content
            if os.path.exists(test_file) and os.path.getsize(test_file) > 0:
                self.log("✅ Pipeline Volume Mount: PASS", "SUCCESS")
                # Cleanup
                os.remove(test_file)
                return True
                
        except Exception as e:
            self.log(f"❌ Pipeline Volume Mount: FAIL - {e}", "ERROR")
        
        return False
    
    def test_pipeline_docker_cp(self) -> bool:
        """Test Method 2: Docker cp installation for pipelines."""
        self.log("Testing Pipeline Method 2: Docker cp installation...", "TEST")
        
        try:
            # Create test pipeline content
            test_content = '''# Test Enhanced Memory Pipeline
class Pipeline:
    def __init__(self):
        self.id = "test_pipeline_docker"
        self.name = "Test Pipeline Docker"
    
    def pipe(self, user_message, model_id, messages, body):
        return body
'''
            
            # Write to temporary location
            temp_file = "/tmp/test_pipeline_docker.py"
            with open(temp_file, "w", encoding='utf-8') as f:
                f.write(test_content)
            
            # Test docker cp command
            copy_cmd = [
                "docker", "cp", 
                temp_file, 
                "backend-pipelines:/app/pipelines/test_pipeline_docker.py"
            ]
            
            result = subprocess.run(copy_cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                self.log("✅ Pipeline Docker CP: PASS", "SUCCESS")
                
                # Cleanup - remove test file from container
                cleanup_cmd = ["docker", "exec", "backend-pipelines", "rm", "-f", "/app/pipelines/test_pipeline_docker.py"]
                subprocess.run(cleanup_cmd, capture_output=True, text=True, timeout=10)
                
                # Cleanup local temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                return True
            else:
                self.log(f"❌ Pipeline Docker CP: FAIL - {result.stderr}", "ERROR")
                
        except subprocess.TimeoutExpired:
            self.log("❌ Pipeline Docker CP: FAIL - Timeout", "ERROR")
        except Exception as e:
            self.log(f"❌ Pipeline Docker CP: FAIL - {e}", "ERROR")
        
        return False
    
    def test_service_connectivity(self) -> bool:
        """Test connectivity to required services."""
        self.log("Testing service connectivity...", "TEST")
        
        services = {
            "OpenWebUI": "http://openwebui:8080/health",
            "Pipelines": "http://pipelines:9099/",
            "Memory API": "http://memory-api:5001/health",
            "Backend": "http://backend:3000/health"
        }
        
        all_services_ok = True
        
        for service_name, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.log(f"✅ {service_name}: ACCESSIBLE", "SUCCESS")
                else:
                    self.log(f"⚠️ {service_name}: HTTP {response.status_code}", "WARNING")
                    all_services_ok = False
            except Exception as e:
                self.log(f"❌ {service_name}: NOT ACCESSIBLE - {e}", "ERROR")
                all_services_ok = False
        
        return all_services_ok
    
    def verify_installed_components(self) -> dict:
        """Verify that the actual memory components are properly installed."""
        self.log("Verifying installed memory components...", "TEST")
        
        verification_results = {
            "function_installed": False,
            "pipeline_installed": False,
            "function_size": 0,
            "pipeline_size": 0
        }
        
        try:
            # Check function installation
            func_check_cmd = ["docker", "exec", "backend-openwebui", "ls", "-la", "/app/backend/data/functions/enhanced_memory_function.py"]
            result = subprocess.run(func_check_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and "enhanced_memory_function.py" in result.stdout:
                verification_results["function_installed"] = True
                # Extract file size from ls output
                size_info = result.stdout.split()
                if len(size_info) >= 5:
                    verification_results["function_size"] = int(size_info[4])
                self.log("✅ Enhanced Memory Function: VERIFIED", "SUCCESS")
            else:
                self.log("❌ Enhanced Memory Function: NOT FOUND", "ERROR")
                
        except Exception as e:
            self.log(f"❌ Function verification failed: {e}", "ERROR")
        
        try:
            # Check pipeline installation
            pipe_check_cmd = ["docker", "exec", "backend-pipelines", "ls", "-la", "/app/pipelines/enhanced_memory_pipeline.py"]
            result = subprocess.run(pipe_check_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and "enhanced_memory_pipeline.py" in result.stdout:
                verification_results["pipeline_installed"] = True
                # Extract file size from ls output
                size_info = result.stdout.split()
                if len(size_info) >= 5:
                    verification_results["pipeline_size"] = int(size_info[4])
                self.log("✅ Enhanced Memory Pipeline: VERIFIED", "SUCCESS")
            else:
                self.log("❌ Enhanced Memory Pipeline: NOT FOUND", "ERROR")
                
        except Exception as e:
            self.log(f"❌ Pipeline verification failed: {e}", "ERROR")
        
        return verification_results
    
    async def run_comprehensive_test(self):
        """Run all tests and provide comprehensive report."""
        self.log("🚀 Starting Comprehensive Installer Test Suite...", "TEST")
        self.log("=" * 80)
        
        # Test service connectivity first
        connectivity_ok = self.test_service_connectivity()
        
        # Test function installation methods
        self.log("\n📱 TESTING FUNCTION INSTALLATION METHODS", "TEST")
        self.log("-" * 50)
        
        self.test_results["function_methods"]["volume_mount"] = self.test_function_volume_mount()
        self.test_results["function_methods"]["docker_cp"] = self.test_function_docker_cp()
        self.test_results["function_methods"]["api"] = self.test_function_api()
        
        # Test pipeline installation methods
        self.log("\n🔄 TESTING PIPELINE INSTALLATION METHODS", "TEST")
        self.log("-" * 50)
        
        self.test_results["pipeline_methods"]["volume_mount"] = self.test_pipeline_volume_mount()
        self.test_results["pipeline_methods"]["docker_cp"] = self.test_pipeline_docker_cp()
        
        # Verify actual installed components
        self.log("\n🔍 VERIFYING INSTALLED COMPONENTS", "TEST")
        self.log("-" * 50)
        
        verification = self.verify_installed_components()
        
        # Generate comprehensive report
        self.log("\n📊 COMPREHENSIVE TEST REPORT", "TEST")
        self.log("=" * 80)
        
        # Function methods summary
        func_methods_passing = sum(self.test_results["function_methods"].values())
        self.log(f"📱 Function Installation Methods: {func_methods_passing}/3 PASSING")
        for method, status in self.test_results["function_methods"].items():
            status_icon = "✅" if status else "❌"
            self.log(f"   {status_icon} {method.replace('_', ' ').title()}: {'PASS' if status else 'FAIL'}")
        
        # Pipeline methods summary
        pipe_methods_passing = sum(self.test_results["pipeline_methods"].values())
        self.log(f"🔄 Pipeline Installation Methods: {pipe_methods_passing}/2 PASSING")
        for method, status in self.test_results["pipeline_methods"].items():
            status_icon = "✅" if status else "❌"
            self.log(f"   {status_icon} {method.replace('_', ' ').title()}: {'PASS' if status else 'FAIL'}")
        
        # Component verification summary
        self.log(f"🔍 Component Verification:")
        self.log(f"   {'✅' if verification['function_installed'] else '❌'} Enhanced Memory Function: {'INSTALLED' if verification['function_installed'] else 'MISSING'} ({verification['function_size']} bytes)")
        self.log(f"   {'✅' if verification['pipeline_installed'] else '❌'} Enhanced Memory Pipeline: {'INSTALLED' if verification['pipeline_installed'] else 'MISSING'} ({verification['pipeline_size']} bytes)")
        
        # Overall assessment
        critical_methods_working = (
            self.test_results["function_methods"]["volume_mount"] or self.test_results["function_methods"]["docker_cp"]
        ) and (
            self.test_results["pipeline_methods"]["volume_mount"] or self.test_results["pipeline_methods"]["docker_cp"]
        )
        
        components_verified = verification["function_installed"] and verification["pipeline_installed"]
        
        if critical_methods_working and components_verified and connectivity_ok:
            self.test_results["overall_status"] = "EXCELLENT"
            self.log("\n🎉 OVERALL STATUS: EXCELLENT - All systems operational", "SUCCESS")
        elif critical_methods_working and components_verified:
            self.test_results["overall_status"] = "GOOD"
            self.log("\n✅ OVERALL STATUS: GOOD - Core functionality working", "SUCCESS")
        elif components_verified:
            self.test_results["overall_status"] = "ACCEPTABLE"
            self.log("\n⚠️ OVERALL STATUS: ACCEPTABLE - Components installed but some methods failing", "WARNING")
        else:
            self.test_results["overall_status"] = "CRITICAL"
            self.log("\n❌ OVERALL STATUS: CRITICAL - Installation issues detected", "ERROR")
        
        self.log("=" * 80)
        
        return self.test_results

async def main():
    """Main test entry point."""
    tester = InstallerTester()
    results = await tester.run_comprehensive_test()
    
    # Exit with appropriate code
    if results["overall_status"] in ["EXCELLENT", "GOOD"]:
        exit(0)
    elif results["overall_status"] == "ACCEPTABLE":
        exit(1)
    else:
        exit(2)

if __name__ == "__main__":
    asyncio.run(main())
