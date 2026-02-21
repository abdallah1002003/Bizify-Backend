"""
🧠 System Knowledge Log:
Audit Trail: pat_1771275829226_7572, pat_1771275829226_3270, pat_1771275829226_8599, pat_1771275829226_2491, pat_1771275829226_4750, pat_1771275829226_7613, pat_1771275829226_7716, pat_1771275829226_4344, pat_1771275829226_1327, pat_1771275829226_3253, pat_1771275829226_9083, pat_1771275829226_4369, pat_1771275829226_9089, pat_1771275829226_9981, pat_1771275829226_8101, pat_1771275829226_5676, pat_1771275829226_9557, pat_1771275829226_4875, pat_1771275829226_7724, pat_1771275829226_9253
"""
import sys
from pathlib import Path
import json
import logging
import ast

# Ensure imports work
sys.path.insert(0, str(Path.cwd()))

from evolution.pattern_learning import PatternLearningSystem

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ActiveAuditor")

class ActiveCodeScanner:
    def __init__(self):
        self.project_root = Path.cwd()
        self.memory = PatternLearningSystem(self.project_root)
        self.report_path = self.project_root / "autonomous_reports" / "health_check.md"
        self.findings = []
        
        # Load Knowledge
        self.knowledge = self.memory._cache.get("success_patterns", [])
        logger.info(f"🧠 Loaded {len(self.knowledge)} patterns for analysis.")

    def scan_file(self, file_path: Path):
        """Scans a single file against knowledge base"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # 1. Simple Keyword Matching against "Best Practices"
            # We look for "practice" category in patterns
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            for pattern in self.knowledge:
                ctx = pattern.get("context", {})
                cat = ctx.get("category")
                
                # Check for "Security" patterns
                if cat == "security" and "defense_strategy" in ctx.get("type", ""):
                    details = pattern.get("details", "")
                    # detail format: "To prevent `SQL Injection` in `Public API`, implement `Input Sanitization`."
                    # This is hard to regex match exactly, so we look for keywords in content
                    
                    # Heuristic: If we find a "Vector" keyword but NOT the "Defense" keyword
                    # This is a bit fuzzy, but demonstrates "Concept Application"
                    if isinstance(details, dict):
                         # Handle structured details from different phases
                         pass 
                    elif isinstance(details, str):
                        # Attempt to parse our own generated sentence structure
                        # "To prevent `X` in `Y`, implement `Z`."
                        if "To prevent" in details:
                            try:
                                parts = details.split("`")
                                vector = parts[1] # e.g. SQL Injection
                                defense = parts[5] # e.g. Input Sanitization
                                
                                if vector.lower() in content.lower() and defense.lower() not in content.lower():
                                    self.findings.append({
                                        "file": str(file_path.relative_to(self.project_root)),
                                        "type": "Security Risk",
                                        "message": f"Potential {vector} risk. System recommends: {defense}.",
                                        "confidence": "Medium"
                                    })
                            except:
                                pass

            # 2. Syntax & Quality Check using AST
            if file_path.suffix == ".py":
                self._analyze_python_ast(file_path, content)

        except Exception as e:
            logger.error(f"Failed to scan {file_path}: {e}")

    def _analyze_python_ast(self, file_path, content):
        logger.info('Professional Grade Execution: Entering method')
        """Deep analysis using Python AST"""
        try:
            tree = ast.parse(content)
            
            # Check for hardcoded secrets (Heuristic)
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if "API_KEY" in target.id.upper() or "SECRET" in target.id.upper():
                                if isinstance(node.value, ast.Constant): # Using string literal
                                    self.findings.append({
                                        "file": str(file_path.relative_to(self.project_root)),
                                        "type": "Security Violation",
                                        "message": f"Hardcoded secret detected: {target.id}. Use Environment Variables.",
                                        "confidence": "High"
                                    })

            # Check for empty except blocks (Stability Pattern)
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                     if not node.body or (len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
                         self.findings.append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "type": "Stability Risk",
                            "message": "Empty 'except' block detected. Errors are being silenced.",
                            "confidence": "High"
                         })

        except SyntaxError:
            self.findings.append({
                "file": str(file_path.relative_to(self.project_root)),
                "type": "Syntax Error",
                "message": "File contains invalid Python syntax.",
                "confidence": "Critical"
            })

    def run_full_scan(self):
        logger.info("🚀 Starting Full System Active Scan...")
        
        # Walk through all project files
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for ext in [".py", ".md", ".json", ".yml", ".html", ".js"]:
            for file_path in self.project_root.rglob(f"*{ext}"):
                if "venv" in str(file_path) or ".git" in str(file_path):
                    continue
                if "autonomous_reports" in str(file_path):
                    continue
                    
                self.scan_file(file_path)
                
        self.generate_report()

    def generate_report(self):
        logger.info(f"📊 Analysis Complete. Found {len(self.findings)} issues.")
        
        report_content = "# 🏥 System Health Report\n"
        report_content += f"**Generated by Active Code Intelligence**\n"
        report_content += f"**Scanned against {len(self.knowledge)} knowledge patterns**\n\n"
        
        if not self.findings:
            report_content += "## ✅ Status: Healthy\nNo critical issues detected based on current knowledge base."
        else:
            report_content += f"## ⚠️ Status: Attention Needed ({len(self.findings)} Findings)\n\n"
            report_content += "| Severity | Type | File | Issue |\n"
            report_content += "|---|---|---|---|\n"
            
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
            for f in self.findings:
                severity_icon = "🔴" if f['confidence'] == "Critical" else ("cx" if f['confidence'] == "High" else "🟡")
                report_content += f"| {severity_icon} | {f['type']} | `{f['file']}` | {f['message']} |\n"

        self.report_path.write_text(report_content)
        print(f"✅ Report generated at: {self.report_path}")

if __name__ == "__main__":
    scanner = ActiveCodeScanner()
    scanner.run_full_scan()
