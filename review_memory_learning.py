#!/usr/bin/env python3
"""
Review Learning and Memory Functions
====================================

This script analyzes all memory and learning-related functions in the codebase
and provides detailed improvement suggestions.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json

class MemoryLearningReviewer:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.memory_files = []
        self.learning_files = []
        self.issues = []
        self.improvements = []
        
    def find_memory_learning_files(self):
        """Find all files related to memory and learning."""
        patterns = ['memory', 'learning', 'adaptive', 'retrieval', 'embedding', 'vector']
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip irrelevant directories
            if any(skip in root for skip in ['.git', '__pycache__', 'venv', 'test', 'storage']):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    try:
                        filepath = Path(root) / file
                        try:
                            content = filepath.read_text(encoding='utf-8')
                            
                            # Check if file contains memory/learning related code
                            if any(pattern in content.lower() for pattern in patterns):
                                if 'memory' in file.lower() or 'memory' in content.lower():
                                    self.memory_files.append(filepath)
                                if 'learning' in file.lower() or 'adaptive' in content.lower():
                                    self.learning_files.append(filepath)
                        except (OSError, UnicodeDecodeError) as e:
                            print(f"Warning: Could not read file {filepath}: {e}")
                    except Exception as e:
                        print(f"Warning: Error processing file {file} in {root}: {e}")
                            
    def analyze_memory_functions(self):
        """Analyze memory-related functions for issues and improvements."""
        print("\n🧠 Analyzing Memory Functions...")
        
        # Key files to analyze
        key_files = [
            'database_manager.py',
            'memory_manager.py',
            'enhanced_memory_system.py',
            'memory/advanced_memory_pipeline.py',
            'memory/memory_pipeline.py'
        ]
        
        for filename in key_files:
            filepath = self.project_root / filename
            if filepath.exists():
                self._analyze_file(filepath, 'memory')
                
    def analyze_learning_functions(self):
        """Analyze learning-related functions for issues and improvements."""
        print("\n📚 Analyzing Learning Functions...")
        
        # Key files to analyze
        key_files = [
            'adaptive_learning.py',
            'enhanced_integration.py',
            'utilities/ai_tools.py'
        ]
        
        for filename in key_files:
            filepath = self.project_root / filename
            if filepath.exists():
                self._analyze_file(filepath, 'learning')
                
    def _analyze_file(self, filepath: Path, category: str):
        """Analyze a specific file for memory/learning issues."""
        try:
            content = filepath.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            # Analyze functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self._analyze_function(node, filepath, category)
                    
        except Exception as e:
            self.issues.append({
                'file': str(filepath),
                'issue': f'Failed to parse file: {e}',
                'severity': 'high'
            })
            
    def _analyze_function(self, node: ast.AST, filepath: Path, category: str):
        """Analyze a specific function for issues."""
        function_name = node.name
        
        # Check for common issues
        issues = []
        
        # 1. Check for missing error handling
        has_try_except = any(isinstance(n, ast.Try) for n in ast.walk(node))
        if not has_try_except and not function_name.startswith('_'):
            issues.append("Missing error handling")
            
        # 2. Check for performance issues
        if self._has_nested_loops(node):
            issues.append("Nested loops detected - potential O(n²) complexity")
            
        # 3. Check for memory leaks
        if self._has_potential_memory_leak(node):
            issues.append("Potential memory leak - large data structures not cleared")
            
        # 4. Check for missing validation
        if self._lacks_input_validation(node):
            issues.append("Missing input validation")
            
        # 5. Check for synchronization issues
        if 'async' in ast.unparse(node) and self._lacks_proper_locking(node):
            issues.append("Potential race condition - missing locks/semaphores")
            
        if issues:
            self.issues.append({
                'file': str(filepath),
                'function': function_name,
                'issues': issues,
                'category': category
            })
            
    def _has_nested_loops(self, node: ast.AST) -> bool:
        """Check if function has nested loops."""
        loop_depth = 0
        max_depth = 0
        
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While)):
                loop_depth += 1
                max_depth = max(max_depth, loop_depth)
            elif isinstance(child, ast.FunctionDef):
                loop_depth = 0
                
        return max_depth > 1
        
    def _has_potential_memory_leak(self, node: ast.AST) -> bool:
        """Check for potential memory leaks."""
        # Look for large collections that aren't cleared
        has_large_collection = False
        has_clear_operation = False
        
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                if child.id in ['cache', 'buffer', 'history', 'data']:
                    has_large_collection = True
            if isinstance(child, ast.Call):
                if hasattr(child.func, 'attr') and child.func.attr in ['clear', 'close', 'cleanup']:
                    has_clear_operation = True
                    
        return has_large_collection and not has_clear_operation
        
    def _lacks_input_validation(self, node: ast.AST) -> bool:
        """Check if function lacks input validation."""
        # Check if function has parameters but no validation
        if node.args.args:
            has_validation = any(
                isinstance(n, ast.If) or 
                (isinstance(n, ast.Call) and hasattr(n.func, 'id') and 
                 n.func.id in ['isinstance', 'validate', 'check'])
                for n in ast.walk(node)
            )
            return not has_validation
        return False
        
    def _lacks_proper_locking(self, node: ast.AST) -> bool:
        """Check if async function lacks proper locking."""
        has_shared_state = any(
            isinstance(n, ast.Attribute) and 'self' in ast.unparse(n)
            for n in ast.walk(node)
        )
        has_lock = any(
            'lock' in ast.unparse(n).lower() or 'semaphore' in ast.unparse(n).lower()
            for n in ast.walk(node)
        )
        return has_shared_state and not has_lock
        
    def generate_improvements(self):
        """Generate specific improvements based on analysis."""
        self.improvements = [
            {
                'category': 'Memory Management',
                'improvements': [
                    {
                        'title': 'Implement Memory Pooling',
                        'description': 'Use object pooling for frequently created/destroyed memory objects',
                        'priority': 'high'
                    },
                    {
                        'title': 'Add Memory Pressure Monitoring',
                        'description': 'Monitor and respond to memory pressure',
                        'priority': 'medium'
                    },
                    {
                        'title': 'Implement Hierarchical Memory',
                        'description': 'Create memory hierarchy for better organization',
                        'priority': 'high'
                    }
                ]
            },
            {
                'category': 'Learning Optimization',
                'improvements': [
                    {
                        'title': 'Implement Learning Rate Scheduling',
                        'description': 'Adaptive learning rate based on performance',
                        'priority': 'medium'
                    },
                    {
                        'title': 'Add Reinforcement Learning',
                        'description': 'Learn from user feedback',
                        'priority': 'high'
                    },
                    {
                        'title': 'Implement Meta-Learning',
                        'description': 'Learn how to learn better',
                        'priority': 'medium'
                    }
                ]
            },
            {
                'category': 'Retrieval Enhancement',
                'improvements': [
                    {
                        'title': 'Implement Hybrid Search',
                        'description': 'Combine vector and keyword search',
                        'priority': 'high'
                    },
                    {
                        'title': 'Add Contextual Reranking',
                        'description': 'Rerank results based on context',
                        'priority': 'medium'
                    },
                    {
                        'title': 'Implement Query Expansion',
                        'description': 'Expand queries for better recall',
                        'priority': 'low'
                    }
                ]
            }
        ]
        
    def run_analysis(self):
        """Run the complete analysis."""
        print("🔍 Starting Memory & Learning System Analysis...")
        
        # Find relevant files
        self.find_memory_learning_files()
        print(f"\nFound {len(self.memory_files)} memory files and {len(self.learning_files)} learning files")
        
        # Analyze functions
        self.analyze_memory_functions()
        self.analyze_learning_functions()
        
        # Generate improvements
        self.generate_improvements()
        
        # Generate report
        report = {
            'timestamp': str(datetime.now()),
            'files_analyzed': {
                'memory_files': [str(f) for f in self.memory_files],
                'learning_files': [str(f) for f in self.learning_files]
            },
            'issues': self.issues,
            'improvements': self.improvements
        }
        
        # Save report
        report_path = self.project_root / 'memory_learning_review.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n✅ Analysis complete! Report saved to {report_path}")
        return report

if __name__ == '__main__':
    from datetime import datetime
    reviewer = MemoryLearningReviewer()
    reviewer.run_analysis()
