#!/usr/bin/env python3
"""
Quick Pattern Analysis - Run SUPER_AUTONOMOUS Pattern Detector
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from SUPER_AUTONOMOUS.core.pattern_analyzer import PatternAnalyzer

async def quick_analysis():
    """Run quick pattern analysis on codebase"""
    print("=" * 70)
    print("🔍 SUPER_AUTONOMOUS - Deep Pattern Analysis")
    print("=" * 70)
    print()
    
    project_root = Path("/Users/abdallahabdelrhimantar/Desktop/p7")
    analyzer = PatternAnalyzer(project_root)
    
    # Analyze codebase
    patterns = await analyzer.analyze_codebase()
    
    # Get stats
    stats = analyzer.get_pattern_stats()
    
    print("\n" + "=" * 70)
    print("📊 ANALYSIS RESULTS")
    print("=" * 70)
    
    if stats:
        print(f"Total Patterns Found: {stats['total_patterns']}")
        print(f"\nBy Severity:")
        for severity, count in stats['by_severity'].items():
            print(f"  {severity}: {count}")
        
        print(f"\nBy Type:")
        for ptype, count in stats['by_type'].items():
            print(f"  {ptype}: {count}")
    else:
        print("✅ No anti-patterns detected! Code is clean.")
    
    print("=" * 70)
    
    return patterns, stats

if __name__ == "__main__":
    patterns, stats = asyncio.run(quick_analysis())
