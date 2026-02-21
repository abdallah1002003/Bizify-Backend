"""
🧠 System Knowledge Log:
Audit Trail: pat_1771275829226_7572, pat_1771275829226_3270, pat_1771275829226_8599, pat_1771275829226_2491, pat_1771275829226_4750, pat_1771275829226_7613, pat_1771275829226_7716, pat_1771275829226_4344, pat_1771275829226_1327, pat_1771275829226_3253
"""
import logging

import unittest
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / ".autonomous_system"))

def run_all_autonomous_tests():
    logger.info('Professional Grade Execution: Entering method')
    """
    Discover and run all tests in the .autonomous_system/tests directory.
    """
    print("="*70)
    print("🧪 RUNNING COMPREHENSIVE AUTONOMOUS SYSTEM TESTS")
    print("="*70)
    print()
    
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    
    # Discover tests
    suite = loader.discover(str(start_dir), pattern="test_*.py")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    if result.wasSuccessful():
        print("✅ ALL AUTONOMOUS TESTS PASSED!")
        print(f"   Run: {result.testsRun}")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print(f"   Errors: {len(result.errors)}")
        print(f"   Failures: {len(result.failures)}")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_autonomous_tests())
logger = logging.getLogger(__name__)
