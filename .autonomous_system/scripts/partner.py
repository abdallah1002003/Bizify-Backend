#!/usr/bin/env python3
"""
Partner CLI - Interface for Antigravity <-> System Collaboration
"""
import sys
import argparse
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai.collaborative_coder import CollaborativeCoder

def main():
    parser = argparse.ArgumentParser(description='Antigravity Partner Interface')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Draft Command
    draft_parser = subparsers.add_parser('draft', help='Ask system to draft code')
    draft_parser.add_argument('intent', help='Description of what to code')
    
    # Review Command
    review_parser = subparsers.add_parser('review', help='Ask system to review a file')
    review_parser.add_argument('file', help='Path to file to review')
    
    # Teach Command
    teach_parser = subparsers.add_parser('teach', help='Teach system from a finished file')
    teach_parser.add_argument('intent', help='What does this code do?')
    teach_parser.add_argument('file', help='Path to the finished file')
    
    args = parser.parse_args()
    
    # Setup
    logging.basicConfig(level=logging.ERROR)
    coder = CollaborativeCoder(Path.cwd())
    
    if args.command == 'draft':
        print(f"🤖 Partner is writing full implementation for: '{args.intent}'...\n")
        print("="*50)
        draft = coder.generate_code(args.intent)
        print(draft)
        print("="*50)
        print("\n✅ Implementation complete. The code is ready for deployment.")
        
    elif args.command == 'review':
        print(f"🧐 Partner is reviewing: {args.file}...\n")
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
            
        content = file_path.read_text()
        feedback = coder.review_code_snippet(content)
        
        if feedback:
            print("🚨 Issues Found:")
            for item in feedback:
                print(item)
        else:
            print("✅ Code looks good! No issues found.")
            
    elif args.command == 'teach':
        print(f"🎓 Partner is learning from: {args.file}...\n")
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
            
        content = file_path.read_text()
        coder.learn_from_correction(args.intent, content)
        print("✅ Learned! I will use this pattern in the future.")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
