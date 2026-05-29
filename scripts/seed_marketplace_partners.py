"""
Seed script — inserts approved marketplace partners and their categories.
Run once:  python scripts/seed_marketplace_partners.py
Idempotent: re-running updates existing rows (matched by email/name) instead of
creating duplicates.
"""
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.partner_category import PartnerCategory
from app.models.partner_profile import ApprovalStatus, PartnerProfile, PartnerType
from app.models.user import User, UserRole

DEFAULT_PASSWORD = "partner123"

# ── Categories ────────────────────────────────────────────────────────────────
CATEGORIES = [
    # Mentors
    {"name": "Business Strategy",    "partner_type": PartnerType.MENTOR},
    {"name": "Fundraising & VC",     "partner_type": PartnerType.MENTOR},
    {"name": "Brand & Marketing",    "partner_type": PartnerType.MENTOR},
    {"name": "Product & Tech",       "partner_type": PartnerType.MENTOR},
    {"name": "Legal & Finance",      "partner_type": PartnerType.MENTOR},
    {"name": "Operations",           "partner_type": PartnerType.MENTOR},
    # Suppliers
    {"name": "Textiles & Fabrics",   "partner_type": PartnerType.SUPPLIER},
    {"name": "Packaging & Print",    "partner_type": PartnerType.SUPPLIER},
    {"name": "Raw Materials",        "partner_type": PartnerType.SUPPLIER},
    {"name": "Electronics & Components", "partner_type": PartnerType.SUPPLIER},
    {"name": "Food & Beverages",     "partner_type": PartnerType.SUPPLIER},
    {"name": "Office Supplies",      "partner_type": PartnerType.SUPPLIER},
    # Manufacturers
    {"name": "Apparel & Garments",   "partner_type": PartnerType.MANUFACTURER},
    {"name": "Metal Fabrication",    "partner_type": PartnerType.MANUFACTURER},
    {"name": "Plastics & Polymers",  "partner_type": PartnerType.MANUFACTURER},
    {"name": "Electronics",          "partner_type": PartnerType.MANUFACTURER},
    {"name": "Food Processing",      "partner_type": PartnerType.MANUFACTURER},
    {"name": "Furniture & Wood",     "partner_type": PartnerType.MANUFACTURER},
]

# ── Partners ──────────────────────────────────────────────────────────────────
PARTNERS = [
    {
        "email": "sara.mentor@bizify.com",
        "full_name": "Sara El-Sayed",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Sara Mentorship",
        "phone_number": "+20 100 555 0101",
        "category_name": "Brand & Marketing",
        "linkedin_url": "https://www.linkedin.com/in/sara-elsayed-mentor",
        "description": (
            "15+ years building consumer brands across MENA. I help early-stage "
            "founders nail positioning, pricing, and their first 100 customers."
        ),
        "services_json": ["Go-to-market", "Brand strategy", "Pricing"],
        "experience_json": [
            {"role": "VP Growth", "company": "Jumia", "years": "2018-2023"},
            {"role": "Founder", "company": "BrandLab MENA", "years": "2023-now"},
        ],
    },
    {
        "email": "omar.mentor@bizify.com",
        "full_name": "Omar Habib",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Habib Advisory",
        "phone_number": "+20 100 555 0102",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/omar-habib-advisor",
        "description": (
            "Ex-YC founder turned mentor. I focus on technical co-founders who "
            "need help turning a prototype into a fundable startup."
        ),
        "services_json": ["Fundraising", "Product strategy", "Hiring"],
        "experience_json": [
            {"role": "Founder/CEO", "company": "Cairo SaaS Co (YC W20)", "years": "2020-2024"},
        ],
    },
    {
        "email": "nile.supplies@bizify.com",
        "full_name": "Nile Supplies",
        "role": UserRole.SUPPLIER,
        "partner_type": PartnerType.SUPPLIER,
        "company_name": "Nile Supplies Co.",
        "phone_number": "+20 101 222 0301",
        "category_name": "Textiles & Fabrics",
        "linkedin_url": None,
        "description": (
            "Wholesale supplier of organic cotton, linen, and recycled "
            "polyester for fashion and home-textile brands. MOQ 200 units."
        ),
        "services_json": ["Organic cotton", "Linen", "Recycled polyester", "Low MOQ"],
        "experience_json": [{"since": "2015", "clients": "120+ brands"}],
    },
    {
        "email": "pyramid.packaging@bizify.com",
        "full_name": "Pyramid Packaging",
        "role": UserRole.SUPPLIER,
        "partner_type": PartnerType.SUPPLIER,
        "company_name": "Pyramid Packaging Ltd.",
        "phone_number": "+20 101 222 0302",
        "category_name": "Packaging & Print",
        "linkedin_url": None,
        "description": (
            "Custom eco-friendly packaging: kraft boxes, compostable mailers, "
            "and printed tissue. Lead time 10-14 days from artwork approval."
        ),
        "services_json": ["Custom boxes", "Compostable mailers", "Printed tissue"],
        "experience_json": [{"since": "2018", "monthly_volume": "300K units"}],
    },
    {
        "email": "deltaworks.mfg@bizify.com",
        "full_name": "DeltaWorks Manufacturing",
        "role": UserRole.MANUFACTURER,
        "partner_type": PartnerType.MANUFACTURER,
        "company_name": "DeltaWorks Manufacturing",
        "phone_number": "+20 102 777 0401",
        "category_name": "Apparel & Garments",
        "linkedin_url": None,
        "description": (
            "Full-service apparel manufacturer in 10th of Ramadan. Cut-and-sew, "
            "knit, and woven garments. CMT and full-package available."
        ),
        "services_json": ["Apparel CMT", "Full-package production", "Sampling"],
        "experience_json": [
            {"capacity": "80K units/month", "certifications": ["BSCI", "OEKO-TEX"]},
        ],
    },
    {
        "email": "redsea.mfg@bizify.com",
        "full_name": "Red Sea Metal Works",
        "role": UserRole.MANUFACTURER,
        "partner_type": PartnerType.MANUFACTURER,
        "company_name": "Red Sea Metal Works",
        "phone_number": "+20 102 777 0402",
        "category_name": "Metal Fabrication",
        "linkedin_url": None,
        "description": (
            "Precision metal fabrication for furniture and small appliance "
            "startups. Laser cutting, powder coating, and short-run assembly."
        ),
        "services_json": ["Laser cutting", "Powder coating", "Short-run assembly"],
        "experience_json": [{"min_order": "50 units", "lead_time": "3-5 weeks"}],
    },
]


