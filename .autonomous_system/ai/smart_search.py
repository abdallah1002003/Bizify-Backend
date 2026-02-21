#!/usr/bin/env python3
"""
Smart Search Engine
Provides intelligent, context-aware file searches and code snippets
"""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai.file_indexer import FileIndexer

logger = logging.getLogger(__name__)

class SmartSearch:
    """
    Intelligent search engine that understands code context.
    Uses FileIndexer to provide fast, relevant results.
    """
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.indexer = FileIndexer(self.project_root)
        # Ensure index is ready
        if not self.indexer.index:
            self.indexer.build_index()
            
    def search_by_context(self, context: str, limit: int = 5) -> List[Dict]:
        """
        Find relevant files based on natural language context.
        
        Args:
            context: Description of what you're looking for (e.g., "auth system", "error handling")
            limit: Max results to return
            
        Returns:
            List of file metadata dicts
        """
        # Simple keyword matching for now (could be enhanced with embeddings later)
        keywords = context.lower().split()
        scores = []
        
        for path, metadata in self.indexer.index.items():
            score = 0
            path_lower = path.lower()
            
            # Score based on filename matches
            for kw in keywords:
                if kw in path_lower:
                    score += 10
                    # Bonus for exact word match in filename
                    if f"/{kw}." in path_lower or f"_{kw}" in path_lower:
                        score += 5
            
            # Score based on function/class names
            for func in metadata.get('functions', []):
                for kw in keywords:
                    if kw in func['name'].lower():
                        score += 3
            
            for cls in metadata.get('classes', []):
                for kw in keywords:
                    if kw in cls['name'].lower():
                        score += 5
            
            if score > 0:
                scores.append((score, metadata))
        
        # Sort by score desc
        scores.sort(key=lambda x: x[0], reverse=True)
        
        return [item[1] for item in scores[:limit]]

    def get_code_snippet(self, file_path: str, target_name: str, context_lines: int = 0) -> Optional[str]:
        """
        Get a specific code snippet (function or class) without reading the whole file.
        
        Args:
            file_path: Relative path to file
            target_name: Name of function or class to extract
            context_lines: Number of extra lines to include
            
        Returns:
            String containing the code snippet or None
        """
        metadata = self.indexer.get_file_info(file_path)
        if not metadata:
            return None
            
        target_line = -1
        
        # Find target in functions
        for func in metadata.get('functions', []):
            if func['name'] == target_name:
                target_line = func['line']
                break
                
        # Find target in classes
        if target_line == -1:
            for cls in metadata.get('classes', []):
                if cls['name'] == target_name:
                    target_line = cls['line']
                    break
        
        if target_line == -1:
            return None
            
        # Read file and extract snippet
        # We need to read lines to find the end of the block (indentation based)
        full_path = self.project_root / file_path
        try:
            lines = full_path.read_text(encoding='utf-8').splitlines()
        except:
            return None
            
        start_idx = max(0, target_line - 1 - context_lines)
        target_idx = target_line - 1
        
        if target_idx >= len(lines):
            return None
            
        # Determine indentation of the target definition
        target_indent = len(lines[target_idx]) - len(lines[target_idx].lstrip())
        
        end_idx = target_idx + 1
        
        # Scan forward to find end of block (next line with same or less indentation that isn't empty)
        while end_idx < len(lines):
            line = lines[end_idx]
            if not line.strip(): # Skip empty lines
                end_idx += 1
                continue
                
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= target_indent:
                break
            end_idx += 1
            
        return '\n'.join(lines[start_idx:end_idx])

    def suggest_files(self, intent: str) -> Dict[str, List[str]]:
        """
        Suggest a package of files based on intent.
        
        Returns:
            Dict with 'primary', 'related', 'tests' lists of file paths
        """
        primary_files = self.search_by_context(intent, limit=3)
        primary_paths = [f['path'] for f in primary_files]
        
        related_paths = set()
        test_paths = set()
        
        for p in primary_paths:
            # Add related files (imports)
            related = self.indexer.get_related_files(p)
            for r in related:
                if r not in primary_paths:
                    related_paths.add(r)
            
            # Try to find associated tests
            # Assumption: tests are often named test_filename.py or similar
            name_stem = Path(p).stem
            test_candidates = self.indexer.find_files_by_name(f"test_{name_stem}")
            for t in test_candidates:
                test_paths.add(t['path'])
                
        return {
            'primary': primary_paths,
            'related': list(related_paths)[:5], # Limit related
            'tests': list(test_paths)
        }

if __name__ == "__main__":
    # Test CLI
    import sys
    
    # Add project root to path
    sys.path.insert(0, str(Path.cwd()))
    
    # Re-import after path fix
    try:
        from ai.smart_search import SmartSearch
    except ImportError:
        # If running directly, we might need to adjust import
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from ai.smart_search import SmartSearch

    logging.basicConfig(level=logging.INFO)
    
    search = SmartSearch(Path.cwd())
    
    print("🔍 Smart Search Engine Test")
    print("="*50)
    
    query = "web research"
    print(f"\nSearching for: '{query}'")
    results = search.search_by_context(query)
    for res in results:
        print(f"  • {res['path']}")
        
    if results:
        target = "WebKnowledgeRetriever"
        target_file = results[0]['path']
        print(f"\nExtracting '{target}' from {target_file}...")
        snippet = search.get_code_snippet(target_file, target)
        if snippet:
            print(f"✅ Snippet found ({len(snippet.splitlines())} lines)")
            print("-" * 20)
            print('\n'.join(snippet.splitlines()[:5]) + "\n...")
            
    print("\nSuggestions for 'error handling':")
    suggestions = search.suggest_files("error handling")
    print("Primary:", suggestions['primary'])
    print("Related:", suggestions['related'])
    print("Tests:", suggestions['tests'])
