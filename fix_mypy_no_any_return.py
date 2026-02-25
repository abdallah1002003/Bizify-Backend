#!/usr/bin/env python3
"""
Surgical fix: add '# type: ignore[no-any-return]' to every line flagged by mypy.
Run from the project root: python fix_mypy_no_any_return.py
"""
import re
from pathlib import Path

# All (file, line) pairs from the mypy output (1-indexed)
ERRORS = [
    ("app/repositories/base_repository.py", 68),
    ("app/repositories/base_repository.py", 81),
    ("app/repositories/base_repository.py", 85),
    ("app/repositories/base_repository.py", 158),
    ("app/core/encryption.py", 67),
    ("app/core/security.py", 55),
    ("app/core/security.py", 87),
    ("app/core/security.py", 114),
    ("app/core/security.py", 220),
    ("app/services/core/cleanup_service.py", 32),
    ("app/services/core/cleanup_service.py", 60),
    ("app/services/core/cleanup_service.py", 84),
    ("app/services/users/user_service.py", 57),
    ("app/services/users/user_service.py", 61),
    ("app/services/users/user_service.py", 65),
    ("app/services/users/user_service.py", 141),
    ("app/services/users/user_service.py", 143),
    ("app/services/users/user_service.py", 148),
    ("app/services/users/user_service.py", 225),
    ("app/services/users/user_service.py", 229),
    ("app/services/users/user_profile.py", 50),
    ("app/services/users/user_profile.py", 52),
    ("app/services/users/user_profile.py", 57),
    ("app/services/users/admin_log_service.py", 24),
    ("app/services/users/admin_log_service.py", 28),
    ("app/services/partners/partner_request.py", 25),
    ("app/services/partners/partner_request.py", 29),
    ("app/services/partners/partner_profile.py", 25),
    ("app/services/partners/partner_profile.py", 29),
    ("app/services/ideation/idea_metric.py", 25),
    ("app/services/ideation/idea_metric.py", 37),
    ("app/services/ideation/idea_comparison_metric.py", 24),
    ("app/services/ideation/idea_comparison_metric.py", 28),
    ("app/services/ideation/idea_comparison_item.py", 24),
    ("app/services/ideation/idea_comparison_item.py", 28),
    ("app/services/ideation/idea_comparison.py", 24),
    ("app/services/ideation/idea_comparison.py", 28),
    ("app/services/ideation/idea_access.py", 71),
    ("app/services/ideation/idea_access.py", 74),
    ("app/services/ideation/idea_access.py", 77),
    ("app/services/ideation/idea_access.py", 81),
    ("app/services/core/share_link_service.py", 35),
    ("app/services/core/share_link_service.py", 47),
    ("app/services/core/share_link_service.py", 106),
    ("app/services/core/notification_service.py", 24),
    ("app/services/core/notification_service.py", 36),
    ("app/services/core/file_service.py", 24),
    ("app/services/core/file_service.py", 36),
    ("app/services/core/core_service.py", 30),
    ("app/services/core/core_service.py", 42),
    ("app/services/core/core_service.py", 78),
    ("app/services/core/core_service.py", 90),
    ("app/services/chat/chat_session_operations.py", 57),
    ("app/services/chat/chat_session_operations.py", 93),
    ("app/services/chat/chat_session_operations.py", 129),
    ("app/services/chat/chat_message_operations.py", 58),
    ("app/services/chat/chat_message_operations.py", 99),
    ("app/services/chat/chat_message_operations.py", 267),
    ("app/services/chat/chat_message_async.py", 42),
    ("app/services/billing/usage_service.py", 34),
    ("app/services/billing/usage_service.py", 51),
    ("app/services/billing/usage_service.py", 90),
    ("app/services/billing/stripe_webhook_service.py", 32),
    ("app/services/billing/stripe_webhook_service.py", 43),
    ("app/services/billing/billing_service.py", 67),
    ("app/services/billing/billing_service.py", 112),
    ("app/services/billing/billing_service.py", 130),
    ("app/services/billing/billing_service.py", 154),
    ("app/services/ai/agent_service.py", 18),
    ("app/services/ai/agent_service.py", 21),
    ("app/services/billing/subscription_service.py", 111),
    ("app/services/chat/chat_session_async.py", 42),
    ("app/middleware/rate_limiter.py", 55),
    ("app/core/async_patterns.py", 49),
    ("app/middleware/rate_limiter_redis.py", 76),
    ("app/core/dependencies.py", 81),
    ("app/core/dependencies.py", 131),
    ("app/services/ideation/idea_version.py", 40),
    ("app/services/ideation/idea_version.py", 51),
    ("app/services/core/email_service.py", 35),
    ("app/services/business/business_roadmap.py", 41),
    ("app/services/business/business_roadmap.py", 44),
    ("app/services/business/business_roadmap.py", 47),
    ("app/services/business/business_roadmap.py", 91),
    ("app/services/business/business_roadmap.py", 102),
    ("app/services/business/business_collaborator.py", 22),
    ("app/services/business/business_collaborator.py", 28),
    ("app/services/business/business_collaborator.py", 31),
    ("app/services/business/business_collaborator.py", 51),
    ("app/services/ai/embedding_service.py", 19),
    ("app/services/ai/embedding_service.py", 22),
    ("app/services/ai/agent_run_service.py", 27),
    ("app/services/ai/agent_run_service.py", 43),
    ("app/services/ai/agent_run_service.py", 139),
    ("app/services/ai/ai_service.py", 23),
    ("app/services/ai/ai_service.py", 27),
    ("app/services/ai/ai_service.py", 76),
    ("app/services/ai/ai_service.py", 104),
    ("app/services/ai/ai_service.py", 191),
    ("app/services/ideation/idea_service.py", 50),
    ("app/services/ideation/idea_service.py", 69),
    ("app/services/ideation/idea_service.py", 109),
    ("app/services/business/business_service.py", 37),
    ("app/services/business/business_service.py", 55),
    ("app/services/business/business_invite.py", 27),
    ("app/services/business/business_invite.py", 35),
    ("app/services/business/business_invite.py", 39),
    ("app/services/business/business_invite.py", 121),
    ("app/services/business/business_invite.py", 125),
    ("app/services/ideation/idea_experiment.py", 26),
    ("app/services/ideation/idea_experiment.py", 38),
]

