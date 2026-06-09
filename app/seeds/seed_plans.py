"""
app/seeds/seed_plans.py
========================
Upsert the four Bizify subscription plans with correct features_json.

Run once after the credits-system migration:
    python -m app.seeds.seed_plans

Safe to re-run — it updates existing rows and inserts missing ones.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.database import SessionLocal
from app.models.plan import Plan

PLANS = [
    {
        "name": "Free",
        "price": 0.00,
        "features_json": {
            "plan_type":       "free",
            "credits_limit":   15,          # 15 starter; 5/month renewal when balance = 0
            "is_ppf":          False,
            "ai_analysis":     True,
            "marketing":       False,       # plan-gated
            "roadmap":         False,       # plan-gated
            "translation":     False,       # plan-gated
            "pdf_validation":  False,       # plan-gated
            "section_chat":    False,       # plan-gated
            "chat_daily_limit": 20,
            "ideas_limit":     1,
            "teams_limit":     0,
            "export_pdf":      False,
            "export_word":     False,
            "premium_model":   False,
            "ai_tokens":       -1,          # no token cap (credit system is the gate)
        },
    },
    {
        "name": "Pay-Per-Feature",
        "price": 0.00,
        "features_json": {
            "plan_type":       "payg",
            "credits_limit":   0,           # no subscription credits; PPF balance is the gate
            "is_ppf":          True,
            "ai_analysis":     True,
            "marketing":       True,
            "roadmap":         True,
            "translation":     True,
            "pdf_validation":  True,
            "section_chat":    True,        # included with purchase
            "chat_daily_limit": 20,
            "ideas_limit":     3,
            "teams_limit":     0,
            "export_pdf":      False,
            "export_word":     False,
            "premium_model":   False,
            "ai_tokens":       -1,
        },
    },
    {
        "name": "Pro",
        "price": 350.00,
        "features_json": {
            "plan_type":       "pro",
            "credits_limit":   90,
            "is_ppf":          False,
            "ai_analysis":     True,
            "marketing":       True,
            "roadmap":         True,
            "translation":     True,
            "pdf_validation":  True,
            "section_chat":    True,
            "chat_daily_limit": -1,         # unlimited
            "ideas_limit":     5,
            "teams_limit":     3,
            "export_pdf":      True,
            "export_word":     True,
            "premium_model":   False,
            "ai_tokens":       -1,
        },
    },
    {
        "name": "Premium",
        "price": 600.00,
        "features_json": {
            "plan_type":       "premium",
            "credits_limit":   150,
            "is_ppf":          False,
            "ai_analysis":     True,
            "marketing":       True,
            "roadmap":         True,
            "translation":     True,
            "pdf_validation":  True,
            "section_chat":    True,
            "chat_daily_limit": -1,
            "ideas_limit":     -1,          # unlimited
            "teams_limit":     20,
            "export_pdf":      True,
            "export_word":     True,
            "premium_model":   True,        # Llama-4-Maverick (verify DeepInfra rate first!)
            "ai_tokens":       -1,
        },
    },
]


def seed_plans() -> None:
    db = SessionLocal()
    try:
        for data in PLANS:
            plan = db.query(Plan).filter(Plan.name == data["name"]).first()
            if plan:
                plan.price = data["price"]
                plan.features_json = data["features_json"]
                plan.is_active = True
                print(f"  Updated plan: {data['name']}")
            else:
                plan = Plan(
                    name=data["name"],
                    price=data["price"],
                    features_json=data["features_json"],
                    is_active=True,
                )
                db.add(plan)
                print(f"  Created plan: {data['name']}")
        db.commit()
        print("Plans seeded successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding plans...")
    seed_plans()
