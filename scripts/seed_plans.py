"""
Seed script — inserts the default Bizify subscription plans into the DB.
Run once:  python scripts/seed_plans.py
"""
import sys
import os

# Make sure the app package is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.plan   import Plan


PLANS = [
    {
        "name":          "Free",
        "price":         0.00,
        "features_json": {
            "ai_runs":      3,
            "ideas":        5,
            "businesses":   1,
            "export":       False,
            "priority_support": False,
        },
        "is_active": True,
    },
    {
        "name":          "Pro",
        "price":         9.99,        
        "features_json": {
            "ai_runs":      50,
            "ideas":        50,
            "businesses":   5,
            "export":       True,
            "priority_support": False,
        },
        "is_active": True,
    },
    {
        "name":          "Enterprise",
        "price":         29.99,       
        "features_json": {
            "ai_runs":      -1,       # -1 = unlimited
            "ideas":        -1,
            "businesses":   -1,
            "export":       True,
            "priority_support": True,
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
