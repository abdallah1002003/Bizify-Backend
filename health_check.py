
#!/usr/bin/env python3
"""
Project Health Check Script für Bizify
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
END = '\033[0m'

class ProjectHealthCheck:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results = {}
        self.total_score = 0
        self.checks_passed = 0
        self.checks_failed = 0
        
    def print_header(self, text: str):
        print(f"\n{BOLD}{BLUE}{'='*60}{END}")
        print(f"{BOLD}{BLUE}{text:^60}{END}")
        print(f"{BOLD}{BLUE}{'='*60}{END}\n")
        
    def print_section(self, text: str):
        print(f"\n{BOLD}{text}{END}")
        print("-" * 40)
        
    def check_file_exists(self, name: str, path: str) -> bool:
        """Check if a file exists"""
        full_path = self.project_root / path
        exists = full_path.exists()
        status = f"{GREEN}✓{END}" if exists else f"{RED}✗{END}"
        print(f"{status} {name:40} {path}")
        if exists:
            self.checks_passed += 1
        else:
            self.checks_failed += 1
        return exists
        
    def check_directory_exists(self, name: str, path: str) -> bool:
        """Check if a directory exists"""
        full_path = self.project_root / path
        exists = full_path.is_dir()
        status = f"{GREEN}✓{END}" if exists else f"{RED}✗{END}"
        count = len(list(full_path.glob("*.py"))) if exists else 0
        print(f"{status} {name:40} {path} ({count} .py files)")
        if exists:
            self.checks_passed += 1
        else:
            self.checks_failed += 1
        return exists
        
    def check_secret_key(self) -> bool:
        """Check if SECRET_KEY is properly configured in .env."""
        env_file = self.project_root / ".env"
        if not env_file.exists():
            print(f"{RED}✗{END} {'.env file':40} NOT FOUND")
            self.checks_failed += 1
            return False

        content = env_file.read_text()
        app_env_match = re.search(r"^APP_ENV\s*=\s*(.+)$", content, flags=re.MULTILINE)
        app_env = app_env_match.group(1).strip().strip('"').strip("'").lower() if app_env_match else "development"

        match = re.search(r"^SECRET_KEY\s*=\s*(.+)$", content, flags=re.MULTILINE)
        if not match:
            print(f"{RED}✗{END} {'SECRET_KEY in .env':40} NOT SET")
            self.checks_failed += 1
            return False

        secret_key = match.group(1).strip().strip('"').strip("'")
        weak_values = {
            "change-me-in-env",
            "replace-with-a-long-random-secret",
            "changeme",
            "secret",
            "default",
        }
        if not secret_key:
            print(f"{RED}✗{END} {'SECRET_KEY in .env':40} EMPTY")
            self.checks_failed += 1
            return False
        if app_env != "test" and secret_key.lower() in weak_values:
            print(f"{RED}✗{END} {'SECRET_KEY in .env':40} DEFAULT/WEAK VALUE")
            self.checks_failed += 1
            return False
        if app_env != "test" and len(secret_key) < 32:
            print(f"{RED}✗{END} {'SECRET_KEY in .env':40} TOO SHORT (<32)")
            self.checks_failed += 1
            return False

        print(f"{GREEN}✓{END} {'SECRET_KEY configured properly':40}")
        self.checks_passed += 1
        return True
            
    def check_requirements(self) -> Tuple[bool, List[str]]:
        """Check if all required packages are in requirements.txt"""
        req_file = self.project_root / "requirements.txt"
        if not req_file.exists():
            print(f"{RED}✗{END} {'requirements.txt':40} FILE NOT FOUND")
            self.checks_failed += 1
            return False, []
            
        content = req_file.read_text().lower()
        required = {
            'fastapi': 'fastapi',
            'sqlalchemy': 'sqlalchemy',
            'pydantic': 'pydantic',
            'pytest': 'pytest',
            'passlib': 'passlib',
            'python-jose': 'python-jose',
        }
        
        missing = []
        for name, package in required.items():
            if package in content:
                print(f"{GREEN}✓{END} {name:40}")
                self.checks_passed += 1
            else:
                print(f"{RED}✗{END} {name:40} MISSING")
                missing.append(name)
                self.checks_failed += 1
                
        return len(missing) == 0, missing
        
    def check_documentation(self) -> int:
        """Check for documentation files"""
        docs = [
            "docs/ROUTES_DOCUMENTATION.md",
            "docs/ROUTES_QUICK_REFERENCE.md",
            "docs/ROUTES_DEVELOPER_SPEC.md",
            "docs/ROUTES_ARCHITECTURE_SECURITY.md",
            "docs/ROUTES_INDEX.md",
            "docs/FINAL_ASSESSMENT.md",
            "docs/IMPROVEMENT_ROADMAP.md",
            "README.md"
        ]
        
        count = 0
        for doc in docs:
            path = self.project_root / doc
            if path.exists():
                size = path.stat().st_size
                print(f"{GREEN}✓{END} {doc:45} {size:>10} bytes")
                count += 1
                self.checks_passed += 1
            else:
                print(f"{RED}✗{END} {doc:45} NOT FOUND")
                self.checks_failed += 1
                
        return count
        
    def check_tests(self) -> Tuple[int, int]:
        """Count test files"""
        tests_dir = self.project_root / "tests"
        if not tests_dir.exists():
            print(f"{RED}✗{END} {'tests directory':40} NOT FOUND")
            self.checks_failed += 1
            return 0, 0
            
        test_files = list(tests_dir.glob("**/test_*.py"))
        total_lines = sum(f.stat().st_size for f in test_files)
        
        print(f"{GREEN}✓{END} {'Test files found':40} {len(test_files)}")
        print(f"{GREEN}✓{END} {'Total test code':40} {total_lines:,} bytes")
        
        self.checks_passed += 2
        return len(test_files), total_lines
        
    def check_api_routes(self) -> int:
        """Count API route files"""
        routes_dir = self.project_root / "app" / "api" / "routes"
        if not routes_dir.exists():
            print(f"{RED}✗{END} {'routes directory':40} NOT FOUND")
            self.checks_failed += 1
            return 0
            
        route_files = list(routes_dir.glob("**/*.py"))
        route_files = [f for f in route_files if f.name != "__init__.py"]
        
        print(f"{GREEN}✓{END} {'Route files':40} {len(route_files)}")
        self.checks_passed += 1
        return len(route_files)
        
    def check_models(self) -> int:
        """Count model files"""
        models_dir = self.project_root / "app" / "models"
        if not models_dir.exists():
            print(f"{RED}✗{END} {'models directory':40} NOT FOUND")
            self.checks_failed += 1
            return 0
            
        model_files = list(models_dir.glob("**/*.py"))
        model_files = [f for f in model_files if f.name != "__init__.py"]
        
        print(f"{GREEN}✓{END} {'Model files':40} {len(model_files)}")
        self.checks_passed += 1
        return len(model_files)
        
    def check_database_config(self) -> bool:
        """Check database configuration"""
        db_file = self.project_root / "app" / "db" / "database.py"
        if not db_file.exists():
            print(f"{RED}✗{END} {'database.py':40} NOT FOUND")
            self.checks_failed += 1
            return False
            
        content = db_file.read_text()
        
        # Check for connection pooling
        if "QueuePool" in content or "pool" in content.lower():
            print(f"{GREEN}✓{END} {'Connection pooling':40}")
            self.checks_passed += 1
        else:
            print(f"{YELLOW}⚠{END} {'Connection pooling':40} NOT CONFIGURED")
            self.checks_failed += 1
            
        return True

    def check_env_database_url(self) -> str:
        """Check DATABASE_URL is present and valid in .env."""
        env_file = self.project_root / ".env"
        if not env_file.exists():
            print(f"{RED}✗{END} {'.env file':40} NOT FOUND")
            self.checks_failed += 1
            return ""

        content = env_file.read_text()
        match = re.search(r"^DATABASE_URL\s*=\s*(.+)$", content, flags=re.MULTILINE)
        if not match:
            print(f"{RED}✗{END} {'DATABASE_URL in .env':40} NOT SET")
            self.checks_failed += 1
            return ""

        database_url = match.group(1).strip().strip('"').strip("'")
        if not database_url:
            print(f"{RED}✗{END} {'DATABASE_URL in .env':40} EMPTY")
            self.checks_failed += 1
            return ""

        app_env_match = re.search(r"^APP_ENV\s*=\s*(.+)$", content, flags=re.MULTILINE)
        app_env = app_env_match.group(1).strip().strip('"').strip("'").lower() if app_env_match else "development"

        allowed_prefixes = ("postgresql://", "postgresql+")
        if app_env == "test":
            allowed_prefixes = ("postgresql://", "postgresql+", "sqlite://")

        if not database_url.startswith(allowed_prefixes):
            print(f"{RED}✗{END} {'DATABASE_URL format':40} EXPECTED POSTGRESQL")
            self.checks_failed += 1
            return ""

        print(f"{GREEN}✓{END} {'DATABASE_URL in .env':40}")
        self.checks_passed += 1
        return database_url

    def should_verify_db_on_startup(self) -> bool:
        """Read VERIFY_DB_ON_STARTUP from .env (defaults to true)."""
        env_file = self.project_root / ".env"
        if not env_file.exists():
            return True

        content = env_file.read_text()
        match = re.search(r"^VERIFY_DB_ON_STARTUP\s*=\s*(.+)$", content, flags=re.MULTILINE)
        if not match:
            return True

        value = match.group(1).strip().strip('"').strip("'").lower()
        return value not in {"0", "false", "no", "off"}

    def check_database_connection_live(self, database_url: str) -> bool:
        """Check if database is reachable."""
        if not database_url:
            print(f"{RED}✗{END} {'Database connectivity':40} SKIPPED (NO URL)")
            self.checks_failed += 1
            return False

        try:
            from sqlalchemy import create_engine, text
            from sqlalchemy.exc import SQLAlchemyError
        except Exception:
            print(f"{YELLOW}⚠{END} {'Database connectivity':40} SQLALCHEMY NOT AVAILABLE")
            self.checks_failed += 1
            return False

        try:
            engine = create_engine(database_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"{GREEN}✓{END} {'Database connectivity':40}")
            self.checks_passed += 1
            return True
        except SQLAlchemyError as exc:
            print(f"{RED}✗{END} {'Database connectivity':40} {str(exc).splitlines()[0]}")
            self.checks_failed += 1
            return False

    def check_legacy_service_imports(self) -> bool:
        """Check whether legacy service modules are still referenced."""
        patterns = (
            "from app.services.ideation import idea_service",
            "from app.services.business import business_service",
        )
        matches = []
        scan_roots = (
            self.project_root / "app",
            self.project_root / "tests",
        )
        for root in scan_roots:
            if not root.exists():
                continue
            for py_file in root.rglob("*.py"):
                try:
                    content = py_file.read_text()
                except Exception:
                    continue
                if any(pattern in content for pattern in patterns):
                    matches.append(py_file)

        if matches:
            print(f"{YELLOW}⚠{END} {'Legacy service imports':40} {len(matches)} file(s)")
            self.checks_failed += 1
            return False

        print(f"{GREEN}✓{END} {'Legacy service imports':40} NONE FOUND")
        self.checks_passed += 1
        return True
        
    def check_auth_security(self) -> bool:
        """Check authentication security"""
        auth_file = self.project_root / "app" / "api" / "routes" / "auth.py"
        if not auth_file.exists():
            return False
            
        content = auth_file.read_text()
        
        checks = {
            "Password validation": "verify_password" in content,
            "JWT tokens": "create_access_token" in content,
            "Active user check": "is_active" in content,
        }
        
        all_passed = True
        for check_name, result in checks.items():
            if result:
                print(f"{GREEN}✓{END} {check_name:40}")
                self.checks_passed += 1
            else:
                print(f"{RED}✗{END} {check_name:40}")
                self.checks_failed += 1
                all_passed = False
                
        return all_passed
        
    def run_all_checks(self):
        """Run all health checks"""
        self.print_header("Idea Spark API - Project Health Check")
        
        # 1. Project Structure
        self.print_section("1. PROJECT STRUCTURE")
        self.check_directory_exists("Main app", "app")
        self.check_directory_exists("Routes", "app/api/routes")
        self.check_directory_exists("Models", "app/models")
        self.check_directory_exists("Services", "app/services")
        self.check_directory_exists("Schemas", "app/schemas")
        self.check_directory_exists("Tests", "tests")
        
        # 2. Configuration Files
        self.print_section("2. CONFIGURATION")
        self.check_file_exists("main.py", "main.py")
        self.check_file_exists("requirements.txt", "requirements.txt")
        self.check_file_exists("pytest.ini", "pytest.ini")
        self.check_file_exists("alembic.ini", "alembic.ini")
        self.check_file_exists(".env.example", ".env.example")
        self.check_file_exists("README.md", "README.md")
        
        # 3. Core Application
        self.print_section("3. CORE APPLICATION")
        self.check_directory_exists("Security", "app/core")
        self.check_directory_exists("Database", "app/db")
        self.check_directory_exists("Middleware", "app/middleware")
        
        # 4. Security
        self.print_section("4. SECURITY CHECK")
        self.check_secret_key()
        self.check_auth_security()
        
        # 5. Dependencies
        self.print_section("5. DEPENDENCIES")
        req_ok, missing = self.check_requirements()
        if missing:
            print(f"{YELLOW}⚠ Missing packages: {', '.join(missing)}{END}")
        
        # 6. Documentation
        self.print_section("6. DOCUMENTATION")
        doc_count = self.check_documentation()
        print(f"\n{GREEN}Documentation files: {doc_count}/8{END}")
        
        # 7. Code Organization
        self.print_section("7. CODE ORGANIZATION")
        route_count = self.check_api_routes()
        model_count = self.check_models()
        test_count, test_size = self.check_tests()
        
        # 8. Database
        self.print_section("8. DATABASE CONFIGURATION")
        database_url = self.check_env_database_url()
        self.check_database_config()
        if self.should_verify_db_on_startup():
            self.check_database_connection_live(database_url)
        else:
            print(f"{YELLOW}⚠{END} {'Database connectivity':40} SKIPPED (VERIFY_DB_ON_STARTUP=false)")
            self.checks_passed += 1

        # 9. Legacy Refactor
        self.print_section("9. LEGACY SERVICE STATUS")
        self.check_legacy_service_imports()

        # 10. Summary
        self.print_header("HEALTH CHECK SUMMARY")
        
        total_checks = self.checks_passed + self.checks_failed
        percentage = (self.checks_passed / total_checks * 100) if total_checks > 0 else 0
        
        print(f"\nChecks Passed:  {GREEN}{self.checks_passed}{END}")
        print(f"Checks Failed:  {RED}{self.checks_failed}{END}")
        print(f"Total Checks:   {total_checks}")
        print(f"Health Score:   {BOLD}{percentage:.1f}%{END}\n")
        
        # Grade
        if percentage >= 90:
            grade = f"{GREEN}A{END}"
        elif percentage >= 80:
            grade = f"{GREEN}B{END}"
        elif percentage >= 70:
            grade = f"{YELLOW}C{END}"
        elif percentage >= 60:
            grade = f"{YELLOW}D{END}"
        else:
            grade = f"{RED}F{END}"
            
        print(f"Grade: {grade}\n")
        
        # Recommendations
        self.print_section("RECOMMENDATIONS")
        
        recommendations = [
            ("CRITICAL", [
                "Use a strong non-default SECRET_KEY in .env",
                "Keep PostgreSQL reachable when VERIFY_DB_ON_STARTUP=true",
                "Implement comprehensive test coverage tracking",
            ]),
            ("HIGH PRIORITY", [
                "Add more integration tests",
                "Configure caching (Redis)",
                "Set up structured logging",
                "Add security testing",
            ]),
            ("MEDIUM PRIORITY", [
                "Implement async/await patterns fully",
                "Add API rate limiting per user",
                "Set up monitoring and metrics",
                "Document deployment process",
            ]),
        ]
        
        for level, items in recommendations:
            if level == "CRITICAL":
                icon = "🔴"
            elif level == "HIGH PRIORITY":
                icon = "🟠"
            else:
                icon = "🟡"
                
            print(f"\n{icon} {BOLD}{level}{END}:")
            for item in items:
                print(f"   • {item}")
        
        print("\n")
        
        # Statistics
        self.print_section("PROJECT STATISTICS")
        print(f"Routes:         {route_count}")
        print(f"Models:         {model_count}")
        print(f"Test Files:     {test_count}")
        print(f"Test Code Size: {test_size:,} bytes")
        print("\nFor detailed evaluation, see docs/FINAL_ASSESSMENT.md")
        print("For improvement plan, see docs/IMPROVEMENT_ROADMAP.md\n")
        
        return percentage >= 70  # Return success if score >= 70%

def main():
    """Main entry point"""
    check = ProjectHealthCheck()
    success = check.run_all_checks()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
