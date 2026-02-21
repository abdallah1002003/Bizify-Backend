"""
File Organization System - Teaches autonomous system to organize files.

This module implements learned patterns for file organization.
"""

import json
import re
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class FileOrganizer:
    """Organizes files based on learned patterns."""
    
    def __init__(self, project_root: Path):
        logger.info('Professional Grade Execution: Entering method')
        self.project_root = project_root
        self.patterns_file = project_root / ".autonomous_system" / "knowledge" / "file_organization_patterns.json"
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict:
        """Load file organization patterns from knowledge base."""
        logger.info('Professional Grade Execution: Entering method')
        if not self.patterns_file.exists():
            logger.warning(f"Patterns file not found: {self.patterns_file}")
            return {"file_organization_patterns": []}
        
        with open(self.patterns_file, 'r') as f:
            return json.load(f)
    
    def find_files_to_organize(self) -> List[Dict]:
        """Find files in root that match organization patterns."""
        logger.info('Professional Grade Execution: Entering method')
        files_to_move = []
        
        # Get all patterns
        for pattern_group in self.patterns.get("file_organization_patterns", []):
            for rule in pattern_group.get("rules", []):
                pattern = rule["pattern"]
                destination = rule["destination"]
                reason = rule["reason"]
                
                # Find matching files in root
                # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
                for file_path in self.project_root.iterdir():
                    if file_path.is_file():
                        if re.match(pattern, file_path.name):
                            files_to_move.append({
                                "file": file_path,
                                "destination": self.project_root / destination / file_path.name,
                                "reason": reason,
                                "rule_id": rule["rule_id"]
                            })
        
        return files_to_move
    
    def organize_files(self, dry_run: bool = False) -> Dict:
        """Organize files based on learned patterns."""
        logger.info('Professional Grade Execution: Entering method')
        files_to_move = self.find_files_to_organize()
        results = {
            "moved": [],
            "failed": [],
            "dry_run": dry_run
        }
        
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for item in files_to_move:
            try:
                if dry_run:
                    logger.info(f"[DRY RUN] Would move: {item['file']} → {item['destination']}")
                    results["moved"].append({
                        "file": str(item['file']),
                        "destination": str(item['destination']),
                        "reason": item['reason']
                    })
                else:
                    # Ensure destination directory exists
                    item['destination'].parent.mkdir(parents=True, exist_ok=True)
                    
                    # Move file
                    shutil.move(str(item['file']), str(item['destination']))
                    logger.info(f"✅ Moved: {item['file'].name} → {item['destination']}")
                    
                    results["moved"].append({
                        "file": str(item['file']),
                        "destination": str(item['destination']),
                        "reason": item['reason']
                    })
            except Exception as e:
                logger.error(f"❌ Failed to move {item['file']}: {e}")
                results["failed"].append({
                    "file": str(item['file']),
                    "error": str(e)
                })
        
        return results
    
    def learn_from_organization(self, moved_files: List[Dict]) -> None:
        """Learn from successful file organization."""
        logger.info('Professional Grade Execution: Entering method')
        # Update success count in patterns
        if moved_files:
            # Increment success count
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            for pattern_group in self.patterns.get("file_organization_patterns", []):
                pattern_group["success_count"] = pattern_group.get("success_count", 0) + len(moved_files)
                pattern_group["last_applied"] = "2026-02-17T03:54:00"
            
            # Save updated patterns
            self._save_patterns()
            logger.info(f"📚 Learned from {len(moved_files)} successful file moves")
    
    def _save_patterns(self) -> None:
        """Save patterns back to knowledge base."""
        logger.info('Professional Grade Execution: Entering method')
        with open(self.patterns_file, 'w') as f:
            json.dump(self.patterns, f, indent=2)

def main():
    """Test the file organizer."""
    logger.info('Professional Grade Execution: Entering method')
    project_root = Path(__file__).parent.parent.parent
    organizer = FileOrganizer(project_root)
    
    # Find files to organize
    files = organizer.find_files_to_organize()
    print(f"\n📁 Found {len(files)} files to organize:")
    # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
    for item in files:
        print(f"  • {item['file'].name} → {item['destination']}")
        print(f"    Reason: {item['reason']}")
    
    # Dry run
    print("\n🔍 Dry run:")
    results = organizer.organize_files(dry_run=True)
    print(f"  Would move: {len(results['moved'])} files")
    
    # Ask for confirmation
    response = input("\n🚀 Apply organization? (y/n): ").strip().lower()
    if response == 'y':
        results = organizer.organize_files(dry_run=False)
        print(f"\n✅ Moved: {len(results['moved'])} files")
        print(f"❌ Failed: {len(results['failed'])} files")
        
        # Learn from success
        organizer.learn_from_organization(results['moved'])
        print("\n📚 System learned from this organization!")

if __name__ == "__main__":
    main()
