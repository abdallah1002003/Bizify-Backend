"""
🧠 System Knowledge Log:
Audit Trail: pat_1771275829226_7572, pat_1771275829226_3270, pat_1771275829226_8599, pat_1771275829226_2491, pat_1771275829226_4750, pat_1771275829226_7613, pat_1771275829226_7716, pat_1771275829226_4344, pat_1771275829226_1327, pat_1771275829226_3253
"""
import logging

import unittest
import sys
import importlib
import pkgutil
from pathlib import Path

# Setup Path
# We need to be able to import '.autonomous_system' as a package
# AND import modules directly if they expect to be run standalone
file_path = Path(__file__).resolve()
.autonomous_system_dir = file_path.parent.parent
project_root = .autonomous_system_dir.parent

# Add paths uniquely
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
# if str(.autonomous_system_dir) not in sys.path:
#     sys.path.insert(0, str(.autonomous_system_dir))

class TestGlobalIntegrity(unittest.TestCase):
    """
    The Ultimate Smoke Test.
    Verifies that EVERY SINGLE file in the .autonomous_system package 
    can be imported without crashing.
    """
    
    def test_all_modules_importable(self):
        logger.info('Professional Grade Execution: Entering method')
        """
        Dynamically find and import all modules in .autonomous_system.
        Fails if ANY file has a SyntaxError or ImportError.
        """
        package_path = .autonomous_system_dir
        self.assertTrue(package_path.exists(), "Autonomous System directory missing")
        
        failed_imports = []
        success_count = 0
        
        print(f"\n🔍 Scanning {package_path} for python modules...")
        print(f"DEBUG: sys.path: {sys.path}")
        print(f"DEBUG: project_root: {project_root}")
        
        # Walk through all python files
        # We need to explicitly check subdirectories too
        for file_path in package_path.rglob("*.py"):
            # Skip tests/scripts/migrations/pycache and __init__
            if any(x in str(file_path) for x in ["tests/", "scripts/", "__init__", "migrations", ".pytest_cache"]):
                continue
                
            # e.g. .../.autonomous_system/core/monitor.py
            
            # 1. Package Import: .autonomous_system.core.monitor
            relative_path = file_path.relative_to(project_root)
            module_name_pkg = str(relative_path).replace("/", ".").replace(".py", "")
            
            imported = False
            error_msg = ""
            
            # Attempt 1: Package Import (Preferred)
            try:
                importlib.import_module(module_name_pkg)
                imported = True
            except Exception as e_pkg:
                 import traceback
                 error_msg = f"Import failed: {e_pkg}\n{traceback.format_exc()}"
            
            if imported:
                success_count += 1
                # print(f"✅ {module_name_pkg}")
            else:
                print(f"❌ FAILED: {module_name_pkg} -> {error_msg}")
                failed_imports.append((module_name_pkg, error_msg))
                
        # Assert Perfection
        if failed_imports:
            print("\n⚠️  DETAILED FAILURE REPORT ⚠️")
            for m, e in failed_imports:
                print(f"{m}: {e}")
            self.fail(f"{len(failed_imports)} modules failed to load. See log for details.")
            
        print(f"\n✨ Successfully verified {success_count} modules. All Systems Operational.")

if __name__ == '__main__':
    unittest.main()
logger = logging.getLogger(__name__)
