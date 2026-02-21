import os
from pathlib import Path

# scan for all .py files to build a map: filename -> full_package_path
# e.g. "backup_system.py" -> ".autonomous_system.core.backup_system"

ROOT = Path(".autonomous_system")
FILE_MAP = {}

print("Scanning for python files...")
for root, dirs, files in os.walk(ROOT):
    for file in files:
        if file.endswith(".py") and file != "__init__.py":
            # path relative to CWD, e.g. .autonomous_system/core/backup_system.py
            full_path = Path(root) / file
            # module path: .autonomous_system.core.backup_system
            module_path = str(full_path).replace("/", ".").replace(".py", "")
            FILE_MAP[file] = module_path
            # print(f"Found: {file} -> {module_path}")

# Now fix master_orchestrator.py
TARGET_FILE = ROOT / "core" / "master_orchestrator.py"
print(f"\nFixing {TARGET_FILE}...")

content = TARGET_FILE.read_text()
lines = content.splitlines()
new_lines = []

for line in lines:
    stripped = line.strip()
    if stripped.startswith("from ") and " import " in stripped:
        if stripped.startswith("from "):
            # Already absolute, skip
            new_lines.append(line)
            continue
            
        # extract likely module name: "from backup_system import BackupSystem"
        # module_name = "backup_system"
        parts = stripped.split()
        module_name = parts[1]
        
        # Check if we have a file for this module
        file_name = f"{module_name}.py"
        
        if file_name in FILE_MAP:
            proper_package = FILE_MAP[file_name]
            # Replace "from backup_system" with "from app.core.backup_system"
            new_line = line.replace(f"from {module_name}", f"from {proper_package}")
            print(f"Fixed: {line.strip()} -> {new_line.strip()}")
            new_lines.append(new_line)
        else:
            # Maybe it's not a file but a package? Or standard lib.
            new_lines.append(line)
    else:
        new_lines.append(line)

TARGET_FILE.write_text("\n".join(new_lines) + "\n")
print("Done.")
