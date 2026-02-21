"""
🧠 System Knowledge Log:
Audit Trail: pat_1771275829226_7572, pat_1771275829226_3270, pat_1771275829226_8599, pat_1771275829226_2491, pat_1771275829226_4750, pat_1771275829226_7613, pat_1771275829226_7716, pat_1771275829226_4344, pat_1771275829226_1327, pat_1771275829226_3253, pat_1771275829226_9083, pat_1771275829226_4369, pat_1771275829226_9089, pat_1771275829226_9981, pat_1771275829226_8101, pat_1771275829226_5676, pat_1771275829226_9557, pat_1771275829226_4875, pat_1771275829226_7724, pat_1771275829226_9253
"""
# Expose Core Components
from app.core.master_orchestrator import MasterAutonomousOrchestrator
from app.core.autonomous_monitor import AutonomousMonitor
from app.core.autonomous_integration_hub import AutonomousIntegrationHub
from app.core.safe_executor import SafeExecutor
from app.core.backup_system import BackupSystem

# Expose AI Components
from ai.ai_agent import TrueAIAgent
from ai.ai_consultant import AIConsultant
from ai.ai_observer import AIObserver
from ai.main_ai_communicator import MainAICommunicator
from ai.gemini_client import GeminiClient
from ai.claude_client import ClaudeAPIClient

# Expose Evolution Components
from evolution.evolution_orchestrator import EvolutionOrchestrator
from evolution.autonomous_self_improver import AutonomousSelfImprover
from evolution.pattern_learning import PatternLearningSystem

# Expose Tools
from tools.atomic_code_fixer import AtomicCodeFixer
from tools.code_analyzer import CodeAnalyzer
from tools.code_generator import CodeGenerator

# Expose Validation
from validation.qa_validator import AdvancedQAValidator as QAValidator

__all__ = [
    'ClaudeAPIClient',
    'MasterAutonomousOrchestrator',
    'AutonomousMonitor',
    'AutonomousIntegrationHub',
    'SafeExecutor',
    'BackupSystem',
    'TrueAIAgent',
    'AIConsultant',
    'AIObserver',
    'MainAICommunicator',
    'EvolutionOrchestrator',
    'AutonomousSelfImprover',
    'PatternLearningSystem',
    'AtomicCodeFixer',
    'CodeAnalyzer',
    'CodeGenerator',
    'QAValidator'
]
