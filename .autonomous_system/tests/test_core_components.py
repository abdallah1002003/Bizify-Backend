"""
🧠 System Knowledge Log:
Audit Trail: pat_1771275829226_7572, pat_1771275829226_3270, pat_1771275829226_8599, pat_1771275829226_2491, pat_1771275829226_4750, pat_1771275829226_7613, pat_1771275829226_7716, pat_1771275829226_4344, pat_1771275829226_1327, pat_1771275829226_3253
"""
import logging

import unittest
import asyncio
import sys
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / ".autonomous_system"))

# Use direct imports where package structure is fragile
try:
    from app.core.autonomous_integration_hub import AutonomousIntegrationHub, EventType
    from app.core.master_orchestrator import MasterAutonomousOrchestrator
    from evolution.self_evolution import SelfEvolutionSystem
    from ai.ai_consultant import AIConsultant
except ImportError:
    # Fallback for running inside .autonomous_system folder
    from autonomous_integration_hub import AutonomousIntegrationHub, EventType
    from master_orchestrator import MasterAutonomousOrchestrator
    from evolution.self_evolution import SelfEvolutionSystem
    from ai.ai_consultant import AIConsultant

class TestAutonomousCore(unittest.TestCase):
    
    def setUp(self):
        logger.info('Professional Grade Execution: Entering method')
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.test_dir = self.project_root / ".autonomous_system" / "tests" / "temp_test_env"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
    def tearDown(self):
        logger.info('Professional Grade Execution: Entering method')
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_integration_hub(self):
        logger.info('Professional Grade Execution: Entering method')
        """Test Event Bus Publish/Subscribe"""
        hub = AutonomousIntegrationHub(self.project_root)
        
        # Define a handler
        received_events = []
        async def handler(event):
            received_events.append(event)
            
        # Subscribe
        hub.subscribe(EventType.TASK_STARTED, handler)
        
        # Publish
        asyncio.run(hub.publish(EventType.TASK_STARTED, {"task": "test_task"}))
        
        # Verify
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0]["data"]["task"], "test_task")

    def test_orchestrator_initialization(self):
        logger.info('Professional Grade Execution: Entering method')
        """Test Master Orchestrator Initialization"""
        orchestrator = MasterAutonomousOrchestrator(self.project_root)
        
        # Check if modules are initialized
        self.assertIsNotNone(orchestrator.integration_hub)
        # Verify state tracking
        self.assertGreater(orchestrator.state['modules_active'], 0)
        self.assertGreater(orchestrator.state['utilization_score'], 0)
        
    def test_evolution_system_ast(self):
        logger.info('Professional Grade Execution: Entering method')
        """Test AST-based docstring injection"""
        evolution = SelfEvolutionSystem(self.project_root)
        
        # Create a dummy python file
        dummy_file = self.test_dir / "dummy.py"
        dummy_file.write_text("def hello():\n    print('world')")
        
        # Evolve
        result = evolution.evolve(dummy_file)
        
        # Verify
        self.assertEqual(result["status"], "modified")
        content = dummy_file.read_text()
        self.assertIn('"""', content) # Docstring added
        self.assertIn("TODO: Add docstring", content)

    def test_ai_consultant_scope(self):
        logger.info('Professional Grade Execution: Entering method')
        """Test AI Consultant Restricted Scope"""
        consultant = AIConsultant(self.project_root)
        
        # Test restricted query
        response = consultant.consult("How is the database?")
        self.assertIn("I can only answer questions about the '.autonomous_system'", response)
        
        # Test allowed query
        response = consultant.consult("What is the structure?")
        self.assertIn(".autonomous_system", response)

if __name__ == '__main__':
    unittest.main()
logger = logging.getLogger(__name__)