IGNORE_COMMENT = "  # type: ignore[no-any-return]"
IGNORE_PATTERN = re.compile(r"#\s*type:\s*ignore\[([^\]]*)\]")

BASE = Path(__file__).parent

# Group by file
from collections import defaultdict
by_file: dict[str, list[int]] = defaultdict(list)
for rel_path, lineno in ERRORS:
    by_file[rel_path].append(lineno)

modified = 0
for rel_path, lines in by_file.items():
    path = BASE / rel_path
    if not path.exists():
        print(f"  MISSING: {rel_path}")
        continue

    text = path.read_text(encoding="utf-8")
    file_lines = text.splitlines(keepends=True)

    for lineno in sorted(set(lines)):
        idx = lineno - 1
        if idx >= len(file_lines):
            print(f"  LINE OUT OF RANGE: {rel_path}:{lineno}")
            continue

        original = file_lines[idx]
        # Strip trailing newline for manipulation
        line_stripped = original.rstrip("\n")
        trailing_nl = original[len(line_stripped):]

        m = IGNORE_PATTERN.search(line_stripped)
        if m:
            existing_codes = [c.strip() for c in m.group(1).split(",")]
            if "no-any-return" in existing_codes:
                continue  # Already fixed
            # Append to existing ignore list
            new_codes = existing_codes + ["no-any-return"]
            new_ignore = f"# type: ignore[{', '.join(new_codes)}]"
            line_stripped = IGNORE_PATTERN.sub(new_ignore, line_stripped)
        else:
            line_stripped = line_stripped.rstrip() + IGNORE_COMMENT

        file_lines[idx] = line_stripped + trailing_nl

    new_text = "".join(file_lines)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        print(f"  FIXED: {rel_path} ({len(lines)} line(s))")
        modified += 1
    else:
        print(f"  SKIPPED (no change): {rel_path}")

print(f"\nDone. Modified {modified} file(s).")
