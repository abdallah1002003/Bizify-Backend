from functools import lru_cache
"""
Auto-Fix Engine - Intelligent Code Repair System
Detects issues, applies fixes, tests them, and learns patterns.
"""

import ast
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import subprocess

logger = logging.getLogger(__name__)

@dataclass
class CodeIssue:
    """Represents a detected code issue."""
    file_path: Path
    line_number: int
    issue_type: str  # 'nested_loop', 'hardcoded_secret', 'missing_cache', etc.
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    original_code: str
    suggested_fix: Optional[str] = None

@dataclass
class FixResult:
    """Result of applying a fix."""
    success: bool
    issue: CodeIssue
    applied_fix: str
    test_passed: bool
    error_message: Optional[str] = None

class AutoFixEngine:
    """
    Intelligent auto-fix engine that:
    1. Detects code issues
    2. Generates and applies fixes
    3. Tests the fixes
    4. Learns successful patterns
    """
    
    def __init__(self, project_root: Path):
        logger.info('Professional Grade Execution: Entering method')
        self.project_root = project_root
        self.fixes_applied = []
        self.patterns_learned = []
        
        # Fix strategies
        self.fix_strategies = {
            'nested_loop': self._fix_nested_loop,
            'hardcoded_secret': self._fix_hardcoded_secret,
            'missing_cache': self._fix_missing_cache,
            'unsafe_eval': self._fix_unsafe_eval,
        }
    
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    def detect_issues(self, file_path: Path) -> List[CodeIssue]:
        """Detect all issues in a file."""
        if not file_path.exists() or file_path.suffix != '.py':
            return []
        
        issues = []
        content = file_path.read_text()
        lines = content.split('\n')
        
        try:
            tree = ast.parse(content)
            
            # Detect nested loops
            issues.extend(self._detect_nested_loops(file_path, tree, lines))
            
            # Detect hardcoded secrets
            issues.extend(self._detect_hardcoded_secrets(file_path, lines))
            
            # Detect missing caching opportunities
            issues.extend(self._detect_missing_cache(file_path, tree, lines))
            
            # Detect unsafe eval
            issues.extend(self._detect_unsafe_eval(file_path, tree, lines))
            
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        
        return issues
    
    def _detect_nested_loops(self, file_path: Path, tree: ast.AST, lines: List[str]) -> List[CodeIssue]:
        logger.info('Professional Grade Execution: Entering method')
        """Detect nested loops that can be optimized."""
        issues = []
        
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Check if there's a nested loop
                for child in ast.walk(node):
                    if child != node and isinstance(child, ast.For):
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type='nested_loop',
                            severity='medium',
                            description='Nested loop detected - can be optimized',
                            original_code=lines[node.lineno - 1] if node.lineno <= len(lines) else ''
                        ))
                        break
        
        return issues
    
    def _detect_hardcoded_secrets(self, file_path: Path, lines: List[str]) -> List[CodeIssue]:
        logger.info('Professional Grade Execution: Entering method')
        """Detect hardcoded secrets."""
        issues = []
        # 🛑 SECURITY CRITICAL: Hardcoded secret detected. Move to environment variables.
        # 🛑 SECURITY CRITICAL: Hardcoded secret detected. Move to environment variables.
        # 🛑 SECURITY CRITICAL: Hardcoded secret detected. Move to environment variables.
        # 🛑 SECURITY CRITICAL: Hardcoded secret detected. Move to environment variables.
        # 🛑 SECURITY CRITICAL: Hardcoded secret detected. Move to environment variables.
        # 🛑 SECURITY CRITICAL: Hardcoded secret detected. Move to environment variables.
        # 🛑 SECURITY CRITICAL: Hardcoded secret detected. Move to environment variables.
        secret_patterns = [
            (r'api[_-]?key\s*=\s*["\']([^"\']+)["\']', 'API key'),
            (r'password\s*=\s*["\']([^"\']+)["\']', 'Password'),
            (r'secret\s*=\s*["\']([^"\']+)["\']', 'Secret'),
            (r'token\s*=\s*["\']([^"\']+)["\']', 'Token'),
        ]
        
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for line_num, line in enumerate(lines, 1):
            for pattern, secret_type in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip if it's already using os.environ or getenv
                    if 'os.environ' not in line and 'getenv' not in line:
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=line_num,
                            issue_type='hardcoded_secret',
                            severity='critical',
                            description=f'Hardcoded {secret_type} detected',
                            original_code=line.strip()
                        ))
        
        return issues
    
    def _detect_missing_cache(self, file_path: Path, tree: ast.AST, lines: List[str]) -> List[CodeIssue]:
        logger.info('Professional Grade Execution: Entering method')
        """Detect functions that should be cached."""
        issues = []
        
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has no side effects and returns a value
                has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
                has_cache = any(
                    isinstance(d, ast.Name) and 'cache' in d.id.lower()
                    for d in node.decorator_list
                )
                
                # Simple heuristic: if it has return and no cache, suggest caching
                if has_return and not has_cache and len(node.args.args) > 0:
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type='missing_cache',
                        severity='low',
                        description=f'Function {node.name} could benefit from caching',
                        original_code=lines[node.lineno - 1] if node.lineno <= len(lines) else ''
                    ))
        
        return issues
    
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    def _detect_unsafe_eval(self, file_path: Path, tree: ast.AST, lines: List[str]) -> List[CodeIssue]:
        logger.info('Professional Grade Execution: Entering method')
        """Detect unsafe eval usage."""
        issues = []
        
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'eval':
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type='unsafe_eval',
                        severity='high',
                        description='Unsafe eval() detected',
                        original_code=lines[node.lineno - 1] if node.lineno <= len(lines) else ''
                    ))
        
        return issues
    
    def apply_fix(self, issue: CodeIssue) -> FixResult:
        """Apply a fix for the given issue."""
        strategy = self.fix_strategies.get(issue.issue_type)
        
        if not strategy:
            return FixResult(
                success=False,
                issue=issue,
                applied_fix='',
                test_passed=False,
                error_message=f'No fix strategy for {issue.issue_type}'
            )
        
        try:
            # Generate fix
            fixed_code = strategy(issue)
            
            if not fixed_code:
                return FixResult(
                    success=False,
                    issue=issue,
                    applied_fix='',
                    test_passed=False,
                    error_message='Fix generation failed'
                )
            
            # Apply fix to file
            content = issue.file_path.read_text()
            lines = content.split('\n')
            
            # Replace the line
            if 1 <= issue.line_number <= len(lines):
                lines[issue.line_number - 1] = fixed_code
                new_content = '\n'.join(lines)
                
                # Backup original
                backup_path = issue.file_path.with_suffix('.py.backup')
                issue.file_path.write_text(content)  # Save backup
                backup_path.write_text(content)
                
                # Write fixed version
                issue.file_path.write_text(new_content)
                
                # Test the fix
                test_passed = self._test_fix(issue.file_path)
                
                if test_passed:
                    # Remove backup
                    if backup_path.exists():
                        backup_path.unlink()
                    
                    # Learn the pattern
                    self._learn_pattern(issue, fixed_code)
                    
                    return FixResult(
                        success=True,
                        issue=issue,
                        applied_fix=fixed_code,
                        test_passed=True
                    )
                else:
                    # Restore backup
                    issue.file_path.write_text(content)
                    if backup_path.exists():
                        backup_path.unlink()
                    
                    return FixResult(
                        success=False,
                        issue=issue,
                        applied_fix=fixed_code,
                        test_passed=False,
                        error_message='Fix caused test failure'
                    )
            
        except Exception as e:
            logger.error(f"Error applying fix: {e}")
            return FixResult(
                success=False,
                issue=issue,
                applied_fix='',
                test_passed=False,
                error_message=str(e)
            )
    
    def _fix_nested_loop(self, issue: CodeIssue) -> Optional[str]:
        logger.info('Professional Grade Execution: Entering method')
        """Generate fix for nested loop."""
        # Simple strategy: add comment suggesting list comprehension
        return f"    # TODO: Consider list comprehension or vectorization\n{issue.original_code}"
    
    def _fix_hardcoded_secret(self, issue: CodeIssue) -> Optional[str]:
        logger.info('Professional Grade Execution: Entering method')
        """Generate fix for hardcoded secret."""
        # Extract variable name
        match = re.search(r'(\w+)\s*=\s*["\']([^"\']+)["\']', issue.original_code)
        if match:
            var_name = match.group(1)
            # Replace with environment variable
            indent = len(issue.original_code) - len(issue.original_code.lstrip())
            return f"{' ' * indent}{var_name} = os.getenv('{var_name.upper()}', '')"
        return None
    
    def _fix_missing_cache(self, issue: CodeIssue) -> Optional[str]:
        logger.info('Professional Grade Execution: Entering method')
        """Generate fix for missing cache."""
        # Add @lru_cache decorator
        indent = len(issue.original_code) - len(issue.original_code.lstrip())
        return f"{' ' * indent}@lru_cache(maxsize=128)\n{issue.original_code}"
    
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.    
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    def _fix_unsafe_eval(self, issue: CodeIssue) -> Optional[str]:
        logger.info('Professional Grade Execution: Entering method')
        """Generate fix for unsafe eval."""
        # Replace eval with ast.literal_eval
        fixed = issue.original_code.replace('eval(', 'ast.literal_eval(')
        return fixed
    
    def _test_fix(self, file_path: Path) -> bool:
        """Test if the fix doesn't break the code."""
        try:
            # Try to compile the file
            content = file_path.read_text()
            compile(content, str(file_path), 'exec')
            
            # Try to import if it's a module
            # (This is a simple test, more sophisticated testing can be added)
            return True
        except Exception as e:
            logger.error(f"Fix test failed: {e}")
            return False
    
    def _learn_pattern(self, issue: CodeIssue, fix: str) -> None:
        """Learn from successful fix."""
        pattern = {
            'issue_type': issue.issue_type,
            'severity': issue.severity,
            'original': issue.original_code,
            'fixed': fix,
            'file': str(issue.file_path),
            'success': True
        }
        
        self.patterns_learned.append(pattern)
        logger.info(f"✅ Learned pattern: {issue.issue_type} fix")
    
    def process_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a file: detect issues and apply fixes."""
        logger.info(f"🔍 Processing {file_path}")
        
        issues = self.detect_issues(file_path)
        results = []
        
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.        
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for issue in issues:
            if issue.severity in ['high', 'critical']:
                logger.info(f"🔧 Fixing {issue.issue_type} at line {issue.line_number}")
                result = self.apply_fix(issue)
                results.append(result)
                
                if result.success:
                    logger.info(f"✅ Fix applied successfully!")
                else:
                    logger.warning(f"❌ Fix failed: {result.error_message}")
        
        return {
            'file': str(file_path),
            'issues_detected': len(issues),
            'fixes_applied': sum(1 for r in results if r.success),
            'fixes_failed': sum(1 for r in results if not r.success),
            'results': results
        }
    
    def save_learned_patterns(self, output_path: Path) -> None:
        """Save learned patterns to file."""
        output_path.write_text(json.dumps(self.patterns_learned, indent=2))
        logger.info(f"💾 Saved {len(self.patterns_learned)} learned patterns")

def main():
    logger.info('Professional Grade Execution: Entering method')
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-Fix Engine")
    parser.add_argument("file", type=Path, help="File to process")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    engine = AutoFixEngine(args.project_root)
    result = engine.process_file(args.file)
    
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
