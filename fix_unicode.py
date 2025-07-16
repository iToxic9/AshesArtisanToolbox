"""
Fix Unicode characters in test files for Windows compatibility
"""

import os
import re

def fix_unicode_in_file(filepath):
    """Replace Unicode check/cross marks with ASCII alternatives"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace Unicode characters
        replacements = {
            '✓': '[OK]',
            '✗': '[FAIL]',
            '🎉': '[SUCCESS]',
            '❌': '[ERROR]',
            '⚠': '[WARNING]',
            '📈': '[UP]',
            '📉': '[DOWN]',
            '➡️': '[STABLE]',
            '❓': '[UNKNOWN]',
            '❌': '[NO_DATA]'
        }
        
        for unicode_char, replacement in replacements.items():
            content = content.replace(unicode_char, replacement)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Fixed Unicode in {filepath}")
        return True
        
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

def main():
    """Fix Unicode in all test files"""
    files_to_fix = [
        'test_api_integration.py',
        'test_gui.py'
    ]
    
    for filename in files_to_fix:
        if os.path.exists(filename):
            fix_unicode_in_file(filename)
        else:
            print(f"File not found: {filename}")

if __name__ == "__main__":
    main()