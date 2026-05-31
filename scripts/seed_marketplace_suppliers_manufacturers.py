"""
Seed real Egyptian suppliers & manufacturers into the marketplace.

- Loads scripts/data/egypt_partners.json (real directory data).
- Upserts SUPPLIER/MANUFACTURER categories that cover the real dataset.
- DELETES all existing SUPPLIER/MANUFACTURER partner profiles (and their
  dependent requests/views), plus seed-owned partner users, so only this real
  data remains. Mentors are left completely untouched.
- Inserts every record as an APPROVED partner profile with rich fields.

Run once:  python scripts/seed_marketplace_suppliers_manufacturers.py
Idempotent: re-running wipes the previous supplier/manufacturer seed and recreates it.
"""
import json
import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.partner_category import PartnerCategory
from app.models.partner_profile import ApprovalStatus, PartnerProfile, PartnerType
from app.models.partner_request import PartnerRequest
from app.models.profile_view import ProfileView
from app.models.user import User, UserRole

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "egypt_partners.json")
DEFAULT_PASSWORD = "partner123"
PARTNER_EMAIL_DOMAIN = "partners.bizify.local"
# Emails of the old fake seed rows that must also be removed.
LEGACY_SEED_EMAILS = {
    "nile.supplies@bizify.com",
    "pyramid.packaging@bizify.com",
    "deltaworks.mfg@bizify.com",
    "redsea.mfg@bizify.com",
}

TYPE_MAP = {
    "supplier": (PartnerType.SUPPLIER, UserRole.SUPPLIER),
    "manufacturer": (PartnerType.MANUFACTURER, UserRole.MANUFACTURER),
}


# ── Category mapping ────────────────────────────────────────────────────────────
def canonical_category(record: dict) -> str:
    industry = (record.get("industry") or "").lower()
    tags = " ".join(record.get("industry_tags") or []).lower()
    blob = f"{industry} {tags}"

    if "packaging machinery" in industry or "machinery" in blob:
        return "Packaging Machinery"
    if "paint" in blob:
        return "Paints & Coatings"
    if "chemical" in blob:
        return "Chemicals"
    if "food" in blob or "beverage" in blob:
        return "Food & Beverage"
    if "printing" in industry:
        return "Printing"
    if "textile" in blob or "apparel" in blob or "cotton" in blob:
        return "Textiles & Apparel"
    if "packaging" in blob:
        return "Packaging"
    if "plastic" in blob or "polymer" in blob:
        return "Plastics & Polymers"
    if "metal" in blob:
        return "Metal & Industrial"
    return "Other"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:60] or "partner"


def synth_description(record: dict) -> str:
    biz = record.get("business_type", "Partner")
    industry = record.get("industry", "")
    city = record.get("city") or record.get("governorate") or "Egypt"
    products = record.get("products") or record.get("product_tags") or []
    caps = record.get("manufacturing_capabilities") or []
    lead = f"{industry} {biz.lower()} based in {city}.".strip()
    if products:
        lead += " Products: " + ", ".join(products[:5]) + "."
    elif caps:
        lead += " Capabilities: " + ", ".join(caps[:5]) + "."
    return lead


def estimated_size(record: dict) -> str | None:
    return record.get("estimated_business_size") or record.get("estimated_factory_size")


# ── Upserts ─────────────────────────────────────────────────────────────────────
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


def _wipe_existing_suppliers_manufacturers(db) -> int:
    """Delete all SUPPLIER/MANUFACTURER profiles + dependents, and seed-owned users."""
    profiles = (
        db.query(PartnerProfile)
        .filter(PartnerProfile.partner_type.in_([PartnerType.SUPPLIER, PartnerType.MANUFACTURER]))
        .all()
    )
    profile_ids = [p.id for p in profiles]
    user_ids = [p.user_id for p in profiles]

    if profile_ids:
        db.query(ProfileView).filter(ProfileView.partner_id.in_(profile_ids)).delete(
            synchronize_session=False
        )
        db.query(PartnerRequest).filter(PartnerRequest.partner_id.in_(profile_ids)).delete(
            synchronize_session=False
        )
        db.query(PartnerProfile).filter(PartnerProfile.id.in_(profile_ids)).delete(
            synchronize_session=False
        )

    # Remove backing users that are clearly seed accounts (don't touch real users
    # who might have other data — only the legacy fakes and our synthetic domain).
    seed_user_ids = []
    if user_ids:
        seed_users = (
            db.query(User)
            .filter(User.id.in_(user_ids))
            .filter(
                (User.email.in_(LEGACY_SEED_EMAILS))
                | (User.email.like(f"%@{PARTNER_EMAIL_DOMAIN}"))
            )
            .all()
        )
        seed_user_ids = [u.id for u in seed_users]
        if seed_user_ids:
            db.query(User).filter(User.id.in_(seed_user_ids)).delete(synchronize_session=False)

    db.flush()
    return len(profile_ids)


