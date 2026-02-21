#!/usr/bin/env python3
"""
Auto-fix empty import statements in test files
"""
import os
import re
from pathlib import Path

def fix_empty_imports(project_root):
    """Fix all empty import statements in test files"""
    test_dir = Path(project_root) / 'tests' / 'unit' / 'services'
    fixed_files = []
    
    for filepath in test_dir.rglob('test_*.py'):
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Pattern to match empty imports like: from X import (\n\n)
            pattern = r'from\s+[\w\.]+\s+import\s*\(\s*\)\s*\n'
            
            if re.search(pattern, content):
                new_content = re.sub(pattern, '', content)
                
                with open(filepath, 'w') as f:
                    f.write(new_content)
                
                fixed_files.append(str(filepath.relative_to(project_root)))
                print(f"✅ Fixed: {filepath.relative_to(project_root)}")
        
        except Exception as e:
            print(f"⚠️ Error processing {filepath}: {e}")
    
    return fixed_files

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    print("\n🔧 Fixing syntax errors in test files...\n")
    
    fixed = fix_empty_imports(project_root)
    
    print(f"\n✨ Fixed {len(fixed)} files!\n")
    
    # Run pytest to verify
    print("Running pytest to verify fixes...\n")
    os.system("cd " + str(project_root) + " && python -m pytest --collect-only -q | head -20")
