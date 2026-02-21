"""
🧠 System Knowledge Log:
Audit Trail: pat_1771275829226_7572, pat_1771275829226_3270, pat_1771275829226_8599, pat_1771275829226_2491, pat_1771275829226_4750, pat_1771275829226_7613, pat_1771275829226_7716, pat_1771275829226_4344, pat_1771275829226_1327, pat_1771275829226_3253, pat_1771275829226_9083, pat_1771275829226_4369, pat_1771275829226_9089, pat_1771275829226_9981, pat_1771275829226_8101, pat_1771275829226_5676, pat_1771275829226_9557, pat_1771275829226_4875, pat_1771275829226_7724, pat_1771275829226_9253
"""
import logging
"""
Flatten Autonomous System Directory

Moves all files from subdirectories to the root of .autonomous_system
to ensure imports work correctly and everything is unified.
"""

import shutil
from pathlib import Path
import os

def flatten_directory():
    logger.info('Professional Grade Execution: Entering method')
    base_dir = Path("AUTONOMOUS_SYSTEM_COMPLETE/.autonomous_system")
    print(f"Flattening {base_dir}...")
    
    # Subdirectories to flatten
    subdirs = [
        "core", "integration", "learning", "monitoring", 
        "observation", "utils", "knowledge_base", "bridge"
    ]
    
    # Also flatten SUPER_AUTONOMOUS into .autonomous_system
    super_dir = Path("AUTONOMOUS_SYSTEM_COMPLETE/SUPER_AUTONOMOUS")
    if super_dir.exists():
        print(f"Moving SUPER_AUTONOMOUS files to {base_dir}...")
        for root, dirs, files in os.walk(super_dir):
            for file in files:
                if file == "__init__.py":
                    continue
                    
                src = Path(root) / file
                dst = base_dir / file
                
                # Handle duplicates
                if dst.exists():
                    print(f"  ⚠️  Duplicate {file}, skipping")
                    continue
                
                shutil.copy2(src, dst)
                print(f"  ✅ Moved {file} from SUPER")

    # Flatten categories inside .autonomous_system
    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
    for subdir_name in subdirs:
        subdir = base_dir / subdir_name
        if not subdir.exists():
            continue
            
        print(f"Flattening {subdir_name}...")
        for root, dirs, files in os.walk(subdir):
            for file in files:
                if file == "__init__.py":
                    continue
                    
                src = Path(root) / file
                dst = base_dir / file
                
                if dst.exists():
                    print(f"  ⚠️  Duplicate {file}, skipping")
                    continue
                    
                shutil.move(str(src), str(dst))
                print(f"  ✅ Moved {file}")
        
        # Remove empty dir
        shutil.rmtree(subdir)
        print(f"  🗑️  Removed {subdir_name}/")

    print("\nFlattening complete!")

if __name__ == "__main__":
    flatten_directory()
logger = logging.getLogger(__name__)
