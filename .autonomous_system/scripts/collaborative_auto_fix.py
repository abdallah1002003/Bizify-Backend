"""
Collaborative Coding Directive
Enables autonomous system to work WITH Antigravity AI in improving code.
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

def collaborative_auto_fix():
    """
    Main directive for collaborative auto-fixing.
    This runs continuously and coordinates with Antigravity AI.
    """
    
    # Import auto-fix engine
    from app.core.auto_fix_engine import AutoFixEngine
    
    engine = AutoFixEngine(project_root)
    
    logger.info("🤝 Starting Collaborative Auto-Fix Mode")
    logger.info("🎯 Autonomous System + Antigravity AI = Better Code!")
    
    # Target directories
    target_dirs = [
        project_root / ".autonomous_system",
        project_root / "routes",
        project_root / "services",
        project_root / "middleware",
    ]
    
    # Process files
    total_fixes = 0
    total_files = 0
    
    for target_dir in target_dirs:
        if not target_dir.exists():
            continue
        
        python_files = list(target_dir.rglob("*.py"))
        
        for py_file in python_files:
            # Skip test files and migrations
            if 'test' in str(py_file) or 'migration' in str(py_file):
                continue
            
            # Skip if file is too large
            if py_file.stat().st_size > 100000:  # 100KB
                continue
            
            try:
                result = engine.process_file(py_file)
                total_files += 1
                total_fixes += result['fixes_applied']
                
                if result['fixes_applied'] > 0:
                    logger.info(f"✅ {py_file.name}: {result['fixes_applied']} fixes applied")
                
            except Exception as e:
                logger.error(f"Error processing {py_file}: {e}")
    
    # Save learned patterns
    patterns_file = project_root / ".autonomous_system" / "knowledge" / "auto_fix_patterns.json"
    patterns_file.parent.mkdir(parents=True, exist_ok=True)
    engine.save_learned_patterns(patterns_file)
    
    # Report
    report = {
        "timestamp": time.time(),
        "files_processed": total_files,
        "total_fixes_applied": total_fixes,
        "patterns_learned": len(engine.patterns_learned),
        "mode": "collaborative_auto_fix"
    }
    
    report_file = project_root / "autonomous_reports" / "auto_fix_report.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, indent=2))
    
    logger.info(f"🎉 Collaborative Auto-Fix Complete!")
    logger.info(f"📊 Files: {total_files}, Fixes: {total_fixes}, Patterns: {len(engine.patterns_learned)}")
    
    return report

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    collaborative_auto_fix()
