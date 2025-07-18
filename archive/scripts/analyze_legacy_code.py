#!/usr/bin/env python3
"""
Legacy Code Detection and Archival Script
This script analyzes the codebase to identify obsolete, unused, or legacy files and moves them to an archive folder.
"""

import os
import ast
import re
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class LegacyCodeAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.archive_dir = self.root_dir / 'archive'
        self.archive_dir.mkdir(exist_ok=True)
        
        # Track imports and usage
        self.imports_map = defaultdict(set)  # file -> set of imported modules
        self.exports_map = defaultdict(set)  # file -> set of exported functions/classes
        self.used_modules = set()
        self.all_python_files = []
        
        # Files that are definitely obsolete or legacy
        self.obsolete_patterns = [
            r'.*_old\.py$',
            r'.*_legacy\.py$',
            r'.*_backup\.py$',
            r'.*_original\.py$',
            r'.*\.bak$',
            r'.*\.tmp$',
            r'.*_test_old\.py$',
        ]
        
        # Directories that might contain obsolete code
        self.obsolete_dirs = [
            'old', 'legacy', 'backup', 'deprecated', 'unused'
        ]
        
        # Files to analyze for specific obsolete patterns
        self.legacy_indicators = [
            'TODO.*remove',
            'FIXME.*delete',
            'DEPRECATED',
            'OBSOLETE',
            '# OLD CODE',
            '# LEGACY',
            'This file is no longer used',
            'REMOVE THIS FILE'
        ]

    def scan_project_structure(self):
        """Scan the entire project to build a map of all Python files and their relationships"""
        print("🔍 Scanning project structure...")
        
        for py_file in self.root_dir.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            self.all_python_files.append(py_file)
            
        print(f"📊 Found {len(self.all_python_files)} Python files to analyze")

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during analysis"""
        skip_patterns = [
            '__pycache__', '.git', '.pytest_cache', 'node_modules',
            'venv', '.venv', 'env', '.env', 'openwebui'
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)

    def analyze_imports_and_exports(self):
        """Analyze all Python files to understand import relationships"""
        print("🔗 Analyzing imports and exports...")
        
        for file_path in self.all_python_files:
            try:
                self._analyze_file(file_path)
            except Exception as e:
                print(f"⚠️  Error analyzing {file_path}: {e}")

    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file for imports and exports"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse AST to find imports and exports
            try:
                tree = ast.parse(content)
                self._extract_imports_exports(tree, file_path)
            except SyntaxError:
                # If AST fails, use regex for basic analysis
                self._extract_imports_regex(content, file_path)
                
            # Check for legacy indicators
            self._check_legacy_indicators(content, file_path)
            
        except Exception as e:
            print(f"⚠️  Error reading {file_path}: {e}")

    def _extract_imports_exports(self, tree: ast.AST, file_path: Path):
        """Extract imports and exports using AST"""
        relative_path = file_path.relative_to(self.root_dir)
        
        for node in ast.walk(tree):
            # Track imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports_map[str(relative_path)].add(alias.name)
                    
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.imports_map[str(relative_path)].add(node.module)
                    
            # Track exports (functions and classes)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not node.name.startswith('_'):  # Public functions/classes
                    self.exports_map[str(relative_path)].add(node.name)

    def _extract_imports_regex(self, content: str, file_path: Path):
        """Extract imports using regex as fallback"""
        relative_path = file_path.relative_to(self.root_dir)
        
        # Find import statements
        import_patterns = [
            r'from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import',
            r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                self.imports_map[str(relative_path)].add(match)

    def _check_legacy_indicators(self, content: str, file_path: Path):
        """Check for legacy code indicators in file content"""
        for indicator in self.legacy_indicators:
            if re.search(indicator, content, re.IGNORECASE):
                print(f"🏷️  Legacy indicator found in {file_path}: {indicator}")

    def identify_obsolete_files(self) -> List[Path]:
        """Identify files that appear to be obsolete or unused"""
        print("🗑️  Identifying obsolete files...")
        
        obsolete_files = []
        
        # 1. Files matching obsolete patterns
        for pattern in self.obsolete_patterns:
            for file_path in self.all_python_files:
                if re.match(pattern, file_path.name):
                    obsolete_files.append(file_path)
                    print(f"📋 Pattern match: {file_path}")
        
        # 2. Files in obsolete directories
        for file_path in self.all_python_files:
            if any(obs_dir in file_path.parts for obs_dir in self.obsolete_dirs):
                obsolete_files.append(file_path)
                print(f"📂 Obsolete directory: {file_path}")
        
        # 3. Analyze specific files based on content and usage
        obsolete_files.extend(self._analyze_specific_obsolete_files())
        
        return list(set(obsolete_files))  # Remove duplicates

    def _analyze_specific_obsolete_files(self) -> List[Path]:
        """Analyze specific files that might be obsolete based on project knowledge"""
        obsolete_files = []
        
        # Files that are likely obsolete based on the reorganization
        potentially_obsolete = [
            'startup_original.py',  # Replaced by startup.py
            'startup_simplified.py',  # Likely unused variant
            'config_minimal.py',  # Might be replaced by config_unified.py
            'debug_config.py',  # Might be development-only
            'migrate_config.py',  # Migration scripts are often temporary
            'pipeline_config_simplified.py',  # Simplified version might be unused
        ]
        
        for file_name in potentially_obsolete:
            file_path = self._find_file_by_name(file_name)
            if file_path:
                # Check if it's actually used
                if not self._is_file_referenced(file_path):
                    obsolete_files.append(file_path)
                    print(f"🔍 Unused file: {file_path}")
        
        return obsolete_files

    def _find_file_by_name(self, filename: str) -> Path:
        """Find a file by name in the project"""
        for file_path in self.all_python_files:
            if file_path.name == filename:
                return file_path
        return None

    def _is_file_referenced(self, target_file: Path) -> bool:
        """Check if a file is referenced/imported by other files"""
        target_module = self._path_to_module_name(target_file)
        
        for file_path, imports in self.imports_map.items():
            if target_module in imports or target_file.stem in imports:
                return True
        
        return False

    def _path_to_module_name(self, file_path: Path) -> str:
        """Convert file path to Python module name"""
        relative_path = file_path.relative_to(self.root_dir)
        return str(relative_path.with_suffix('')).replace(os.sep, '.')

    def identify_test_files(self) -> Dict[str, List[Path]]:
        """Identify test files and categorize them"""
        print("🧪 Analyzing test files...")
        
        test_categories = {
            'outdated_tests': [],
            'comprehensive_tests': [],
            'migration_tests': [],
            'integration_tests': []
        }
        
        for file_path in self.all_python_files:
            if 'test' in file_path.name.lower():
                # Categorize based on patterns
                if any(pattern in file_path.name for pattern in ['comprehensive_test', 'enhanced_comprehensive']):
                    test_categories['comprehensive_tests'].append(file_path)
                elif 'migration' in file_path.name:
                    test_categories['migration_tests'].append(file_path)
                elif any(pattern in file_path.name for pattern in ['integration', 'end_to_end']):
                    test_categories['integration_tests'].append(file_path)
                else:
                    # Check if test file is outdated
                    if self._is_test_outdated(file_path):
                        test_categories['outdated_tests'].append(file_path)
        
        return test_categories

    def _is_test_outdated(self, test_file: Path) -> bool:
        """Check if a test file appears to be outdated"""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for outdated patterns
            outdated_indicators = [
                'from main import',  # Should now be 'from core.main import'
                'from config import',  # Should be 'from config.config import'
                'from database_manager import',  # Should be 'from services.database_manager import'
                '# This test is no longer valid',
                '# OUTDATED',
                '# DEPRECATED TEST'
            ]
            
            for indicator in outdated_indicators:
                if indicator in content:
                    return True
                    
            return False
            
        except Exception:
            return False

    def identify_documentation_files(self) -> Dict[str, List[Path]]:
        """Identify documentation files that might be outdated"""
        print("📚 Analyzing documentation files...")
        
        doc_categories = {
            'outdated_docs': [],
            'migration_docs': [],
            'cleanup_reports': []
        }
        
        # Check documentation files
        doc_extensions = ['.md', '.txt', '.rst']
        for ext in doc_extensions:
            for doc_file in self.root_dir.rglob(f"*{ext}"):
                if self._should_skip_file(doc_file):
                    continue
                    
                file_name = doc_file.name.lower()
                
                if any(pattern in file_name for pattern in ['cleanup', 'report', 'summary']):
                    doc_categories['cleanup_reports'].append(doc_file)
                elif 'migration' in file_name:
                    doc_categories['migration_docs'].append(doc_file)
                elif self._is_doc_outdated(doc_file):
                    doc_categories['outdated_docs'].append(doc_file)
        
        return doc_categories

    def _is_doc_outdated(self, doc_file: Path) -> bool:
        """Check if documentation file appears outdated"""
        try:
            with open(doc_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for outdated references
            outdated_refs = [
                'main.py in root',
                'config.py in root',
                'Old structure',
                'Before reorganization'
            ]
            
            return any(ref in content for ref in outdated_refs)
            
        except Exception:
            return False

    def move_to_archive(self, files_to_archive: List[Path], category: str):
        """Move files to archive with categorization"""
        if not files_to_archive:
            return
            
        category_dir = self.archive_dir / category
        category_dir.mkdir(exist_ok=True)
        
        print(f"\n📦 Moving {len(files_to_archive)} files to archive/{category}/")
        
        for file_path in files_to_archive:
            try:
                # Preserve directory structure in archive
                relative_path = file_path.relative_to(self.root_dir)
                archive_path = category_dir / relative_path
                
                # Create directory structure
                archive_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move file
                shutil.move(str(file_path), str(archive_path))
                print(f"✅ Archived: {relative_path} → archive/{category}/{relative_path}")
                
            except Exception as e:
                print(f"❌ Failed to archive {file_path}: {e}")

    def create_archive_manifest(self, archived_files: Dict[str, List[Path]]):
        """Create a manifest of archived files"""
        manifest_path = self.archive_dir / 'ARCHIVE_MANIFEST.md'
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write("# Archive Manifest\n\n")
            f.write(f"Generated on: {Path().cwd()}\n")
            f.write(f"Total categories: {len(archived_files)}\n\n")
            
            for category, files in archived_files.items():
                if files:
                    f.write(f"## {category.replace('_', ' ').title()}\n\n")
                    f.write(f"Files archived: {len(files)}\n\n")
                    
                    for file_path in files:
                        relative_path = file_path.relative_to(self.root_dir) if file_path.is_relative_to(self.root_dir) else file_path
                        f.write(f"- `{relative_path}`\n")
                    f.write("\n")
        
        print(f"📋 Archive manifest created: {manifest_path}")

    def analyze_and_archive(self):
        """Run the complete analysis and archival process"""
        print("🚀 Starting legacy code analysis and archival...")
        
        # Step 1: Scan project
        self.scan_project_structure()
        
        # Step 2: Analyze imports and usage
        self.analyze_imports_and_exports()
        
        # Step 3: Identify different categories of files to archive
        obsolete_files = self.identify_obsolete_files()
        test_categories = self.identify_test_files()
        doc_categories = self.identify_documentation_files()
        
        # Step 4: Move files to archive
        archived_files = {}
        
        if obsolete_files:
            self.move_to_archive(obsolete_files, 'obsolete_code')
            archived_files['obsolete_code'] = obsolete_files
        
        for category, files in test_categories.items():
            if files and category in ['outdated_tests', 'migration_tests']:
                self.move_to_archive(files, category)
                archived_files[category] = files
        
        for category, files in doc_categories.items():
            if files and category in ['cleanup_reports', 'migration_docs']:
                self.move_to_archive(files, category)
                archived_files[category] = files
        
        # Step 5: Create manifest
        self.create_archive_manifest(archived_files)
        
        # Summary
        total_archived = sum(len(files) for files in archived_files.values())
        print(f"\n✅ Analysis complete!")
        print(f"📊 Total files archived: {total_archived}")
        print(f"📂 Archive location: {self.archive_dir}")

if __name__ == "__main__":
    import sys
    
    root_directory = sys.argv[1] if len(sys.argv) > 1 else "."
    
    analyzer = LegacyCodeAnalyzer(root_directory)
    analyzer.analyze_and_archive()
