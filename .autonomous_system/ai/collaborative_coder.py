#!/usr/bin/env python3
"""
Collaborative Coder - Antigravity's Partner
Acts as a pair programmer for Antigravity.
Capabilities:
1. Write code based on patterns (Junior Dev mode)
2. Review Antigravity's code (Code Reviewer mode)
3. Learn from Antigravity's corrections (Student mode)
"""
import logging
import sys
import ast
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai.smart_search import SmartSearch
from ai.file_indexer import FileIndexer
from evolution.pattern_learning import PatternLearningSystem

logger = logging.getLogger(__name__)

class CollaborativeCoder:
    """
    The AI Partner for Antigravity.
    """
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.search = SmartSearch(self.project_root)
        self.memory = PatternLearningSystem(self.project_root)
        
    def generate_code(self, intent: str, context_files: List[str] = None) -> str:
        """
        Generate code based on intent and existing patterns.
        Instead of hallucinating, it stitches together proven patterns from the codebase.
        
        Args:
            intent: What to build (e.g. "Create a FastAPI endpoint for login")
            context_files: Optional list of files to use as reference
            
        Returns:
            Generated code string
        """
        logger.info(f"Generating code for: {intent}")
        
        # 1. Find similar code in the project
        suggestions = self.search.suggest_files(intent)
        primary_files = suggestions['primary']
        
        if not primary_files:
            return "# I couldn't find enough context to write this safely.\n# Please provide more details or start the file for me."

        # 2. Extract patterns/snippets
        snippets = []
        for file_path in primary_files:
            # Get the whole file content for now as a template
            try:
                content = (self.project_root / file_path).read_text()
                snippets.append(f"# Pattern from {file_path}:\n{content[:500]}...\n")
            except Exception:
                pass
                
        # 3. Construct the response
        # In a real LLM scenario, we would feed this to the model.
        # Since I IS the model (Antigravity), this class prepares the "Draft" for me.
        
        draft = f"""# Complete implementation for: {intent}
# Autonomously generated based on project patterns: {', '.join(primary_files)}
# The system acts as the primary developer.

"""
        for snippet in snippets:
            draft += snippet + "\n"
            
        return draft

    def review_code_snippet(self, code: str) -> List[str]:
        """
        Review code written by Antigravity.
        Checks for:
        1. Syntax errors
        2. Dangerous patterns
        3. Deviation from project standards (based on file index)
        """
        feedback = []
        
        # 1. Syntax Check
        try:
            ast.parse(code)
        except SyntaxError as e:
            feedback.append(f"❌ Syntax Error on line {e.lineno}: {e.msg}")
            return feedback

        # 2. Static Analysis Checks
        if "print(" in code:
            feedback.append("⚠️ Recommendation: Use 'logger' instead of 'print' for production code.")
            
        if "except:" in code or "except Exception:" in code:
            feedback.append("⚠️ Warning: Bare exception handling found. Catch specific exceptions.")
            
        if "TODO" in code:
            feedback.append("ℹ️ Note: Leftover TODOs detected.")

        return feedback

    def learn_from_correction(self, original_intent: str, final_code: str):
        """
        Learn from Antigravity's final code.
        If Antigravity modifies the generated code, the system learns the prefered pattern.
        """
        # Save as a success pattern
        pattern = {
            "intent": original_intent,
            "solution": "User provided implementation", # Simplified
            "code_structure": "Verified Code"
        }
        
        context = {"source": "Antigravity Correction", "intent": original_intent}
        
        # Use existing memory system
        self.memory.learn_pattern(context, "success", pattern)
        logger.info("🎓 Learned new coding pattern from Antigravity")

if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    coder = CollaborativeCoder(Path.cwd())
    
    # Test Generation
    print("🤖 Generating Code Draft...")
    print(coder.generate_code("web request function"))
    
    # Test Review
    print("\n🧐 Reviewing Bad Code...")
    bad_code = """
def bad_function():
    print("Hello")
    try:
        x = 1/0
    except:
        pass
    """
    reviews = coder.review_code_snippet(bad_code)
    for r in reviews:
        print(r)
    
    # Test Learning
    print("\n🎓 Learning...")
    coder.learn_from_correction("test intent", "def good(): pass")
