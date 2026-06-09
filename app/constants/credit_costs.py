"""
app/constants/credit_costs.py
==============================
Single source of truth for credit costs and plan gates for every AI route.

Credit anchor: 1 credit = $0.048 real AI operating cost (~2.40 EGP at 50 EGP/$).
Full reference: bizifyAI/files/AI_FEATURES_CREDIT_COSTS.md

Route matching:
  check_ai_usage extracts the path suffix after /ai/ from the request URL
  (e.g.  /api/v1/ai/market-potential → "market-potential")
  and looks it up here.

Return value of get_route_info():
  credits     – credits to deduct (0 = free)
  plan_gates  – set of plan_types that BLOCK this route entirely
  chat_type   – None | 'general' | 'section'
                'general' → 20 turns/day limit for Free and PAYG
                'section' → subscribers + PAYG-with-purchase only; free for Pro/Premium
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, Set


@dataclass(frozen=True)
class RouteInfo:
    credits: int = 0
    plan_gates: Set[str] = field(default_factory=frozenset)
    chat_type: Optional[str] = None  # None | 'general' | 'section'


# ── PAYG flat prices (EGP) per feature key ───────────────────────────────────
# Tier 1 = 120 EGP  (light sections + utilities)
# Tier 2 = 135 EGP  (medium sections)
# Tier 3 = 150 EGP  (advanced / value-priced one-shots)

PAYG_TIER_1 = Decimal("120.00")
PAYG_TIER_2 = Decimal("135.00")
PAYG_TIER_3 = Decimal("150.00")

PAYG_FEATURE_PRICES: dict[str, Decimal] = {
    # Core pipeline — Tier 1
    "customers":        PAYG_TIER_1,
    "idea-strategy":    PAYG_TIER_1,
    "mvp-planning":     PAYG_TIER_1,
    "go-to-market":     PAYG_TIER_1,
    # Core pipeline — Tier 2
    "problems":         PAYG_TIER_2,
    "competition":      PAYG_TIER_2,
    "functions-list":   PAYG_TIER_2,
    "audit":            PAYG_TIER_2,
    # Core pipeline — Tier 3
    "market-potential": PAYG_TIER_3,
    "business-model":   PAYG_TIER_3,
    "unit-economics":   PAYG_TIER_3,
    "roadmap":          PAYG_TIER_3,
    "translation":      PAYG_TIER_3,
    # Marketing — Tier 1
    "customer-research":  PAYG_TIER_1,
    "copywriting":        PAYG_TIER_1,
    "marketing-pricing":  PAYG_TIER_1,
    "launch-strategy":    PAYG_TIER_1,
    "ad-creative":        PAYG_TIER_1,
    "social-media":       PAYG_TIER_1,
    "marketing-ideas":    PAYG_TIER_1,
    # Utilities — Tier 1
    "suggest-name":     PAYG_TIER_1,
    "validate":         PAYG_TIER_1,
    "profile":          PAYG_TIER_1,
    "skills-gap":       PAYG_TIER_1,
}

FREE_PLAN_GATES = frozenset({"free"})
FREE_AND_PAYG_GATES = frozenset({"free", "payg"})  # not used currently but kept for reference

# ── Per-route lookup table ─────────────────────────────────────────────────────
# Keys are the path suffix after /ai/ with the user-id segment removed.
# Pattern: exact first, then suffix-matched by get_route_info().

_ROUTE_TABLE: dict[str, RouteInfo] = {

    # ── Onboarding (always free, no credits, no gate) ─────────────────────────
    "run":                          RouteInfo(credits=0),
    "status":                       RouteInfo(credits=0),
    "rerun/profile":                RouteInfo(credits=0),
    "rerun/problems":               RouteInfo(credits=0),
    "idea-intake":                  RouteInfo(credits=0),
    "idea-intake/run-problems":     RouteInfo(credits=0),
    "idea-intake/start-chat":       RouteInfo(credits=0),
    "idea-intake/chat":             RouteInfo(credits=0, chat_type="general"),
    "idea-intake/chat/stream":      RouteInfo(credits=0, chat_type="general"),
    "idea-intake/approve":          RouteInfo(credits=0),
    "idea-intake/manual":           RouteInfo(credits=0),

    # ── General Chat (20 turns/day — Free & PAYG; unlimited for subscribers) ──
    "general-chat":                 RouteInfo(credits=0, chat_type="general"),
    "general-chat/stream":          RouteInfo(credits=0, chat_type="general"),
    "chat":                         RouteInfo(credits=0, chat_type="general"),
    "chat/stream":                  RouteInfo(credits=0, chat_type="general"),

    # ── Core pipeline — generation & regeneration ──────────────────────────────
    "problems":                     RouteInfo(credits=4),
    "problems/regenerate":          RouteInfo(credits=4),
    "problems/regenerate-custom":   RouteInfo(credits=4),

    "customers":                    RouteInfo(credits=2),
    "customers/regenerate":         RouteInfo(credits=2),
    "customers/regenerate-custom":  RouteInfo(credits=2),

    "competition":                  RouteInfo(credits=3),
    "competition/regenerate":       RouteInfo(credits=3),
    "competition/regenerate-custom":RouteInfo(credits=3),

    "market-potential":                     RouteInfo(credits=5),
    "market-potential/regenerate":          RouteInfo(credits=5),
    "market-potential/regenerate-custom":   RouteInfo(credits=5),

    "idea-strategy":                    RouteInfo(credits=2),
    "idea-strategy/regenerate":         RouteInfo(credits=2),
    "idea-strategy/regenerate-custom":  RouteInfo(credits=2),

    "business-model":                   RouteInfo(credits=4),
    "business-model/regenerate":        RouteInfo(credits=4),
    "business-model/regenerate-custom": RouteInfo(credits=4),

    "functions-list":                   RouteInfo(credits=3),
    "functions-list/regenerate":        RouteInfo(credits=3),
    "functions-list/regenerate-custom": RouteInfo(credits=3),

    "mvp-planning":                     RouteInfo(credits=2),
    "mvp-planning/regenerate":          RouteInfo(credits=2),
    "mvp-planning/regenerate-custom":   RouteInfo(credits=2),

    "unit-economics":                   RouteInfo(credits=4),
    "unit-economics/regenerate":        RouteInfo(credits=4),
    "unit-economics/regenerate-custom": RouteInfo(credits=4),
    "unit-economics/statements":        RouteInfo(credits=4),

    "go-to-market":                     RouteInfo(credits=2),
    "go-to-market/regenerate":          RouteInfo(credits=2),
    "go-to-market/regenerate-custom":   RouteInfo(credits=2),

    # ── Section chat (subscriber + PAYG-with-purchase; blocked on Free) ────────
    "problems/chat":                    RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "problems/chat/stream":             RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "customers/chat":                   RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "customers/chat/stream":            RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "competition/chat":                 RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "competition/chat/stream":          RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "market-potential/chat":            RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "market-potential/chat/stream":     RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "idea-strategy/chat":               RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "idea-strategy/chat/stream":        RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "business-model/chat":              RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "business-model/chat/stream":       RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "functions-list/chat":              RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "functions-list/chat/stream":       RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "mvp-planning/chat":                RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "mvp-planning/chat/stream":         RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "unit-economics/chat":              RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "unit-economics/chat/stream":       RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "go-to-market/chat":                RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "go-to-market/chat/stream":         RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "audit/chat":                       RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "roadmap/chat":                     RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),

    # ── Advanced features ─────────────────────────────────────────────────────
    "audit":                        RouteInfo(credits=3),
    "audit/regenerate":             RouteInfo(credits=3),
    "audit/regenerate-custom":      RouteInfo(credits=3),

    "roadmap/generate":             RouteInfo(credits=10, plan_gates=FREE_PLAN_GATES),
    "roadmap/task":                 RouteInfo(credits=0),   # custom task add — no AI cost

    # Translation goes through ideas.py not ai_pipeline.py — handled separately
    # PDF Validation
    "validate":                     RouteInfo(credits=1, plan_gates=FREE_PLAN_GATES),

    # Name suggestion
    "suggest-name":                 RouteInfo(credits=2),

    # ── Marketing (plan-gated on Free) ────────────────────────────────────────
    "customer-research":                    RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "customer-research/regenerate":         RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "customer-research/regenerate-custom":  RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "customer-research/chat":               RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "customer-research/chat/stream":        RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),

    "copywriting":                    RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "copywriting/regenerate":         RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "copywriting/regenerate-custom":  RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "copywriting/chat":               RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "copywriting/chat/stream":        RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),

    "marketing-pricing":                    RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "marketing-pricing/regenerate":         RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "marketing-pricing/regenerate-custom":  RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "marketing-pricing/chat":               RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "marketing-pricing/chat/stream":        RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),

    "launch-strategy":                    RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "launch-strategy/regenerate":         RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "launch-strategy/regenerate-custom":  RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "launch-strategy/chat":               RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "launch-strategy/chat/stream":        RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),

    "ad-creative":                    RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "ad-creative/regenerate":         RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "ad-creative/regenerate-custom":  RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "ad-creative/chat":               RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "ad-creative/chat/stream":        RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),

    "social-media":                    RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "social-media/regenerate":         RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "social-media/regenerate-custom":  RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "social-media/chat":               RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "social-media/chat/stream":        RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),

    "marketing-ideas":                    RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "marketing-ideas/regenerate":         RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "marketing-ideas/regenerate-custom":  RouteInfo(credits=2, plan_gates=FREE_PLAN_GATES),
    "marketing-ideas/chat":               RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
    "marketing-ideas/chat/stream":        RouteInfo(credits=0, plan_gates=FREE_PLAN_GATES, chat_type="section"),
}

# ── Default for unknown POST routes (safe fallback) ───────────────────────────
_DEFAULT = RouteInfo(credits=1)
_FREE_ALWAYS = RouteInfo(credits=0)


def _extract_ai_suffix(path: str) -> str:
    """Extract the meaningful path after /ai/ regardless of prefix depth."""
    for marker in ("/ai/", "/pipeline/"):
        if marker in path:
            suffix = path.split(marker, 1)[1].rstrip("/")
            # Strip UUID segments (user_id injected into some paths)
            import re
            suffix = re.sub(
                r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                "",
                suffix,
                flags=re.IGNORECASE,
            )
            return suffix.strip("/")
    return path.strip("/")


def get_route_info(path: str, method: str = "POST") -> RouteInfo:
    """
    Return the RouteInfo for a given request path + method.
    GET requests are always free — call this only for write methods.
    """
    if method.upper() in ("GET", "HEAD", "OPTIONS"):
        return _FREE_ALWAYS

    # PATCH/DELETE (roadmap task edits, etc.) are management ops — no AI cost
    if method.upper() in ("DELETE", "PATCH"):
        return _FREE_ALWAYS

    suffix = _extract_ai_suffix(path)

    # Exact match
    if suffix in _ROUTE_TABLE:
        return _ROUTE_TABLE[suffix]

    # Suffix-prefix match — handles /validate/{section}, /ideas/{id}/suggest-name, etc.
    for key, info in _ROUTE_TABLE.items():
        if suffix.startswith(key + "/") or suffix == key:
            return info

    # Unknown POST to AI service — charge 1 credit as a safe default
    return _DEFAULT


# ── Credit constants for section-trigger from general chat ───────────────────
# Maps the section name returned in the generalBot response → credit cost.
# Used by the backend to charge additional credits when run_section fires.
SECTION_CREDIT_COSTS: dict[str, int] = {
    "problems":         4,
    "customers":        2,
    "competition":      3,
    "market_potential": 5,
    "idea_strategy":    2,
    "business_model":   4,
    "functions_list":   3,
    "mvp_planning":     2,
    "unit_economics":   4,
    "go_to_market":     2,
    "audit":            3,
    "roadmap":          10,
    # Marketing
    "customer_research":  2,
    "copywriting":        2,
    "marketing_pricing":  2,
    "launch_strategy":    2,
    "ad_creative":        2,
    "social_media":       2,
    "marketing_ideas":    2,
}