def _create_partner(db, record: dict, category_id) -> None:
    partner_type, role = TYPE_MAP[record["business_type"].lower()]
    name = record["company_name"]
    email = f"{slugify(name)}@{PARTNER_EMAIL_DOMAIN}"

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            password_hash=get_password_hash(DEFAULT_PASSWORD),
            full_name=name,
            role=role,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.flush()

    tags = record.get("products") or record.get("product_tags") or []

    details = {
        "whatsapp":               record.get("whatsapp"),
        "email":                  record.get("email"),
        "website":                record.get("website"),
        "facebook_url":           record.get("facebook_url"),
        "facebook_followers":     record.get("facebook_followers"),
        "instagram_url":          record.get("instagram_url"),
        "tiktok_url":             record.get("tiktok_url"),
        "google_maps_url":        record.get("google_maps_url"),
        "google_rating":          record.get("google_rating"),
        "review_count":           record.get("review_count"),
        "address":                record.get("address") or record.get("factory_address"),
        "area":                   record.get("area") or record.get("factory_area"),
        "city":                   record.get("city"),
        "governorate":            record.get("governorate"),
        "industry":               record.get("industry"),
        "business_model":         record.get("business_model"),
        "minimum_order_quantity": record.get("minimum_order_quantity") or None,
        "delivery_available":     record.get("delivery_available"),
        "estimated_size":         estimated_size(record),
        "factory_name":           record.get("factory_name") or None,
        "factory_address":        record.get("factory_address"),
        "factory_area":           record.get("factory_area"),
        "production_capacity":    record.get("production_capacity"),
        "private_label_available":record.get("private_label_available"),
        "exporting":              record.get("exporting"),
        "year_founded":           record.get("year_founded"),
        "employee_count":         record.get("employee_count"),
        "verification_score":     record.get("verification_score"),
        "last_verified_date":     record.get("last_verified_date") or None,
        "industry_tags":          record.get("industry_tags") or None,
        "product_tags":           record.get("product_tags") or None,
        "products":               record.get("products") or None,
        "brands_distributed":     record.get("brands_distributed") or None,
        "distribution_areas":     record.get("distribution_areas") or None,
        "manufacturing_capabilities": record.get("manufacturing_capabilities") or None,
        "certifications":         record.get("certifications") or None,
        "export_countries":       record.get("export_countries") or None,
        "source_urls":            record.get("source_urls") or None,
    }

    profile = PartnerProfile(
        user_id=user.id,
        partner_type=partner_type,
        company_name=name,
        phone_number=record.get("phone"),
        description=synth_description(record),
        services_json=tags,
        skills_json=tags,
        experience_json=None,
        category_id=category_id,
        country=record.get("country"),
        approval_status=ApprovalStatus.APPROVED,
        details_json=details,
    )
    db.add(profile)


def seed():
    with open(DATA_FILE, encoding="utf-8") as fh:
        records = json.load(fh)

    db = SessionLocal()
    try:
        print(f"Loaded {len(records)} real partner records from {DATA_FILE}")

        removed = _wipe_existing_suppliers_manufacturers(db)
        print(f"Removed {removed} existing supplier/manufacturer profiles.")

        cat_cache: dict[tuple[str, PartnerType], PartnerCategory] = {}
        created = 0
        for record in records:
            biz = (record.get("business_type") or "").lower()
            if biz not in TYPE_MAP:
                print(f"  Skipping (unknown business_type): {record.get('company_name')}")
                continue
            partner_type, _ = TYPE_MAP[biz]
            cat_name = canonical_category(record)
            key = (cat_name, partner_type)
            if key not in cat_cache:
                cat_cache[key] = _upsert_category(db, name=cat_name, partner_type=partner_type)
            _create_partner(db, record, cat_cache[key].id)
            created += 1
            print(f"  + [{partner_type.value}] {record['company_name']} -> {cat_name}")

        db.commit()
        print(f"\nDone. {created} real partners seeded across {len(cat_cache)} categories.")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"Error: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
