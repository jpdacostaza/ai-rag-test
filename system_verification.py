#!/usr/bin/env python3
"""
Comprehensive System Verification & Cleanup Tool
Verifies all endpoints, functions, and system components
"""
import requests
import json
import time
import os
from typing import Dict, List, Any
from pathlib import Path

class SystemVerifier:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.memory_api_url = "http://localhost:8001"
        self.openwebui_url = "http://localhost:3000"
        self.results = {
            "endpoints": {},
            "files": {},
            "functions": {},
            "containers": {},
            "cleanup_recommendations": []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp and level"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_endpoint(self, url: str, method: str = "GET", payload: dict = None) -> dict:
        """Test a single endpoint"""
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json=payload, timeout=5)
            else:
                return {"status": "error", "message": f"Unsupported method: {method}"}
            
            return {
                "status": "success" if response.status_code < 400 else "error",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "content_length": len(response.content) if response.content else 0
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def verify_memory_api_endpoints(self):
        """Verify all Memory API endpoints"""
        self.log("🔍 Verifying Memory API Endpoints...")
        
        endpoints = {
            "root": {"url": f"{self.memory_api_url}/", "method": "GET"},
            "retrieve": {
                "url": f"{self.memory_api_url}/api/memory/retrieve",
                "method": "POST",
                "payload": {"user_id": "test", "query": "test", "limit": 1}
            },
            "remember": {
                "url": f"{self.memory_api_url}/api/memory/remember",
                "method": "POST", 
                "payload": {"user_id": "test", "content": "verification test"}
            },
            "forget": {
                "url": f"{self.memory_api_url}/api/memory/forget",
                "method": "POST",
                "payload": {"user_id": "test", "forget_query": "verification test"}
            },
            "learning": {
                "url": f"{self.memory_api_url}/api/learning/process_interaction",
                "method": "POST",
                "payload": {
                    "user_id": "test",
                    "conversation_id": "test",
                    "user_message": "test message"
                }
            },
            "debug": {"url": f"{self.memory_api_url}/debug/stats", "method": "GET"}
        }
        
        for name, config in endpoints.items():
            result = self.test_endpoint(
                config["url"], 
                config["method"], 
                config.get("payload")
            )
            self.results["endpoints"][f"memory_api_{name}"] = result
            
            status_icon = "✅" if result["status"] == "success" else "❌"
            self.log(f"  {status_icon} {name}: {result['status']} ({result.get('status_code', 'N/A')})")
    
    def verify_openwebui_endpoints(self):
        """Verify OpenWebUI endpoints"""
        self.log("🔍 Verifying OpenWebUI Endpoints...")
        
        endpoints = {
            "root": {"url": f"{self.openwebui_url}/", "method": "GET"},
            "models": {"url": f"{self.openwebui_url}/api/models", "method": "GET"},
            "functions": {"url": f"{self.openwebui_url}/api/v1/functions/", "method": "GET"}
        }
        
        for name, config in endpoints.items():
            result = self.test_endpoint(config["url"], config["method"])
            self.results["endpoints"][f"openwebui_{name}"] = result
            
            status_icon = "✅" if result["status"] == "success" else "❌"
            self.log(f"  {status_icon} {name}: {result['status']} ({result.get('status_code', 'N/A')})")
    
    def analyze_project_files(self):
        """Analyze all project files for cleanup opportunities"""
        self.log("📁 Analyzing Project Files...")
        
        # Categorize files
        categories = {
            "active_core": [],
            "active_tests": [],
            "active_config": [],
            "documentation": [],
            "obsolete": [],
            "backup": [],
            "unknown": []
        }
        
        # Define patterns for each category
        patterns = {
            "active_core": [
                "enhanced_memory_api.py", "docker-compose.yml", "requirements.txt",
                "storage/openwebui/memory_function_working.py"
            ],
            "active_tests": [
                "test_comprehensive_memory.py", "test_explicit_memory.py", 
                "test_memory_integration.py"
            ],
            "active_config": [
                "config.py", "models.py", ".env.example", "Dockerfile*"
            ],
            "documentation": [
                "*.md", "readme/*", "docs/*"
            ],
            "obsolete": [
                "*_old*", "*_backup*", "*_deprecated*", "memory_function.py",
                "memory_api_main_fixed.py", "adaptive_learning.py"
            ],
            "backup": [
                "CLEANUP_BACKUP_*", "archive/*", "__pycache__/*"
            ]
        }
        
        # Scan all files
        for file_path in self.base_dir.rglob("*"):
            try:
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.base_dir)
                    categorized = False
                    
                    for category, pattern_list in patterns.items():
                        for pattern in pattern_list:
                            if file_path.match(pattern) or str(relative_path).startswith(pattern.replace("*", "")):
                                categories[category].append(str(relative_path))
                                categorized = True
                                break
                        if categorized:
                            break
                    
                    if not categorized:
                        categories["unknown"].append(str(relative_path))
            except (OSError, PermissionError):
                # Skip files that can't be accessed (long paths, permissions, etc.)
                continue
        
        # Report findings
        for category, files in categories.items():
            if files:
                self.log(f"📂 {category.upper()}: {len(files)} files")
                self.results["files"][category] = files
                
                if category == "obsolete":
                    self.results["cleanup_recommendations"].extend([
                        f"Consider removing obsolete file: {f}" for f in files[:5]
                    ])
    
    def verify_docker_containers(self):
        """Verify Docker container status"""
        self.log("🐳 Verifying Docker Containers...")
        
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "ps", "--format", "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"],
                capture_output=True, text=True, cwd=self.base_dir
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            name = parts[0]
                            status = parts[1]
                            ports = parts[2] if len(parts) > 2 else "No ports"
                            
                            self.results["containers"][name] = {
                                "status": status,
                                "ports": ports,
                                "healthy": "Up" in status
                            }
                            
                            status_icon = "✅" if "Up" in status else "❌"
                            self.log(f"  {status_icon} {name}: {status}")
            else:
                self.log("❌ Failed to get Docker container status", "ERROR")
                
        except Exception as e:
            self.log(f"❌ Docker verification failed: {e}", "ERROR")
    
    def verify_memory_function_integration(self):
        """Verify memory function file integration"""
        self.log("🧠 Verifying Memory Function Integration...")
        
        memory_function_path = self.base_dir / "storage" / "openwebui" / "memory_function_working.py"
        
        if memory_function_path.exists():
            # Check for key functions
            try:
                content = memory_function_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                content = memory_function_path.read_text(encoding='utf-8', errors='ignore')
            
            required_functions = [
                "explicit_remember",
                "explicit_forget", 
                "detect_memory_commands",
                "inlet"
            ]
            
            missing_functions = []
            for func in required_functions:
                if f"def {func}" not in content:
                    missing_functions.append(func)
            
            if missing_functions:
                self.results["functions"]["memory_function"] = {
                    "status": "incomplete",
                    "missing": missing_functions
                }
                self.log(f"⚠️ Memory function missing: {', '.join(missing_functions)}")
            else:
                self.results["functions"]["memory_function"] = {"status": "complete"}
                self.log("✅ Memory function integration complete")
        else:
            self.results["functions"]["memory_function"] = {"status": "missing"}
            self.log("❌ Memory function file not found")
    
    def run_comprehensive_verification(self):
        """Run all verification checks"""
        self.log("🚀 Starting Comprehensive System Verification")
        self.log("=" * 60)
        
        # Wait for services to be ready
        self.log("⏳ Waiting for services to be ready...")
        time.sleep(3)
        
        # Run all verification steps
        self.verify_docker_containers()
        self.verify_memory_api_endpoints()
        self.verify_openwebui_endpoints()
        self.verify_memory_function_integration()
        self.analyze_project_files()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive verification report"""
        self.log("📊 Generating Verification Report")
        self.log("=" * 60)
        
        # Summary statistics
        endpoint_success = sum(1 for r in self.results["endpoints"].values() if r["status"] == "success")
        endpoint_total = len(self.results["endpoints"])
        
        container_healthy = sum(1 for r in self.results["containers"].values() if r["healthy"])
        container_total = len(self.results["containers"])
        
        self.log(f"📈 SUMMARY:")
        self.log(f"  Endpoints: {endpoint_success}/{endpoint_total} working")
        self.log(f"  Containers: {container_healthy}/{container_total} healthy")
        self.log(f"  Functions: {len(self.results['functions'])} verified")
        
        # Cleanup recommendations
        if self.results["cleanup_recommendations"]:
            self.log("🧹 CLEANUP RECOMMENDATIONS:")
            for rec in self.results["cleanup_recommendations"][:10]:
                self.log(f"  • {rec}")
        
        # Write detailed report to file
        report_path = self.base_dir / "SYSTEM_VERIFICATION_REPORT.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# System Verification Report\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Endpoint Status\n")
            for name, result in self.results["endpoints"].items():
                status_icon = "✅" if result["status"] == "success" else "❌"
                f.write(f"- {status_icon} **{name}**: {result['status']} ({result.get('status_code', 'N/A')})\n")
            
            f.write("\n## Container Status\n")
            for name, result in self.results["containers"].items():
                status_icon = "✅" if result["healthy"] else "❌"
                f.write(f"- {status_icon} **{name}**: {result['status']}\n")
            
            f.write("\n## File Analysis\n")
            for category, files in self.results["files"].items():
                if files:
                    f.write(f"### {category.title()} ({len(files)} files)\n")
                    for file in files[:10]:  # Limit to first 10
                        f.write(f"- {file}\n")
                    if len(files) > 10:
                        f.write(f"- ... and {len(files) - 10} more\n")
                    f.write("\n")
            
            if self.results["cleanup_recommendations"]:
                f.write("## Cleanup Recommendations\n")
                for rec in self.results["cleanup_recommendations"]:
                    f.write(f"- {rec}\n")
        
        self.log(f"📄 Detailed report saved to: {report_path.name}")
        
        # Overall status
        overall_healthy = (endpoint_success == endpoint_total and 
                          container_healthy == container_total)
        
        if overall_healthy:
            self.log("🎉 SYSTEM STATUS: HEALTHY ✅")
        else:
            self.log("⚠️ SYSTEM STATUS: NEEDS ATTENTION ❌")

def main():
    """Main verification function"""
    verifier = SystemVerifier()
    verifier.run_comprehensive_verification()

if __name__ == "__main__":
    main()
