#!/usr/bin/env python3
"""Fix Unicode emojis in comprehensive_analysis.py for Windows compatibility."""

import re

def fix_unicode_emojis():
    """Replace Unicode emojis with ASCII equivalents."""
    
    # Read the file
    with open('comprehensive_analysis.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace emojis with ASCII equivalents
    replacements = {
        '🔍': '[*]',
        '1️⃣': '1.',
        '2️⃣': '2.',
        '3️⃣': '3.',
        '4️⃣': '4.',
        '5️⃣': '5.',
        '6️⃣': '6.',
        '❌': '[X]',
        '✅': '[OK]',
        '⚠️': '[!]',
        '📁': '',
        '🔄': '[DUP]',
        '📊': '[STATS]',
        '📋': '[SUMMARY]'
    }
    
    for emoji, replacement in replacements.items():
        content = content.replace(emoji, replacement)
    
    # Write back to file
    with open('comprehensive_analysis.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed Unicode emojis in comprehensive_analysis.py")

if __name__ == '__main__':
    fix_unicode_emojis()
