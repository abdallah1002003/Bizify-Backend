#!/usr/bin/env python3
"""
Clean Code Import Organizer
Automatically reorganizes imports in Python files according to PEP 8.
Groups: stdlib, third-party, local
"""

import re
from pathlib import Path
from typing import List, Tuple

# Known standard library modules (common ones)
STDLIB_MODULES = {
    'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections', 'contextlib',
    'copy', 'csv', 'datetime', 'decimal', 'enum', 'functools', 'hashlib',
    'http', 'io', 'itertools', 'json', 'logging', 'math', 'os', 'pathlib',
    'pickle', 're', 'secrets', 'shutil', 'socket', 'sqlite3', 'string',
    'subprocess', 'sys', 'tempfile', 'time', 'timeit', 'typing', 'unittest',
    'urllib', 'uuid', 'warnings', 'weakref', 'xml'
}

# Known third-party packages in this project
THIRD_PARTY_MODULES = {
    'fastapi', 'pydantic', 'sqlalchemy', 'passlib', 'jose', 'pytest',
    'requests', 'anthropic', 'openai', 'celery', 'redis', 'alembic',
    'uvicorn', 'starlette', 'httpx', 'psycopg2', 'bcrypt'
}

# Local modules (project-specific)
LOCAL_MODULES = {
    'core', 'database', 'models', 'schemas', 'services', 'routes',
    'middleware', 'dependencies', 'utils', 'config', 'main'
}

def categorize_import(import_line: str) -> str:
    """Categorize an import line into stdlib, third-party, or local."""
    # Extract the module name
    if import_line.startswith('from '):
        match = re.match(r'from\s+([a-zA-Z0-9_\.]+)', import_line)
        if match:
            module = match.group(1).split('.')[0]
        else:
            return 'local'
    elif import_line.startswith('import '):
        match = re.match(r'import\s+([a-zA-Z0-9_]+)', import_line)
        if match:
            module = match.group(1)
        else:
            return 'local'
    else:
        return 'local'
    
    # Categorize
    if module in STDLIB_MODULES:
        return 'stdlib'
    elif module in THIRD_PARTY_MODULES:
        return 'third_party'
    elif module in LOCAL_MODULES or module.startswith('.'):
        return 'local'
    else:
        # Default to third-party for unknown
        return 'third_party'

def extract_imports(content: str) -> Tuple[List[str], str]:
    """Extract import lines and return them with the rest of the content."""
    lines = content.split('\n')
    imports = []
    non_imports = []
    in_import_block = False
    docstring_start = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip module docstring
        if i < 5 and (stripped.startswith('"""') or stripped.startswith("'''")):
            non_imports.append(line)
            if stripped.count('"""') == 1 or stripped.count("'''") == 1:
                i += 1
                while i < len(lines):
                    non_imports.append(lines[i])
                    if '"""' in lines[i] or "'''" in lines[i]:
                        break
                    i += 1
            i += 1
            continue
        
        # Skip comments at the top
        if stripped.startswith('#'):
            non_imports.append(line)
            i += 1
            continue
        
        # Check if it's an import line
        if stripped.startswith('from ') or stripped.startswith('import '):
            in_import_block = True
            imports.append(line)
        elif in_import_block and stripped == '':
            # Empty line after imports - ignore it
            pass
        elif in_import_block:
            # End of import block
            non_imports.extend(lines[i:])
            break
        else:
            non_imports.append(line)
        
        i += 1
    
    return imports, '\n'.join(non_imports)

def organize_imports(imports: List[str]) -> str:
    """Organize imports into stdlib, third-party, and local groups."""
    if not imports:
        return ''
    
    stdlib = []
    third_party = []
    local = []
    
    for imp in imports:
        stripped = imp.strip()
        if not stripped:
            continue
        
        category = categorize_import(stripped)
        if category == 'stdlib':
            stdlib.append(stripped)
        elif category == 'third_party':
            third_party.append(stripped)
        else:
            local.append(stripped)
    
    # Sort each group
    stdlib.sort()
    third_party.sort()
    local.sort()
    
    # Combine with blank lines between groups
    result = []
    if stdlib:
        result.extend(stdlib)
    if third_party:
        if result:
            result.append('')
        result.extend(third_party)
    if local:
        if result:
            result.append('')
        result.extend(local)
    
    return '\n'.join(result)

def format_file(filepath: Path) -> bool:
    """Format imports in a single file. Returns True if modified."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        imports, rest = extract_imports(original_content)
        if not imports:
            return False
        
        organized = organize_imports(imports)
        
        # Reconstruct file
        new_content = organized + '\n\n' + rest.lstrip('\n')
        
        if new_content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        return False
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

def main():
    """Main function to organize imports in all backend files."""
    base_path = Path('/Users/abdallahabdelrhimantar/Desktop/p7')
    
    # Target directories
    targets = [
        base_path / 'routes',
        base_path / 'services',
        base_path / 'models',
        base_path / 'schemas',
        base_path / 'middleware',
    ]
    
    modified_count = 0
    total_count = 0
    
    for target_dir in targets:
        if not target_dir.exists():
            continue
        
        for py_file in target_dir.rglob('*.py'):
            if py_file.name == '__init__.py':
                continue
            
            total_count += 1
            if format_file(py_file):
                modified_count += 1
                print(f"✅ Organized: {py_file.relative_to(base_path)}")
            else:
                print(f"⏭️  Skipped: {py_file.relative_to(base_path)}")
    
    print(f"\n{'='*60}")
    print(f"✨ Import organization complete!")
    print(f"📊 Modified: {modified_count}/{total_count} files")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
