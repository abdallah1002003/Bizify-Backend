#!/usr/bin/env python3
"""
Smart File Finder CLI
Use this tool to quickly find files and context for Antigravity
"""
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai.antigravity_helper import AntigravityHelper

def main():
    if len(sys.argv) < 2:
        print("Usage: find_files.py <query>")
        print("Example: find_files.py 'web research'")
        sys.exit(1)
        
    query = " ".join(sys.argv[1:])
    
    # Configure logging to hide internal logs
    logging.basicConfig(level=logging.ERROR)
    
    try:
        helper = AntigravityHelper(Path.cwd())
        helper.quick_find(query)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
