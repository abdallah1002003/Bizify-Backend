#!/usr/bin/env python3
"""
Clean Code Analyzer - Type Hints & Naming Conventions
Analyzes backend files for:
1. Missing type hints
2. Naming convention violations
3. Code quality metrics
"""

import ast
import re
from pathlib import Path
from typing import Dict

class CleanCodeAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze code quality."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.issues = []
        self.stats = {
            'functions': 0,
            'functions_with_hints': 0,
            'classes': 0,
            'constants': 0,
            'naming_violations': 0
        }
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Analyze function definitions."""
        self.stats['functions'] += 1
        
        # Check if function has type hints
        has_return_hint = node.returns is not None
        has_param_hints = all(
            arg.annotation is not None 
            for arg in node.args.args 
            if arg.arg != 'self' and arg.arg != 'cls'
        )
        
        if has_return_hint and has_param_hints:
            self.stats['functions_with_hints'] += 1
        elif self.stats['functions'] > 0 and not node.name.startswith('_'):
            # Only report public functions
            self.issues.append({
                'type': 'missing_type_hints',
                'line': node.lineno,
                'name': node.name,
                'message': f"Function '{node.name}' missing type hints"
            })
        
        # Check naming convention (should be snake_case)
        if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
            if not node.name.startswith('__'):  # Allow dunder methods
                self.stats['naming_violations'] += 1
                self.issues.append({
                    'type': 'naming_violation',
                    'line': node.lineno,
                    'name': node.name,
                    'message': f"Function '{node.name}' should use snake_case"
                })
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Analyze class definitions."""
        self.stats['classes'] += 1
        
        # Check naming convention (should be PascalCase)
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
            self.stats['naming_violations'] += 1
            self.issues.append({
                'type': 'naming_violation',
                'line': node.lineno,
                'name': node.name,
                'message': f"Class '{node.name}' should use PascalCase"
            })
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Analyze constant assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id
                # Check if it looks like a constant (ALL_CAPS)
                if name.isupper() and len(name) > 1:
                    self.stats['constants'] += 1
                # Check for camelCase variables (should be snake_case)
                elif re.match(r'^[a-z]+[A-Z]', name):
                    self.stats['naming_violations'] += 1
                    self.issues.append({
                        'type': 'naming_violation',
                        'line': node.lineno,
                        'name': name,
                        'message': f"Variable '{name}' should use snake_case, not camelCase"
                    })
        
        self.generic_visit(node)

def analyze_file(filepath: Path) -> Dict:
    """Analyze a single Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(filepath))
        analyzer = CleanCodeAnalyzer(str(filepath))
        analyzer.visit(tree)
        
        # Calculate type hint coverage
        coverage = 0
        if analyzer.stats['functions'] > 0:
            coverage = (analyzer.stats['functions_with_hints'] / analyzer.stats['functions']) * 100
        
        return {
            'filepath': filepath,
            'stats': analyzer.stats,
            'issues': analyzer.issues,
            'type_hint_coverage': coverage
        }
    except Exception as e:
        return {
            'filepath': filepath,
            'error': str(e),
            'stats': {},
            'issues': [],
            'type_hint_coverage': 0
        }

def main():
    """Main analyzer function."""
    base_path = Path('/Users/abdallahabdelrhimantar/Desktop/p7')
    
    # Target directories
    targets = [
        base_path / 'routes',
        base_path / 'services',
    ]
    
    all_results = []
    total_issues = 0
    total_functions = 0
    total_with_hints = 0
    
    print("=" * 70)
    print("🔍 CLEAN CODE ANALYSIS - Type Hints & Naming Conventions")
    print("=" * 70)
    print()
    
    for target_dir in targets:
        if not target_dir.exists():
            continue
        
        for py_file in target_dir.rglob('*.py'):
            if py_file.name == '__init__.py':
                continue
            
            result = analyze_file(py_file)
            all_results.append(result)
            
            if 'error' in result:
                print(f"❌ Error analyzing {py_file.relative_to(base_path)}: {result['error']}")
                continue
            
            stats = result['stats']
            issues = result['issues']
            coverage = result['type_hint_coverage']
            
            total_functions += stats.get('functions', 0)
            total_with_hints += stats.get('functions_with_hints', 0)
            total_issues += len(issues)
            
            # Report files with issues
            if issues:
                print(f"⚠️  {py_file.relative_to(base_path)}")
                print(f"   Type Hint Coverage: {coverage:.1f}%")
                print(f"   Functions: {stats['functions']} ({stats['functions_with_hints']} with hints)")
                print(f"   Issues: {len(issues)}")
                for issue in issues[:3]:  # Show first 3 issues
                    print(f"     - Line {issue['line']}: {issue['message']}")
                if len(issues) > 3:
                    print(f"     ... and {len(issues) - 3} more")
                print()
    
    # Summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total Functions: {total_functions}")
    print(f"With Type Hints: {total_with_hints}")
    if total_functions > 0:
        overall_coverage = (total_with_hints / total_functions) * 100
        print(f"Overall Type Hint Coverage: {overall_coverage:.1f}%")
    print(f"Total Issues Found: {total_issues}")
    print("=" * 70)
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if overall_coverage < 80:
        print(f"   - Type hint coverage is {overall_coverage:.1f}% - aim for 80%+")
    else:
        print(f"   ✅ Type hint coverage is good: {overall_coverage:.1f}%")
    
    if total_issues > 0:
        print(f"   - Fix {total_issues} naming/type hint issues")
    else:
        print("   ✅ No issues found!")

if __name__ == '__main__':
    main()
