#!/usr/bin/env python3
"""
Evolution Runner - The Trigger for Self-Improvement
"""
import sys
import argparse
import logging
from pathlib import Path

# Add .autonomous_system to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Add project root to sys.path as well (for project analysis)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from evolution.recursive_improver import RecursiveImprover

def main():
    parser = argparse.ArgumentParser(description='Antigravity Evolution Loop')
    parser.add_argument('--target', help='Specific file or directory to evolve', default='.autonomous_system')
    parser.add_argument('--iterations', type=int, default=1, help='How many evolutionary generations to run')
    parser.add_argument('--auto-approve', action='store_true', help='Skip confirmation for upgrades')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n🧬 ANTIGRAVITY RECURSIVE EVOLUTION 🧬")
    print("="*50)
    print(f"Target: {args.target}")
    print(f"Generations: {args.iterations}")
    print("="*50 + "\n")
    
    project_root = Path.cwd()
    improver = RecursiveImprover(project_root)
    
    # Resolve target
    target_path = project_root / args.target
    files_to_evolve = []
    
    if target_path.is_file():
        files_to_evolve.append(target_path)
    elif target_path.is_dir():
        # Find python files, prioritizing core logic
        files_to_evolve.extend(list(target_path.rglob("*.py")))
        # Limit for safety in this demo
        files_to_evolve = files_to_evolve[:10] 
        print(f"ℹ️  Selected {len(files_to_evolve)} files for evolution scanning.")
    else:
        print(f"❌ Target not found: {target_path}")
        sys.exit(1)
        
    # Run the loop
    improver.run_evolution_loop(files_to_evolve, args.iterations)
    
    print("\n" + "="*50)
    print("✅ Evolution Cycle Complete")

if __name__ == "__main__":
    main()
