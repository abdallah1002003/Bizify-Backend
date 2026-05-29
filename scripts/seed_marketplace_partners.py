"""
Seed script — inserts approved marketplace partners (mentors, suppliers,
manufacturers) so the entrepreneur marketplace page has data to display.

Run once:  python scripts/seed_marketplace_partners.py

Idempotent: re-running updates existing rows (matched by email) instead of
creating duplicates.
"""
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.partner_profile import ApprovalStatus, PartnerProfile, PartnerType
from app.models.user import User, UserRole

DEFAULT_PASSWORD = "partner123"

PARTNERS = [
    {
        "email": "sara.mentor@bizify.com",
        "full_name": "Sara El-Sayed",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Sara Mentorship",
        "phone_number": "+20 100 555 0101",
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
        "description": (
            "Precision metal fabrication for furniture and small appliance "
            "startups. Laser cutting, powder coating, and short-run assembly."
        ),
        "services_json": ["Laser cutting", "Powder coating", "Short-run assembly"],
        "experience_json": [{"min_order": "50 units", "lead_time": "3-5 weeks"}],
    },
]


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
    db.flush()  # populate user.id before we reference it
    return user


def _upsert_partner_profile(db, *, user_id, data) -> PartnerProfile:
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == user_id).first()
    now = datetime.now(timezone.utc)

    if profile:
        profile.partner_type = data["partner_type"]
        profile.company_name = data["company_name"]
        profile.phone_number = data["phone_number"]
        profile.description = data["description"]
        profile.services_json = data["services_json"]
        profile.experience_json = data["experience_json"]
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
        approval_status=ApprovalStatus.APPROVED,
        approved_at=now,
    )
    db.add(profile)
    return profile


def seed():
    db = SessionLocal()
    try:
        created, updated = 0, 0
        for entry in PARTNERS:
            existed = (
                db.query(User).filter(User.email == entry["email"]).first() is not None
            )
            user = _upsert_user(
                db,
                email=entry["email"],
                full_name=entry["full_name"],
                role=entry["role"],
            )
            _upsert_partner_profile(db, user_id=user.id, data=entry)
            if existed:
                updated += 1
                print(f" Updated approved partner: {entry['company_name']} ({entry['partner_type'].value})")
            else:
                created += 1
                print(f" Added approved partner: {entry['company_name']} ({entry['partner_type'].value})")

        db.commit()
        print(f"\n Marketplace partners seeded: {created} created, {updated} updated.")
    except Exception as e:
        db.rollback()
        print(f" Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
