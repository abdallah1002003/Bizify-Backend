"""
Pattern Learning System - Enhanced
Learns from successful fixes and applies them intelligently.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class LearnedPattern:
    """Represents a learned fix pattern."""
    pattern_id: str
    issue_type: str
    original_code_hash: str
    original_code_snippet: str
    fixed_code: str
    success_count: int
    failure_count: int
    confidence_score: float
    first_seen: str
    last_used: str
    context: Dict[str, Any]

class PatternLearningSystem:
    """
    Advanced pattern learning system that:
    1. Learns from successful fixes
    2. Builds confidence scores
    3. Suggests fixes based on similar patterns
    4. Tracks success/failure rates
    """
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.patterns: Dict[str, LearnedPattern] = {}
        self.load_patterns()
    
    def load_patterns(self) -> None:
        """Load learned patterns from disk."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                for p in data.get('patterns', []):
                    pattern = LearnedPattern(**p)
                    self.patterns[pattern.pattern_id] = pattern
                print(f"📚 Loaded {len(self.patterns)} learned patterns")
            except Exception as e:
                print(f"⚠️ Failed to load patterns: {e}")
    
    def save_patterns(self) -> None:
        """Save learned patterns to disk."""
        data = {
            'patterns': [asdict(p) for p in self.patterns.values()],
            'total_patterns': len(self.patterns),
            'last_updated': datetime.now().isoformat()
        }
        
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(data, indent=2))
        print(f"💾 Saved {len(self.patterns)} patterns")
    
    def learn_from_fix(self, issue_type: str, original_code: str, 
                       fixed_code: str, success: bool, context: Dict[str, Any] = None) -> None:
        """Learn from a fix attempt."""
        # Create hash of original code for matching
        code_hash = hashlib.md5(original_code.encode()).hexdigest()[:16]
        pattern_id = f"{issue_type}_{code_hash}"
        
        if pattern_id in self.patterns:
            # Update existing pattern
            pattern = self.patterns[pattern_id]
            if success:
                pattern.success_count += 1
            else:
                pattern.failure_count += 1
            
            pattern.last_used = datetime.now().isoformat()
            pattern.confidence_score = self._calculate_confidence(pattern)
        else:
            # Create new pattern
            pattern = LearnedPattern(
                pattern_id=pattern_id,
                issue_type=issue_type,
                original_code_hash=code_hash,
                original_code_snippet=original_code[:200],  # Store snippet
                fixed_code=fixed_code,
                success_count=1 if success else 0,
                failure_count=0 if success else 1,
                confidence_score=1.0 if success else 0.0,
                first_seen=datetime.now().isoformat(),
                last_used=datetime.now().isoformat(),
                context=context or {}
            )
            self.patterns[pattern_id] = pattern
        
        print(f"🎓 Learned pattern: {issue_type} (confidence: {pattern.confidence_score:.2f})")
    
    def _calculate_confidence(self, pattern: LearnedPattern) -> float:
        """Calculate confidence score for a pattern."""
        total = pattern.success_count + pattern.failure_count
        if total == 0:
            return 0.0
        
        # Base confidence on success rate
        success_rate = pattern.success_count / total
        
        # Boost confidence with more uses
        experience_factor = min(1.0, total / 10.0)
        
        return success_rate * (0.7 + 0.3 * experience_factor)
    
    def find_similar_pattern(self, issue_type: str, code: str, 
                            min_confidence: float = 0.7) -> Optional[LearnedPattern]:
        """Find a similar pattern with high confidence."""
        code_hash = hashlib.md5(code.encode()).hexdigest()[:16]
        pattern_id = f"{issue_type}_{code_hash}"
        
        # Exact match
        if pattern_id in self.patterns:
            pattern = self.patterns[pattern_id]
            if pattern.confidence_score >= min_confidence:
                return pattern
        
        # Fuzzy match by issue type
        candidates = [
            p for p in self.patterns.values()
            if p.issue_type == issue_type and p.confidence_score >= min_confidence
        ]
        
        if candidates:
            # Return highest confidence
            return max(candidates, key=lambda p: p.confidence_score)
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get learning statistics."""
        if not self.patterns:
            return {'total_patterns': 0}
        
        by_type = {}
        total_success = 0
        total_failure = 0
        
        for pattern in self.patterns.values():
            if pattern.issue_type not in by_type:
                by_type[pattern.issue_type] = {
                    'count': 0,
                    'avg_confidence': 0.0,
                    'success': 0,
                    'failure': 0
                }
            
            by_type[pattern.issue_type]['count'] += 1
            by_type[pattern.issue_type]['success'] += pattern.success_count
            by_type[pattern.issue_type]['failure'] += pattern.failure_count
            total_success += pattern.success_count
            total_failure += pattern.failure_count
        
        # Calculate averages
        for stats in by_type.values():
            if stats['count'] > 0:
                stats['avg_confidence'] = sum(
                    p.confidence_score for p in self.patterns.values()
                    if p.issue_type in by_type
                ) / stats['count']
        
        return {
            'total_patterns': len(self.patterns),
            'total_success': total_success,
            'total_failure': total_failure,
            'success_rate': total_success / (total_success + total_failure) if (total_success + total_failure) > 0 else 0,
            'by_type': by_type
        }

def test_pattern_learning():
    """Test pattern learning system."""
    storage = Path(".autonomous_system/knowledge/learned_patterns.json")
    learner = PatternLearningSystem(storage)
    
    # Learn some patterns
    learner.learn_from_fix(
        'nested_loop',
        'for x in items:\n    for y in x:\n        result.append(y)',
        'result = [y for x in items for y in x]',
        success=True,
        context={'file': 'test.py', 'line': 10}
    )
    
    learner.learn_from_fix(
        'hardcoded_secret',
        "api_key = 'sk-12345'",
        "api_key = os.getenv('API_KEY')",
        success=True
    )
    
    # Save patterns
    learner.save_patterns()
    
    # Get statistics
    stats = learner.get_statistics()
    print("\n📊 Learning Statistics:")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    test_pattern_learning()
