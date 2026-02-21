"""
🧠 System Knowledge Log:
Audit Trail: pat_1771275829226_7572, pat_1771275829226_3270, pat_1771275829226_8599, pat_1771275829226_2491, pat_1771275829226_4750, pat_1771275829226_7613, pat_1771275829226_7716, pat_1771275829226_4344, pat_1771275829226_1327, pat_1771275829226_3253
"""
import logging
#!/usr/bin/env python3
"""
🤖 AUTONOMOUS SYSTEM with GEMINI INTEGRATION
Full autonomous operation with direct Gemini communication + auto-commit!
"""

import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai.gemini_client import GeminiClient
from auto_commit import AutoCommit
from realtime_learning_logger import RealtimeLearningLogger
from SUPER_AUTONOMOUS.core.pattern_analyzer import PatternAnalyzer

class AutonomousSystemWithGemini:
    """
    Fully autonomous system that communicates directly with Gemini!
    
    Features:
    ✅ Direct Gemini communication (no API keys!)
    ✅ Auto-commit (intelligent)
    ✅ Real-time learning
    ✅ Pattern analysis
    """
    
    def __init__(self, project_root: Path):
        logger.info('Professional Grade Execution: Entering method')
        self.project_root = Path(project_root)
        
        print("=" * 70)
        print("🚀 INITIALIZING AUTONOMOUS SYSTEM WITH GEMINI")
        print("=" * 70)
        print()
        
        # Initialize components
        self.gemini = GeminiClient(project_root)
        self.auto_commit = AutoCommit(project_root)
        self.logger = RealtimeLearningLogger(project_root)
        self.analyzer = PatternAnalyzer(project_root)
        
        print("✅ All systems initialized!")
        print()
    
    async def run_autonomous_cycle(self):
        """
        Run one complete autonomous cycle:
        1. Analyze codebase
        2. Ask Gemini for improvements
        3. Learn from patterns
        4. Auto-commit if safe
        """
        print("=" * 70)
        print("🔄 STARTING AUTONOMOUS CYCLE")
        print("=" * 70)
        print()
        
        # Step 1: Analyze codebase
        print("📊 Step 1: Analyzing codebase...")
        patterns = await self.analyzer.analyze_codebase()
        stats = self.analyzer.get_pattern_stats()
        
        if stats:
            print(f"   Found {stats['total_patterns']} patterns")
            print(f"   High severity: {stats['by_severity'].get('high', 0)}")
            print(f"   Medium severity: {stats['by_severity'].get('medium', 0)}")
        else:
            print("   ✅ No issues found - code is clean!")
        
        print()
        
        # Step 2: Ask Gemini for guidance
        if patterns:
            print("💬 Step 2: Asking Gemini for improvement suggestions...")
            
            # Create request for Gemini
            patterns_summary = f"Found {len(patterns)} patterns:\n"
            for p in patterns[:5]:  # First 5
                patterns_summary += f"- {p['type']}: {p['description'][:50]}...\n"
            
            request = self.gemini.create_improvement_request(
                improvement_type="code_quality",
                description=patterns_summary,
                affected_files=[p['location'] for p in patterns[:10]]
            )
            
            print(f"   ✅ Request sent to Gemini: {Path(request).name}")
            print()
        
        # Step 3: Learn from patterns
        print("🧠 Step 3: Learning from patterns...")
        for pattern in patterns[:5]:  # Learn from first 5
            self.logger.log_pattern(
                category=pattern['type'],
                pattern_name=f"{pattern['type']}_detected",
                details={
                    'description': pattern['description'],
                    'location': pattern['location'],
                    'severity': pattern['severity']
                }
            )
        
        print(f"   ✅ Logged {min(len(patterns), 5)} patterns")
        print()
        
        # Step 4: Auto-commit if safe
        print("💾 Step 4: Checking for safe auto-commit...")
        committed = self.auto_commit.auto_commit_if_safe()
        
        if committed:
            print("   ✅ Changes committed automatically")
        else:
            print("   ⚠️  Manual review required for some changes")
        
        print()
        
        # Finalize learning
        self.logger.finalize_session()
        
        print("=" * 70)
        print("✅ AUTONOMOUS CYCLE COMPLETE")
        print("=" * 70)
    
    async def interactive_mode(self):
        """
        Interactive mode - ask Gemini questions directly
        """
        print("=" * 70)
        print("💬 INTERACTIVE MODE - Talk to Gemini!")
        print("=" * 70)
        print()
        print("Commands:")
        print("  'ask <question>' - Ask Gemini a question")
        print("  'review <files>' - Request code review")
        print("  'fix <error>' - Request bug fix help")
        print("  'commit' - Auto-commit changes")
        print("  'analyze' - Analyze codebase")
        print("  'exit' - Exit")
        print()
        
        while True:
            try:
                command = input("🤖 > ").strip()
                
                if command == 'exit':
                    break
                
                elif command.startswith('ask '):
                    question = command[4:]
                    request = self.gemini.ask_gemini(question)
                    print(f"✅ Request sent: {Path(request).name}")
                
                elif command.startswith('review '):
                    files = command[7:].split()
                    request = self.gemini.create_code_review_request(files)
                    print(f"✅ Review request sent: {Path(request).name}")
                
                elif command == 'commit':
                    self.auto_commit.auto_commit_if_safe()
                
                elif command == 'analyze':
                    await self.run_autonomous_cycle()
                
                else:
                    print("❌ Unknown command")
                
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break

async def main():
    """Main entry point"""
    print("\n" * 2)
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  🤖 AUTONOMOUS SYSTEM WITH GEMINI INTEGRATION  ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    project_root = Path.cwd()
    system = AutonomousSystemWithGemini(project_root)
    
    # Run one cycle
    await system.run_autonomous_cycle()
    
    print("\n💡 Tip: Run in interactive mode with --interactive flag")
    print()

if __name__ == "__main__":
    asyncio.run(main())
