"""
🧠 System Knowledge Log:
Audit Trail: pat_1771275847894_7165, pat_1771275847894_6904, pat_1771275847894_7346, pat_1771275847894_4233, pat_1771275847894_6962, pat_1771275847894_9530, pat_1771275847894_4495, pat_1771275847894_3384, pat_1771275847894_4663, pat_1771275847894_6095, pat_1771275847894_2137, pat_1771275847894_1975, pat_1771275847894_9323, pat_1771275847894_6136, pat_1771275847894_4761, pat_1771275847894_6978, pat_1771275847894_5104, pat_1771275847894_5478, pat_1771275847894_2981, pat_1771275847894_3042
"""
from pathlib import Path
import ast
import logging
import sys
import random
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SelfRefactor")

class AutoSurgeon:
    """
    Phase 34: The Knowledge-Aware Surgeon.
    Uses PatternLearningSystem to drive intelligent code mutations.
    """
    def __init__(self, target_file: Path, memory: Optional[object] = None):
        logger.info('Professional Grade Execution: Entering method')
        self.target_file = target_file
        self.memory = memory # Instance of PatternLearningSystem
    
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    # ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers.
    def analyze_and_optimize(self):
        """
        Reads the target file, parses AST, and injects improvements based on patterns.
        """
        logger.info(f"👨‍⚕️ Surgeon: Analyzing {self.target_file} for knowledge-driven upgrades...")
        
        if not self.target_file.exists():
            logger.error("Target file not found.")
            return False

        content = self.target_file.read_text()
        try:
            tree = ast.parse(content)
        except SyntaxError:
            logger.warning(f"⚠️ Syntax Error in {self.target_file}. Attempting Autonomous Repair...")
            # Phase 47: Autonomous Syntax Repairer (Simple)
            import re
            fixed_content = re.sub(r"knowledge_base = (?!['\"])(.+)", r"knowledge_base = '\1'", content)
            if fixed_content != content:
                self.target_file.write_text(fixed_content)
                logger.info("🔧 Autonomous Repair: Fixed missing quotes in knowledge_base.")
                try:
                    tree = ast.parse(fixed_content)
                    content = fixed_content
                    new_lines = content.splitlines()
                except SyntaxError:
                    return False
            else:
                return False
            
        new_lines = content.splitlines()
        changed = False
        pending_mutations = []
        
        # Determine file category for targeted knowledge search
        category = "backend" # Align with MassiveKnowledgeInjector category
        if "FastAPI" in content or "fastapi" in str(self.target_file):
            category = "FastAPI Security"
        elif "PostgreSQL" in content or "db" in str(self.target_file):
            category = "Performance"
        
        # RULE 5: Knowledge-Driven Implementation
        # Try to find a pattern in memory that isn't applied yet
        applied_patterns = []
        if self.memory and hasattr(self.memory, 'search_by_meaning'):
            # Search for relevant patterns
            patterns = self.memory.search_by_meaning(category, top_k=20, min_score=0.0)
            for pat in patterns:
                detail = pat.get("details", "")
                # If the detail looks like a specific requirement (e.g., "Use Pydantic")
                # and it's not in the file, we add a comment/TODO or a semantic marker
                pat_id = pat.get("id", "unknown")
                marker = f"# Knowledge Applied: {pat_id}"
                if marker not in content and detail:
                    # Target the top of the file or a specific class
                    pending_mutations.append({
                        "type": "knowledge_injection",
                        "line": 0,
                        "indent": "",
                        "content": f"{marker}\n# Pattern [{pat_id}]: {detail[:120]}..."
                    })
                    logger.info(f"🧬 Integrity Link: Linking mutation to knowledge {pat_id}")
                    # Removed break to allow multiple mutations per file

        # Standard Rules from Phase 33
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # RULE 1: Caching for Data Retrieval
                if (node.name.startswith("get_") or node.name.startswith("search_")) and node.args.args:
                    has_cache = any(
                        isinstance(d, (ast.Name, ast.Call)) and 
                        (getattr(d, 'id', '') == 'lru_cache' or getattr(getattr(d, 'func', None), 'id', '') == 'lru_cache') 
                        for d in node.decorator_list
                    )
                    if not has_cache:
                        pending_mutations.append({
                            "type": "caching",
                            "line": node.lineno - 1,
                            "indent": " " * node.col_offset,
                            "content": "@lru_cache(maxsize=128)"
                        })

                # RULE 2: Logging Injection
                has_logging = "logger." in ast.get_source_segment(content, node) if hasattr(ast, 'get_source_segment') else "logger." in content
                if not has_logging:
                    insert_line = node.lineno
                    pending_mutations.append({
                        "type": "logging",
                        "line": insert_line,
                        "indent": " " * (node.col_offset + 4),
                        "content": "logger.info('Professional Grade Execution: Entering method')"
                    })

                # RULE 6: Phase 47 - Unsafe Eval Detection
                source = ast.get_source_segment(content, node) if hasattr(ast, 'get_source_segment') else ""
                if "eval(" in source:
                    pending_mutations.append({
                        "type": "security_warning",
                        "line": node.lineno - 1,
                        "indent": " " * node.col_offset,
                        "content": "# ⚠️ SECURITY WARNING: Unsafe 'eval' detected. Replace with literal_eval or safe handlers."
                    })

                # RULE 7: Phase 47 - Nested Loop Detection (Performance)
                for sub_node in ast.walk(node):
                    if isinstance(sub_node, ast.For) and any(isinstance(child, ast.For) for child in ast.walk(sub_node)):
                        pending_mutations.append({
                            "type": "performance_warning",
                            "line": sub_node.lineno - 1,
                            "indent": " " * sub_node.col_offset,
                            "content": "# ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization."
                        })
                        break
            
            # RULE 8: Phase 47 - Hardcoded Secrets Detection
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and any(kw in target.id.upper() for kw in ["PASSWORD", "SECRET", "KEY", "TOKEN"]):
                        pending_mutations.append({
                            "type": "security_critical",
                            "line": node.lineno - 1,
                            "indent": " " * node.col_offset,
                            "content": "# 🛑 SECURITY CRITICAL: Hardcoded secret detected. Move to environment variables."
                        })

        # Apply mutations in reverse order
        pending_mutations.sort(key=lambda x: x["line"], reverse=True)
        for mut in pending_mutations:
            new_lines.insert(mut["line"], f"{mut['indent']}{mut['content']}")
            changed = True
            logger.info(f"🧬 Mutation Applied: {mut['type']} at line {mut['line']+1}")

        if changed:
            final_content = "\n".join(new_lines)
            
            # Ensure imports
            if "@lru_cache" in final_content and "from functools import lru_cache" not in final_content:
                final_content = "from functools import lru_cache\n" + final_content
            if "import logging" not in final_content and "logger." in final_content:
                final_content = "import logging\n" + final_content
                if "logger =" not in final_content:
                    final_content = final_content + "\nlogger = logging.getLogger(__name__)\n"

            self.target_file.write_text(final_content)
            logger.info(f"💾 Upgraded {self.target_file.name} with {len(pending_mutations)} mutations.")
            self.beauty_pass() # Final polish
            return True
        else:
            self.beauty_pass() # Cleanup even if no new mutations
            logger.info("No optimizations applicable.")
            return False

    def beauty_pass(self):
        """Phase 42: Robust Sanitization & Professional Polish."""
        if not self.target_file.exists(): return
        import re
        content = self.target_file.read_text()
        
        # 1. Harvest all Knowledge IDs (from anywhere in the file)
        all_ids = re.findall(r"(?:# Knowledge Applied:|Audit Trail:)\s*([\w\s,]+)", content)
        unique_ids = []
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for match in all_ids:
            # Flatten potential comma-separated lists
            ids = [i.strip() for i in match.split(",") if i.strip().startswith("pat_")]
            for kid in ids:
                if kid not in unique_ids:
                    unique_ids.append(kid)
        
        # 2. Clean EVERYTHING (Regex search and destroy)
        # Remove redundant sequential docstrings/quotes
        content = re.sub(r'("""[\s\S]*?""")\s*("""[\s\S]*?""")+', r'\1', content)
        
        # 3. Clean Mangled Headers
        header_blocks = re.findall(r'"""[\s\S]*?"""', content)
        if len(header_blocks) > 1 and content.startswith('"""'):
             # If there are multiple blocks at the top, merge them
             merged = '"""\n' + '\n'.join([b.strip('"""').strip() for b in header_blocks]) + '\n"""'
             # This is complex to do purely with regex, but we'll stick to basic cleanup
             pass 

        # 4. Final Audit Trail Construction
        # Remove any docstring that mentions Knowledge or Audit
        content = re.sub(r'"""\s*🧠 System Knowledge Log:.*?Audit Trail:.*?"""', "", content, flags=re.DOTALL)
        content = re.sub(r'"""\s*Audit Trail:.*?"""', "", content, flags=re.DOTALL)
        
        # Remove all legacy comment markers
        lines = content.splitlines()
        clean_lines = []
        for line in lines:
            if line.strip().startswith("# Knowledge Applied:"): continue
            if line.strip().startswith("# Pattern:"): continue
            if line.strip().startswith("# Pattern ["): continue
            clean_lines.append(line)
        
        content = "\n".join(clean_lines)
        
        # 3. Create the Perfect Header
        header = []
        if unique_ids:
            header.append('"""')
            header.append("🧠 System Knowledge Log:")
            # Limit audit trail in header to 20 items to keep it professional
            trail = ", ".join(unique_ids[:20])
            if len(unique_ids) > 20: 
                trail += "..."
            header.append(f"Audit Trail: {trail}")
            header.append('"""')
            header.append("") # Spacer
            
        # 4. Final re-assembly
        # Find first non-empty line after stripping whitespace
        content = content.lstrip()
        final_content = "\n".join(header) + content
        
        # 5. Deduplicate blank lines & Ensure Style
        final_lines = []
        last_empty = False
        for line in final_content.splitlines():
            is_empty = not line.strip()
            if is_empty and last_empty:
                continue
            final_lines.append(line)
            last_empty = is_empty
            
        self.target_file.write_text("\n".join(final_lines) + "\n")
        logger.info(f"🧼 Super-Cleaned {self.target_file.name} (IDs: {len(unique_ids)})")

    @staticmethod
    def project_wide_clean(root_path: Path):
        """Phase 44: Recursive cleaning of the entire project."""
        logger.info(f"🧹 Starting Autonomous Project-Wide Clean at {root_path}")
        python_files = list(root_path.rglob("*.py"))
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for f in python_files:
            if any(part in str(f) for part in [".gemini", "venv", "__pycache__", "legacy"]):
                continue
            try:
                surgeon = AutoSurgeon(f)
                surgeon.beauty_pass()
            except Exception as e:
                logger.error(f"❌ Housekeeping failed for {f.name}: {e}")

    @staticmethod
    def organize_cluttered_dirs(root_path: Path):
        """Phase 44: Automatic directory modularization."""
        # Focus on the .autonomous_system/examples or similar areas
        target_dirs = [
            root_path / ".autonomous_system" / "examples",
            root_path / ".autonomous_system" / "genesis",
            root_path / "autonomous_reports" / "knowledge"
        ]
        
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for d in target_dirs:
            if not d.exists(): continue
            files = [f for f in d.iterdir() if f.is_file() and not f.name.startswith(".")]
            if len(files) > 20:
                logger.info(f"🏛️ Architect: Modularizing cluttered directory {d.name}...")
                # Simple logic: group by first word of name
                for f in files:
                    category = f.name.split("_")[0]
                    cat_dir = d / category
                    cat_dir.mkdir(exist_ok=True)
                    f.rename(cat_dir / f.name)

if __name__ == "__main__":
    target = Path.cwd() / ".autonomous_system" / "evolution" / "pattern_learning.py"
    surgeon = AutoSurgeon(target)
    surgeon.analyze_and_optimize()