def _upsert_category(db, *, name, partner_type) -> PartnerCategory:
    cat = (
        db.query(PartnerCategory)
        .filter(PartnerCategory.name == name, PartnerCategory.partner_type == partner_type)
        .first()
    )
    if cat:
        return cat
    cat = PartnerCategory(name=name, partner_type=partner_type)
    db.add(cat)
    db.flush()
    return cat


def _upsert_user(db, *, email, full_name, role) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.full_name = full_name
        user.role = role
        user.is_active = True
        user.is_verified = True
        return user
    user = User(
        email=email,
        password_hash=get_password_hash(DEFAULT_PASSWORD),
        full_name=full_name,
        role=role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()
    return user


def _upsert_partner_profile(db, *, user_id, data, category_id) -> PartnerProfile:
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == user_id).first()
    now = datetime.now(timezone.utc)

    if profile:
        profile.partner_type = data["partner_type"]
        profile.company_name = data["company_name"]
        profile.phone_number = data["phone_number"]
        profile.description = data["description"]
        profile.services_json = data["services_json"]
        profile.experience_json = data["experience_json"]
        profile.category_id = category_id
        profile.linkedin_url = data.get("linkedin_url")
        profile.approval_status = ApprovalStatus.APPROVED
        profile.approved_at = profile.approved_at or now
        return profile

    profile = PartnerProfile(
        user_id=user_id,
        partner_type=data["partner_type"],
        company_name=data["company_name"],
        phone_number=data["phone_number"],
        description=data["description"],
        services_json=data["services_json"],
        experience_json=data["experience_json"],
        category_id=category_id,
        linkedin_url=data.get("linkedin_url"),
        approval_status=ApprovalStatus.APPROVED,
        approved_at=now,
    )
    db.add(profile)
    return profile


def seed():
    db = SessionLocal()
    try:
        # 1. Upsert all categories
        print("Seeding categories...")
        cat_map: dict[str, PartnerCategory] = {}
        for c in CATEGORIES:
            cat = _upsert_category(db, name=c["name"], partner_type=c["partner_type"])
            cat_map[c["name"]] = cat
            print(f"  {c['partner_type'].value}: {c['name']}")
        db.flush()

        # 2. Upsert partners
        print("\nSeeding partners...")
        created, updated = 0, 0
        for entry in PARTNERS:
            existed = db.query(User).filter(User.email == entry["email"]).first() is not None
            user = _upsert_user(db, email=entry["email"], full_name=entry["full_name"], role=entry["role"])
            cat = cat_map[entry["category_name"]]
            _upsert_partner_profile(db, user_id=user.id, data=entry, category_id=cat.id)
            if existed:
                updated += 1
                print(f"  Updated: {entry['company_name']} ->[{entry['category_name']}]")
            else:
                created += 1
                print(f"  Created: {entry['company_name']} ->[{entry['category_name']}]")

        db.commit()
        print(f"\nDone. {created} partners created, {updated} updated.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
