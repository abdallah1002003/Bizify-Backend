#!/usr/bin/env python3
"""
📝 Type Hint Adder - Add Missing Type Hints

Automatically adds type hints to functions missing them.
Created by: Autonomous System
Priority: MEDIUM
"""

from pathlib import Path
from typing import List
import re
import ast

class TypeHintAdder:
    """Add type hints to Python files"""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
    
    def find_files_needing_hints(self) -> List[Path]:
        """Find Python files that likely need type hints"""
        files_needing_hints = []
        
        for directory in [self.project_root / "services", self.project_root / "routes"]:
            if not directory.exists():
                continue
            
            for py_file in directory.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                
                content = py_file.read_text()
                
                # Check if file has functions but no type hints
                if "def " in content and " -> " not in content:
                    files_needing_hints.append(py_file)
        
        return files_needing_hints
    
    def add_basic_hints_to_file(self, file_path: Path) -> bool:
        """
        Add basic type hints to a file
        
        Returns True if changes made
        """
        content = file_path.read_text()
        
        # Parse AST
        try:
            tree = ast.parse(content)
        except:
            return False
        
        lines = content.split('\n')
        modified = False
        
        # Find functions without type hints
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.returns and not any(arg.annotation for arg in node.args.args):
                    # This function needs hints
                    # For now, we'll just add basic hints
                    func_line = node.lineno - 1
                    
                    if func_line < len(lines):
                        line = lines[func_line]
                        
                        # Extract function signature
                        match = re.match(r'(\s*)def\s+(\w+)\s*\((.*?)\)\s*:', line)
                        if match:
                            indent, func_name, params = match.groups()
                            
                            # Add return type hint
                            new_line = f"{indent}def {func_name}({params}) -> None:"
                            lines[func_line] = new_line
                            modified = True
        
        if modified:
            file_path.write_text('\n'.join(lines))
            return True
        
        return False
    
    def add_import_hints(self, file_path: Path):
        """Add typing imports if needed"""
        content = file_path.read_text()
        
        if "from typing import" in content or "import typing" in content:
            return  # Already has typing imports
        
        # Add after other imports
        lines = content.split('\n')
        
        # Find last import line
        last_import = 0
        for i, line in enumerate(lines):
            if line.strip().startswith(('import ', 'from ')):
                last_import = i
        
        # Insert typing import
        lines.insert(last_import + 1, "from typing import Optional, Dict, List, Any")
        
        file_path.write_text('\n'.join(lines))

def main():
    """Add type hints to files"""
    print("\n📝 TYPE HINT ADDER - Finding Files\n")
    
    project_root = Path.cwd()
    adder = TypeHintAdder(project_root)
    
    files = adder.find_files_needing_hints()
    
    print(f"Found {len(files)} file(s) needing type hints:\n")
    
    for file in files[:10]:  # First 10
        print(f"  - {file.relative_to(project_root)}")
    
    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more")
    
    print(f"\n✅ Type hints needed in {len(files)} files")
    print("   (Manual implementation recommended for accuracy)")

if __name__ == "__main__":
    main()
