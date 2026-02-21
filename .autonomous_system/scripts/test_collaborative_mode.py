"""
Test script to verify autonomous system collaboration
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

from app.core.session_detector import AntigravitySessionDetector
from evolution.pattern_learning import PatternLearningSystem
from ai.web_researcher import WebKnowledgeRetriever

def test_collaborative_system():
    """Test that the system is in collaborative mode and working correctly."""
    
    print("🧪 Testing Autonomous Collaborative System\n")
    print("=" * 60)
    
    # Test 1: Session Detection
    print("\n1️⃣ Testing Session Detection...")
    detector = AntigravitySessionDetector(Path.cwd())
    is_active = detector.is_antigravity_active()
    
    if is_active:
        print("   ✅ Antigravity session is ACTIVE")
    else:
        print("   ❌ Antigravity session is INACTIVE")
        return False
    
    # Test 2: Learning System
    print("\n2️⃣ Testing Pattern Learning...")
    learner = PatternLearningSystem(Path.cwd())
    initial_count = learner.get_knowledge_stats()['success_patterns']
    
    # Try to learn
    learner.learn_pattern(
        context={'test': 'collaborative_mode'},
        outcome='success',
        details={'message': 'Testing collaborative learning system'}
    )
    
    final_count = learner.get_knowledge_stats()['success_patterns']
    
    if final_count > initial_count:
        print(f"   ✅ Learning is WORKING: {initial_count:,} -> {final_count:,}")
    else:
        print(f"   ❌ Learning is NOT working: {initial_count:,} == {final_count:,}")
        return False
    
    # Test 3: Web Researcher
    print("\n3️⃣ Testing Web Research Capability...")
    researcher = WebKnowledgeRetriever()
    
    # Test that it's ready (won't actually research, just check it's enabled)
    if researcher.session_detector.is_antigravity_active():
        print("   ✅ Web research is ENABLED")
    else:
        print("   ❌ Web research is DISABLED")
        return False
    
    # Test 4: Knowledge Base
    print("\n4️⃣ Testing Knowledge Base...")
    stats = learner.get_knowledge_stats()
    print(f"   📊 Success Patterns: {stats['success_patterns']:,}")
    print(f"   📊 Failure Patterns: {stats['failure_patterns']:,}")
    print("   ✅ Knowledge base is accessible")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - System is ready for collaboration!")
    print("\n🤝 The system will:")
    print("   • Learn from our interactions")
    print("   • Help fix errors as they occur")
    print("   • Stay with you until tasks are complete")
    print("   • Use collaborative intelligence")
    
    return True

if __name__ == "__main__":
    success = test_collaborative_system()
    sys.exit(0 if success else 1)
