#!/usr/bin/env python3
"""
Comprehensive live test suite for the Mistral 7B Instruct model.
Tests various endpoints and scenarios to ensure proper integration.
"""

import json
import time
import asyncio
import aiohttp
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "http://localhost:8001"
MODEL_NAME = "mistral:7b-instruct-v0.3-q4_k_m"

class MistralTestSuite:
    def __init__(self):
        self.results = {
            "start_time": datetime.now().isoformat(),
            "model": MODEL_NAME,
            "backend_url": BACKEND_URL,
            "tests": []
        }
        
    def log_test(self, test_name: str, status: str, details: Optional[Dict] = None):
        """Log test results"""
        test_result = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "details": details or {}
        }
        self.results["tests"].append(test_result)
        print(f"✓ {test_name}: {status}")
        if details and details.get("error"):
            print(f"  Error: {details['error']}")
        if details and details.get("response_time"):
            print(f"  Response time: {details['response_time']:.2f}s")
    
    def test_health_check(self):
        """Test backend health"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", "PASSED", {
                    "status_code": response.status_code,
                    "response": data
                })
                return True
            else:
                self.log_test("Health Check", "FAILED", {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
        except Exception as e:
            self.log_test("Health Check", "ERROR", {"error": str(e)})
            return False
    
    def test_model_listing(self):
        """Test model listing endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/v1/models", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = [model["id"] for model in data.get("data", [])]
                mistral_found = MODEL_NAME in models
                
                self.log_test("Model Listing", "PASSED" if mistral_found else "FAILED", {
                    "status_code": response.status_code,
                    "total_models": len(models),
                    "mistral_found": mistral_found,
                    "available_models": models
                })
                return mistral_found
            else:
                self.log_test("Model Listing", "FAILED", {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
        except Exception as e:
            self.log_test("Model Listing", "ERROR", {"error": str(e)})
            return False
      def test_simple_chat(self):
        """Test simple chat completion"""
        try:
            start_time = time.time()
            payload = {
                "message": "Hello! Please introduce yourself and tell me what you can do.",
                "model": MODEL_NAME,
                "user_id": "test_user_001"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/chat", 
                json=payload, 
                timeout=60
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")
                
                self.log_test("Simple Chat", "PASSED", {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "response_length": len(response_text),
                    "response_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text
                })
                return True
            else:
                self.log_test("Simple Chat", "FAILED", {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "response": response.text
                })
                return False
        except Exception as e:
            self.log_test("Simple Chat", "ERROR", {"error": str(e)})
            return False
    
    def test_openai_completions(self):
        """Test OpenAI-compatible completions endpoint"""
        try:
            start_time = time.time()
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "user", "content": "Explain quantum computing in simple terms."}
                ],
                "max_tokens": 200,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{BACKEND_URL}/v1/chat/completions",
                json=payload,
                timeout=60
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                self.log_test("OpenAI Completions", "PASSED", {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "content_length": len(content),
                    "content_preview": content[:200] + "..." if len(content) > 200 else content,
                    "usage": data.get("usage", {})
                })
                return True
            else:
                self.log_test("OpenAI Completions", "FAILED", {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "response": response.text
                })
                return False
        except Exception as e:
            self.log_test("OpenAI Completions", "ERROR", {"error": str(e)})
            return False
    
    def test_streaming_completions(self):
        """Test streaming completions"""
        try:
            start_time = time.time()
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "user", "content": "Write a short story about a robot learning to paint."}
                ],
                "stream": True,
                "max_tokens": 300
            }
            
            response = requests.post(
                f"{BACKEND_URL}/v1/chat/completions",
                json=payload,
                stream=True,
                timeout=60
            )
            
            if response.status_code == 200:
                chunks = []
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str.strip() != '[DONE]':
                                try:
                                    chunk_data = json.loads(data_str)
                                    delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                                    if "content" in delta:
                                        chunks.append(delta["content"])
                                except json.JSONDecodeError:
                                    continue
                
                response_time = time.time() - start_time
                full_content = "".join(chunks)
                
                self.log_test("Streaming Completions", "PASSED", {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "chunks_received": len(chunks),
                    "total_content_length": len(full_content),
                    "content_preview": full_content[:200] + "..." if len(full_content) > 200 else full_content
                })
                return True
            else:
                self.log_test("Streaming Completions", "FAILED", {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
        except Exception as e:
            self.log_test("Streaming Completions", "ERROR", {"error": str(e)})
            return False
    
    def test_complex_reasoning(self):
        """Test complex reasoning capabilities"""
        try:
            start_time = time.time()
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "user", "content": """
                    I have a logic puzzle for you:
                    - Alice, Bob, and Charlie are sitting in a row.
                    - Alice is not in the middle.
                    - Bob is to the right of Alice.
                    - Charlie is not at either end.
                    
                    Who is sitting where? Please explain your reasoning step by step.
                    """}
                ],
                "max_tokens": 400,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{BACKEND_URL}/v1/chat/completions",
                json=payload,
                timeout=60
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Check if the response contains logical reasoning
                reasoning_keywords = ["step", "first", "second", "therefore", "because", "since"]
                has_reasoning = any(keyword in content.lower() for keyword in reasoning_keywords)
                
                self.log_test("Complex Reasoning", "PASSED", {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "content_length": len(content),
                    "has_reasoning_keywords": has_reasoning,
                    "content_preview": content[:300] + "..." if len(content) > 300 else content
                })
                return True
            else:
                self.log_test("Complex Reasoning", "FAILED", {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "response": response.text
                })
                return False
        except Exception as e:
            self.log_test("Complex Reasoning", "ERROR", {"error": str(e)})
            return False
      def test_code_generation(self):
        """Test code generation capabilities"""
        try:
            start_time = time.time()
            payload = {
                "message": "Write a Python function to calculate the factorial of a number using recursion. Include comments and error handling.",
                "model": MODEL_NAME,
                "user_id": "test_user_001"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json=payload,
                timeout=60
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")
                
                # Check if response contains code-like content
                code_indicators = ["def ", "return", "if ", "else", "#", "factorial"]
                has_code = any(indicator in response_text for indicator in code_indicators)
                
                self.log_test("Code Generation", "PASSED", {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "response_length": len(response_text),
                    "contains_code_indicators": has_code,
                    "response_preview": response_text[:300] + "..." if len(response_text) > 300 else response_text
                })
                return True
            else:
                self.log_test("Code Generation", "FAILED", {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "response": response.text
                })
                return False
        except Exception as e:
            self.log_test("Code Generation", "ERROR", {"error": str(e)})
            return False
    
    def test_multilingual_capabilities(self):
        """Test multilingual capabilities"""
        try:
            start_time = time.time()
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "user", "content": "Translate 'Hello, how are you today?' to French, Spanish, and German. Provide the translations with language labels."}
                ],
                "max_tokens": 200
            }
            
            response = requests.post(
                f"{BACKEND_URL}/v1/chat/completions",
                json=payload,
                timeout=60
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Check for language indicators
                lang_indicators = ["french", "spanish", "german", "français", "español", "deutsch"]
                has_languages = any(indicator.lower() in content.lower() for indicator in lang_indicators)
                
                self.log_test("Multilingual Capabilities", "PASSED", {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "content_length": len(content),
                    "contains_language_indicators": has_languages,
                    "content_preview": content[:250] + "..." if len(content) > 250 else content
                })
                return True
            else:
                self.log_test("Multilingual Capabilities", "FAILED", {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "response": response.text
                })
                return False
        except Exception as e:
            self.log_test("Multilingual Capabilities", "ERROR", {"error": str(e)})
            return False
    
    def test_conversation_context(self):
        """Test conversation context handling"""
        try:
            start_time = time.time()
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "user", "content": "My name is Alice and I'm 25 years old."},
                    {"role": "assistant", "content": "Nice to meet you, Alice! It's great to know you're 25."},
                    {"role": "user", "content": "What's my name and age again?"}
                ],
                "max_tokens": 100
            }
            
            response = requests.post(
                f"{BACKEND_URL}/v1/chat/completions",
                json=payload,
                timeout=60
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Check if the model remembers the context
                remembers_name = "alice" in content.lower()
                remembers_age = "25" in content
                
                self.log_test("Conversation Context", "PASSED", {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "remembers_name": remembers_name,
                    "remembers_age": remembers_age,
                    "content": content
                })
                return True
            else:
                self.log_test("Conversation Context", "FAILED", {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "response": response.text
                })
                return False
        except Exception as e:
            self.log_test("Conversation Context", "ERROR", {"error": str(e)})
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"🚀 Starting comprehensive Mistral 7B Instruct test suite...")
        print(f"Model: {MODEL_NAME}")
        print(f"Backend: {BACKEND_URL}")
        print("=" * 60)
        
        # Run tests in order
        tests = [
            self.test_health_check,
            self.test_model_listing,
            self.test_simple_chat,
            self.test_openai_completions,
            self.test_streaming_completions,
            self.test_complex_reasoning,
            self.test_code_generation,
            self.test_multilingual_capabilities,
            self.test_conversation_context
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  Unexpected error in {test.__name__}: {e}")
                failed += 1
            
            # Small delay between tests
            time.sleep(1)
        
        # Summary
        self.results["end_time"] = datetime.now().isoformat()
        self.results["summary"] = {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "success_rate": f"{(passed / len(tests)) * 100:.1f}%"
        }
        
        print("=" * 60)
        print(f"🎯 Test Summary:")
        print(f"  Total tests: {len(tests)}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Success rate: {(passed / len(tests)) * 100:.1f}%")
        
        return self.results
    
    def save_results(self, filename: Optional[str] = None):
        """Save test results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mistral_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Results saved to: {filename}")
        return filename

if __name__ == "__main__":
    # Run the test suite
    test_suite = MistralTestSuite()
    results = test_suite.run_all_tests()
    test_suite.save_results()
