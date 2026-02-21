#!/usr/bin/env python3
"""
File Indexer - Fast File Lookup System
Builds and maintains an index of all project files for instant access
"""
import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
import ast

logger = logging.getLogger(__name__)

class FileIndexer:
    """
    Builds and maintains a fast-access index of all project files.
    Provides O(1) lookup for file metadata and relationships.
    """
    
    def __init__(self, project_root: Path):
        logger.info('Initializing File Indexer')
        self.project_root = Path(project_root)
        self.index_file = self.project_root / "autonomous_reports" / "file_index.json"
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory index for fast access
        self.index: Dict[str, Dict] = {}
        self.import_graph: Dict[str, Set[str]] = {}
        
        # Load existing index if available
        self._load_index()
    
    def build_index(self, force_rebuild: bool = False) -> int:
        """
        Build complete file index.
        
        Args:
            force_rebuild: If True, rebuild even if index exists
        
        Returns:
            Number of files indexed
        """
        if not force_rebuild and self.index:
            logger.info(f'Index already loaded with {len(self.index)} files')
            return len(self.index)
        
        logger.info('Building file index...')
        start_time = time.time()
        
        # Clear existing index
        self.index = {}
        self.import_graph = {}
        
        # Scan Python files
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            # Skip virtual environments and cache
            if any(part in file_path.parts for part in ['.venv', 'venv', '__pycache__', '.git']):
                continue
            
            try:
                self._index_file(file_path)
            except Exception as e:
                logger.warning(f'Failed to index {file_path}: {e}')
        
        # Save index
        self._save_index()
        
        elapsed = time.time() - start_time
        logger.info(f'✅ Indexed {len(self.index)} files in {elapsed:.2f}s')
        
        return len(self.index)
    
    def _index_file(self, file_path: Path):
        """Index a single file."""
        relative_path = str(file_path.relative_to(self.project_root))
        
        # Get file stats
        stats = file_path.stat()
        
        # Read file content
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.warning(f'Cannot read {file_path}: {e}')
            return
        
        # Extract metadata
        metadata = {
            'path': relative_path,
            'absolute_path': str(file_path),
            'size': stats.st_size,
            'modified': stats.st_mtime,
            'lines': len(content.splitlines()),
            'functions': [],
            'classes': [],
            'imports': [],
            'last_indexed': time.time()
        }
        
        # Parse Python AST for structure
        try:
            tree = ast.parse(content)
            
            # Extract functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metadata['functions'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'args': [arg.arg for arg in node.args.args]
                    })
                elif isinstance(node, ast.ClassDef):
                    metadata['classes'].append({
                        'name': node.name,
                        'line': node.lineno
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            metadata['imports'].append(alias.name)
                    else:
                        if node.module:
                            metadata['imports'].append(node.module)
        
        except SyntaxError:
            # File has syntax errors, skip AST parsing
            pass
        
        # Store in index
        self.index[relative_path] = metadata
        
        # Build import graph
        if metadata['imports']:
            self.import_graph[relative_path] = set(metadata['imports'])
    
    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """
        Get cached file info instantly.
        
        Args:
            file_path: Relative or absolute path
        
        Returns:
            File metadata or None
        """
        # Normalize path
        if file_path.startswith('/'):
            try:
                file_path = str(Path(file_path).relative_to(self.project_root))
            except ValueError:
                return None
        
        return self.index.get(file_path)
    
    def find_files_by_name(self, name: str) -> List[Dict]:
        """
        Find files by name pattern.
        
        Args:
            name: File name or pattern
        
        Returns:
            List of matching files
        """
        results = []
        name_lower = name.lower()
        
        for path, metadata in self.index.items():
            if name_lower in Path(path).name.lower():
                results.append(metadata)
        
        return results
    
    def find_files_with_function(self, function_name: str) -> List[Dict]:
        """Find files containing a specific function."""
        results = []
        
        for path, metadata in self.index.items():
            for func in metadata.get('functions', []):
                if func['name'] == function_name:
                    results.append({
                        'file': metadata,
                        'function': func
                    })
        
        return results
    
    def find_files_with_class(self, class_name: str) -> List[Dict]:
        """Find files containing a specific class."""
        results = []
        
        for path, metadata in self.index.items():
            for cls in metadata.get('classes', []):
                if cls['name'] == class_name:
                    results.append({
                        'file': metadata,
                        'class': cls
                    })
        
        return results
    
    def get_related_files(self, file_path: str) -> List[str]:
        """
        Find files related to this one through imports.
        
        Args:
            file_path: File to find relations for
        
        Returns:
            List of related file paths
        """
        # Normalize path
        if file_path.startswith('/'):
            try:
                file_path = str(Path(file_path).relative_to(self.project_root))
            except ValueError:
                return []
        
        related = set()
        
        # Files this one imports
        if file_path in self.import_graph:
            for import_name in self.import_graph[file_path]:
                # Try to find the imported file
                for indexed_path in self.index.keys():
                    if import_name.replace('.', '/') in indexed_path:
                        related.add(indexed_path)
        
        # Files that import this one
        for other_path, imports in self.import_graph.items():
            file_module = file_path.replace('/', '.').replace('.py', '')
            if any(file_module in imp for imp in imports):
                related.add(other_path)
        
        return list(related)
    
    def get_stats(self) -> Dict:
        """Get index statistics."""
        total_lines = sum(f.get('lines', 0) for f in self.index.values())
        total_functions = sum(len(f.get('functions', [])) for f in self.index.values())
        total_classes = sum(len(f.get('classes', [])) for f in self.index.values())
        
        return {
            'total_files': len(self.index),
            'total_lines': total_lines,
            'total_functions': total_functions,
            'total_classes': total_classes,
            'index_size': len(json.dumps(self.index)),
            'last_built': max((f.get('last_indexed', 0) for f in self.index.values()), default=0)
        }
    
    def _save_index(self):
        """Save index to disk."""
        try:
            # Convert sets to lists for JSON serialization
            serializable_graph = {k: list(v) for k, v in self.import_graph.items()}
            
            data = {
                'index': self.index,
                'import_graph': serializable_graph,
                'built_at': time.time()
            }
            
            self.index_file.write_text(json.dumps(data, indent=2))
            logger.info(f'✅ Index saved to {self.index_file}')
        except Exception as e:
            logger.error(f'Failed to save index: {e}')
    
    def _load_index(self):
        """Load index from disk."""
        if not self.index_file.exists():
            logger.info('No existing index found')
            return
        
        try:
            data = json.loads(self.index_file.read_text())
            self.index = data.get('index', {})
            
            # Convert lists back to sets
            graph = data.get('import_graph', {})
            self.import_graph = {k: set(v) for k, v in graph.items()}
            
            logger.info(f'✅ Loaded index with {len(self.index)} files')
        except Exception as e:
            logger.error(f'Failed to load index: {e}')
            self.index = {}
            self.import_graph = {}
    
    def update_file(self, file_path: Path):
        """Update index for a single file (for incremental updates)."""
        try:
            self._index_file(file_path)
            self._save_index()
            logger.info(f'✅ Updated index for {file_path}')
        except Exception as e:
            logger.error(f'Failed to update {file_path}: {e}')

# CLI for testing and building
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='File Indexer CLI')
    parser.add_argument('--build', action='store_true', help='Build the index')
    parser.add_argument('--silent', action='store_true', help='Suppress output')
    args = parser.parse_args()
    
    log_level = logging.ERROR if args.silent else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    indexer = FileIndexer(Path.cwd())
    
    if args.build:
        count = indexer.build_index()
        if not args.silent:
            print(f"✅ Indexed {count} files")
        sys.exit(0)
    
    print("🗂️  File Indexer\n")
    print("=" * 70)
    
    # Build index
    print("\n📊 Building index...")
    count = indexer.build_index()
    print(f"✅ Indexed {count} files")
    
    # Show stats
    stats = indexer.get_stats()
    print(f"\n📈 Statistics:")
    print(f"   Files: {stats['total_files']:,}")
    print(f"   Lines: {stats['total_lines']:,}")
    print(f"   Functions: {stats['total_functions']:,}")
    print(f"   Classes: {stats['total_classes']:,}")
    
    # Test search
    print(f"\n🔍 Testing search...")
    results = indexer.find_files_by_name("web_researcher")
    if results:
        print(f"   Found: {results[0]['path']}")
        print(f"   Functions: {len(results[0]['functions'])}")
        print(f"   Lines: {results[0]['lines']}")
    
    # Test related files
    if results:
        related = indexer.get_related_files(results[0]['path'])
        print(f"\n🔗 Related files:")
        for r in related[:5]:
            print(f"   • {r}")
    
    print("\n" + "=" * 70)
    print("✅ File Indexer ready!")
