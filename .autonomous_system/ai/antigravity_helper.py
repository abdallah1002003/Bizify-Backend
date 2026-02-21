#!/usr/bin/env python3
"""
Antigravity Helper
Proactively assists Antigravity by finding and preparing relevant files
"""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai.smart_search import SmartSearch
from app.core.session_detector import AntigravitySessionDetector

logger = logging.getLogger(__name__)

class AntigravityHelper:
    """
    Assistant that uses Smart Search to help Antigravity work faster.
    """
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.search = SmartSearch(self.project_root)
        self.session_detector = AntigravitySessionDetector(self.project_root)
        
    def prepare_context(self, intent: str) -> Dict:
        """
        Prepare all necessary context for a given intent/task.
        
        Args:
            intent: Description of what Antigravity wants to do
            
        Returns:
            Dict containing relevant files, snippets, and suggestions
        """
        logger.info(f"Helper preparing context for: '{intent}'")
        
        # Get file suggestions from Smart Search
        suggestions = self.search.suggest_files(intent)
        
        context = {
            'intent': intent,
            'primary_files': suggestions['primary'],
            'related_files': suggestions['related'],
            'tests': suggestions['tests'],
            'snippets': {},
            'tips': []
        }
        
        # Extract key snippets from primary files
        for file_path in suggestions['primary']:
            # Try to get class definition if it matches file name
            stem = Path(file_path).stem
            # Convert snake_case to CamelCase (simple heuristic)
            class_name = ''.join(word.title() for word in stem.split('_'))
            
            snippet = self.search.get_code_snippet(file_path, class_name)
            if snippet:
                context['snippets'][f"{file_path}:{class_name}"] = snippet
                
        # Generate tips
        if not self.session_detector.is_antigravity_active():
            context['tips'].append("⚠️ Antigravity session is not active. Start it to enable full features.")
            
        if suggestions['tests']:
            context['tips'].append(f"✅ Found {len(suggestions['tests'])} relevant tests. Run them to verify changes.")
            
        return context

    def quick_find(self, query: str) -> None:
        """
        Print quick results for a query (CLI usage).
        """
        print(f"\n🔍 Quick Find: '{query}'")
        print("=" * 50)
        
        context = self.prepare_context(query)
        
        print("\n📂 Primary Files:")
        if context['primary_files']:
            for f in context['primary_files']:
                print(f"  • {f}")
        else:
            print("  (No direct matches found)")
            
        print("\n🔗 Related Files:")
        if context['related_files']:
            for f in context['related_files']:
                print(f"  • {f}")
        else:
            print("  (No related files found)")
            
        print("\n🧪 Relevant Tests:")
        if context['tests']:
            for f in context['tests']:
                print(f"  • {f}")
        else:
            print("  (No tests found)")
            
        if context['tips']:
            print("\n💡 Tips:")
            for tip in context['tips']:
                print(f"  {tip}")
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "session detection"
        
    logging.basicConfig(level=logging.ERROR)
    
    helper = AntigravityHelper(Path.cwd())
    helper.quick_find(query)
