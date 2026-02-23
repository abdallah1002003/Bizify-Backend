import os
import re

target_dir = "/Users/abdallahabdelrhimantar/Desktop/p7/app/services"

pattern = re.compile(
    r"\s*def _utc_now\(\)(?: -> datetime)?:\s*return datetime\.now\(timezone\.utc\)\s*"
    r"def _to_update_dict\(obj_in: Any\) -> Dict\[str, Any\]:\s*if obj_in is None:\s*return \{\}\s*if hasattr\(obj_in, [\"']model_dump[\"']\):\s*return obj_in\.model_dump\(exclude_unset=True\)\s*return dict\(obj_in\)\s*"
    r"def _apply_updates\(db_obj: Any, update_data: Dict\[str, Any\]\) -> Any:\s*for field, value in update_data\.items\(\):\s*if hasattr\(db_obj, field\):\s*setattr\(db_obj, field, value\)\s*return db_obj\s*",
    re.MULTILINE
)

import_statement = "from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates\n\n"

for root, dirs, files in os.walk(target_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r") as f:
                content = f.read()
            
            if "_utc_now" in content and "_to_update_dict" in content and "_apply_updates" in content:
                # Let's cleanly replace it
                new_content = pattern.sub("\n\n" + import_statement, content)
                
                if new_content != content:
                    with open(path, "w") as f:
                        f.write(new_content)
                    print(f"Cleaned {path}")
                else:
                    print(f"Failed to match exact multiline pattern in {path}")
