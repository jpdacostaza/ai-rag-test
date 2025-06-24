#!/usr/bin/env python3
"""
Unicode Fix Script for Debug Tools
Fixes Windows encoding issues by replacing Unicode emoji with ASCII equivalents
"""

import os
import re
from pathlib import Path

class UnicodeFixTool:
    def __init__(self):
        self.emoji_replacements = {
            # Common emoji used in debug tools
            '🚀': '[START]',
            '✅': '[OK]',
            '❌': '[FAIL]', 
            '🔧': '[TOOL]',
            '📊': '[DATA]',
            '🎯': '[TARGET]',
            '💥': '[ERROR]',
            '⏰': '[TIMEOUT]',
            '🧠': '[BRAIN]',
            '🟡': '[YELLOW]',
            '🟣': '[PURPLE]',
            '🏁': '[FINISH]',
            '🎨': '[ART]',
            '📝': '[NOTE]',
            '📁': '[FOLDER]',
            '🐛': '[BUG]',
            '🔍': '[SEARCH]',
            '📋': '[CLIPBOARD]',
            '📄': '[PAGE]',
            '📈': '[CHART]',
            '🚨': '[ALERT]',
            '🛠️': '[TOOLS]',
            '🎪': '[CIRCUS]',
            '💡': '[IDEA]',
            '⚡': '[LIGHTNING]',
            '🔥': '[FIRE]',
            '🎭': '[MASK]',
            '🎲': '[DICE]',
            '📦': '[PACKAGE]',
            '🔐': '[LOCK]',
            '🌐': '[GLOBE]',
            '💾': '[DISK]',
            '📡': '[SATELLITE]',
            '🔗': '[LINK]',
            '⚙️': '[GEAR]',
            '🏃': '[RUNNING]',
            '👥': '[USERS]',
            '💬': '[CHAT]',
            '📅': '[CALENDAR]',
            '⭐': '[STAR]',
            '✨': '[SPARKLE]',
            '🔄': '[REFRESH]',
            '📢': '[MEGAPHONE]'
        }
        
        self.utf8_header = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows-compatible debug tool with Unicode fixes applied
"""
import sys
import os

# Set UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

'''

    def fix_file(self, file_path):
        """Fix Unicode issues in a single file"""
        print(f"Fixing: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp1252') as f:
                    content = f.read()
            except:
                print(f"  ❌ Could not read {file_path}")
                return False
        
        original_content = content
        changes_made = 0
        
        # Replace emoji with ASCII equivalents
        for emoji, replacement in self.emoji_replacements.items():
            if emoji in content:
                content = content.replace(emoji, replacement)
                changes_made += 1
                print(f"  - Replaced '{emoji}' with '{replacement}'")
        
        # Add UTF-8 encoding handling if not present
        if '# -*- coding: utf-8 -*-' not in content and changes_made > 0:
            # Find the shebang line or first import
            lines = content.split('\n')
            insert_pos = 0
            
            for i, line in enumerate(lines):
                if line.startswith('#!'):
                    insert_pos = i + 1
                    break
                elif line.strip().startswith('import ') or line.strip().startswith('from '):
                    insert_pos = i
                    break
            
            # Insert UTF-8 header
            utf8_lines = [
                '# -*- coding: utf-8 -*-',
                '"""',
                'Windows-compatible debug tool with Unicode fixes applied', 
                '"""',
                'import sys',
                'import os',
                '',
                '# Set UTF-8 encoding for Windows compatibility',
                'if sys.platform.startswith(\'win\'):',
                '    import io',
                '    try:',
                '        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=\'utf-8\')',
                '        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding=\'utf-8\')',
                '    except AttributeError:',
                '        pass  # Already wrapped or not available',
                ''
            ]
            
            lines = lines[:insert_pos] + utf8_lines + lines[insert_pos:]
            content = '\n'.join(lines)
        
        if content != original_content:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ Fixed {changes_made} emoji characters")
                return True
            except Exception as e:
                print(f"  ❌ Could not write {file_path}: {e}")
                return False
        else:
            print(f"  ℹ️ No changes needed")
            return True
    
    def fix_all_debug_tools(self):
        """Fix all debug tools in the project"""
        print("🔧 Starting Unicode fix for all debug tools...")
        
        debug_files = [
            "debug/utilities/endpoint_validator.py",
            "debug/utilities/debug_endpoints.py", 
            "debug/utilities/verify_memory_pipeline.py",
            "debug/memory-tests/comprehensive_memory_test.py",
            "debug/memory-tests/test_openwebui_memory.py",
            "debug/memory-tests/test_openwebui_memory_fixed.py",
            "debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py",
            "debug/archived/demo-test/debug-tools/test_memory_cross_chat.py"
        ]
        
        fixed_count = 0
        total_count = len(debug_files)
        
        for file_path in debug_files:
            if os.path.exists(file_path):
                if self.fix_file(file_path):
                    fixed_count += 1
            else:
                print(f"⚠️ File not found: {file_path}")
        
        print(f"\n✅ Unicode fix complete: {fixed_count}/{total_count} files processed")
        
        # Also fix the main runner
        if os.path.exists("run_all_debug_tools.py"):
            print("\n🔧 Fixing main debug runner...")
            self.fix_file("run_all_debug_tools.py")
        
        return fixed_count == total_count

if __name__ == "__main__":
    fixer = UnicodeFixTool()
    success = fixer.fix_all_debug_tools()
    
    if success:
        print("\n🎯 All debug tools have been fixed for Windows compatibility!")
        print("📋 You can now run: python run_all_debug_tools.py")
    else:
        print("\n⚠️ Some files could not be fixed. Check the output above for details.")
