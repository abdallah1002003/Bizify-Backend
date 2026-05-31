"""
Seed script — inserts the default Bizify subscription plans into the DB.
Run once:  python scripts/seed_plans.py
"""
import os
import sys

# Make sure the app package is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.plan import Plan

PLANS = [
    {
        "name":          "Free",
        "price":         0.00,
        "features_json": {
            "ai_tokens":        15_000,   # ~1 full analysis
            "ai_analysis":      True,
            "export":           True,
            "priority_support": True,
            "ideas":            -1,
            "businesses":       -1,
        },
        "is_active": True,
    },
    {
        "name":          "Pay-Per-Feature",
        "price":         135.00,          # EGP per section credit
        "features_json": {
            "ai_tokens":        0,        # tokens come from PPF credits, not a budget
            "ai_analysis":      True,
            "export":           True,
            "priority_support": True,
            "ideas":            -1,
            "businesses":       -1,
            "is_ppf":           True,     # flag so the gate uses PPF credit balance
        },
        "is_active": True,
    },
    {
        "name":          "Pro",
        "price":         350.00,          # EGP / month
        "features_json": {
            "ai_tokens":        150_000,  # ~10 full analyses / mo
            "ai_analysis":      True,
            "export":           True,
            "priority_support": True,
            "ideas":            -1,
            "businesses":       -1,
        },
        "is_active": True,
    },
    {
        "name":          "Premium",
        "price":         600.00,          # EGP / month
        "features_json": {
            "ai_tokens":        -1,       # unlimited
            "ai_analysis":      True,
            "export":           True,
            "priority_support": True,
            "ideas":            -1,
            "businesses":       -1,
        },
        "is_active": True,
    },
]


def seed():
    db = SessionLocal()
    try:
        for plan_data in PLANS:
            # Check if a plan with this name already exists
            existing = db.query(Plan).filter(Plan.name == plan_data["name"]).first()
            if existing:
                # Update existing plan
                existing.price = plan_data["price"]
                existing.features_json = plan_data["features_json"]
                existing.is_active = plan_data["is_active"]
                print(f" Updated plan: {plan_data['name']} to ${plan_data['price']}")
            else:
                # Create new plan
                plan = Plan(**plan_data)
                db.add(plan)
                print(f" Added new plan: {plan_data['name']} — ${plan_data['price']}")

        db.commit()
        print("\n Database updated successfully!")
    except Exception as e:
        db.rollback()
        print(f" Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
