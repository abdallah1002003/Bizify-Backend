#!/usr/bin/env python3
"""
Test Auto-Research System
Demonstrates how the system automatically searches for solutions when encountering errors
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

from ai.web_researcher import WebKnowledgeRetriever
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_auto_research():
    """Test the auto-research functionality."""
    
    print("🧪 Testing Auto-Research System")
    print("=" * 70)
    print()
    
    # Initialize researcher
    researcher = WebKnowledgeRetriever()
    
    # Test cases: different types of errors
    test_cases = [
        {
            'name': 'Missing Module',
            'error': "ModuleNotFoundError: No module named 'requests'",
            'context': {'file': 'test.py', 'line': 10}
        },
        {
            'name': 'Attribute Error',
            'error': "AttributeError: 'NoneType' object has no attribute 'get'",
            'context': {'file': 'app.py', 'line': 45}
        },
        {
            'name': 'Simple Syntax Error',
            'error': "SyntaxError: invalid syntax",
            'context': {'file': 'script.py', 'line': 5}
        },
        {
            'name': 'Type Error',
            'error': "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
            'context': {'file': 'calc.py', 'line': 20}
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Test: {test['name']}")
        print(f"   Error: {test['error']}")
        print(f"   Context: {test['context']}")
        print()
        
        # Auto-research the error
        solution = researcher.auto_research_for_error(
            test['error'],
            test['context']
        )
        
        if solution:
            print(f"   ✅ Solution Found!")
            print(f"      Error Type: {solution['error_type']}")
            print(f"      Suggested Action: {solution['suggested_action']}")
            print(f"      Search Query: {solution['search_query']}")
            print(f"      Confidence: {solution['confidence']:.2f}")
            if solution['needs_manual_review']:
                print(f"      ⚠️  Needs manual review (low confidence)")
        else:
            print(f"   ℹ️  No research needed (simple error)")
        
        print()
    
    print("=" * 70)
    print("✅ Auto-Research Testing Complete!")
    print()
    print("📊 Summary:")
    print("   The system can now:")
    print("   • Analyze errors intelligently")
    print("   • Determine when to search for solutions")
    print("   • Generate smart search queries")
    print("   • Suggest actionable solutions")
    print("   • Learn from the research process")

if __name__ == "__main__":
    test_auto_research()
