"""Public marketplace browse + facets on the new model.

Top-level types: All / Suppliers / Mentors  (Manufacturer is a business_model, not a type).
Suppliers expose two orthogonal facets: category (industry) and business_model. Counts are
computed live and respect the active type + search. Only APPROVED, non-archived rows show.
Card fields are concise: company, category, short about, location, tags, business_model, contact_status.
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User

router = APIRouter()

CANON_BM = ["Manufacturer", "Distributor", "Exporter", "Trader", "Unknown"]
# fold legacy/null business_model into the canonical set
BM_EXPR = ("CASE WHEN details_json->>'business_model' IN "
           "('Manufacturer','Distributor','Exporter','Trader') "
           "THEN details_json->>'business_model' ELSE 'Unknown' END")


def _base_where(ptype: str, q: Optional[str], params: dict) -> list[str]:
    w = ["approval_status = 'APPROVED'",
         "COALESCE(details_json->>'archived','false') <> 'true'"]
    if ptype in ("supplier", "mentor"):
        w.append("partner_type = :pt"); params["pt"] = ptype.upper()
    if q:
        w.append("(company_name ILIKE :q OR details_json->>'category' ILIKE :q "
                 "OR details_json->>'about' ILIKE :q OR details_json->>'tags' ILIKE :q)")
        params["q"] = f"%{q}%"
    return w


@router.get("/facets")
def marketplace_facets(
    type: str = "all",
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    # type counts: ignore the type selection (so tabs always show all three), respect q + approved + archived
    tparams: dict = {}
    tbase = " AND ".join(_base_where("all", q, tparams))
    type_counts = {"supplier": 0, "mentor": 0}
    for k, c in db.execute(text(
        f"SELECT lower(partner_type::text) AS t, COUNT(*) c FROM partner_profiles WHERE {tbase} GROUP BY t"), tparams):
        if k in type_counts:
            type_counts[k] = c
    type_counts["all"] = type_counts["supplier"] + type_counts["mentor"]

    # category + business_model facets scoped to the active type (+search)
    params: dict = {}
    base = " AND ".join(_base_where(type, q, params))

    def facet(expr: str) -> dict:
        return {str(k): c for k, c in db.execute(text(
            f"SELECT {expr} AS k, COUNT(*) c FROM partner_profiles WHERE {base} GROUP BY k"), params) if k is not None}

    if type == "mentor":
        categories: list = []
        business_models: dict = {}
    else:
        categories = [{"slug": s, "name": n, "count": c} for s, n, c in db.execute(text(
            f"SELECT details_json->>'category_slug' AS s, details_json->>'category' AS n, COUNT(*) c "
            f"FROM partner_profiles WHERE {base} GROUP BY s, n ORDER BY c DESC"), params) if s]
        business_models = facet(BM_EXPR)
    return {"type_counts": type_counts, "categories": categories, "business_models": business_models}


@router.get("/browse")
def marketplace_browse(
    type: str = "all",
    category: Optional[str] = None,          # category_slug
    business_model: Optional[str] = None,    # canonical
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=60),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    params: dict = {}
    w = _base_where(type, q, params)
    if category:
        w.append("details_json->>'category_slug' = :cat"); params["cat"] = category
    if business_model:
        w.append(f"({BM_EXPR}) = :bm"); params["bm"] = business_model
    where = " AND ".join(w)

    total = db.execute(text(f"SELECT COUNT(*) FROM partner_profiles WHERE {where}"), params).scalar() or 0
    pp = {**params, "lim": page_size, "off": (page - 1) * page_size}
    items = [dict(r) for r in db.execute(text(
        f"SELECT id, company_name, partner_type::text AS partner_type, {BM_EXPR} AS business_model, "
        f"COALESCE(details_json->>'category', "
        f"  (SELECT name FROM partner_categories WHERE id = category_id LIMIT 1)) AS category, "
        f"details_json->>'category_slug' AS category_slug, "
        f"COALESCE(details_json->>'about', about_summary, description) AS about, "
        f"COALESCE(details_json->>'city', '') AS city, "
        f"COALESCE(details_json->>'country', country) AS country, "
        f"COALESCE(details_json->'tags', details_json->'product_tags', skills_json) AS tags, "
        f"CASE WHEN COALESCE(details_json->>'phone', phone_number) IS NOT NULL "
        f"  OR details_json->>'whatsapp' IS NOT NULL THEN 'direct' ELSE 'pending' END AS contact_status, "
        f"COALESCE(details_json->>'phone', phone_number) AS phone, "
        f"details_json->>'whatsapp' AS whatsapp, details_json->>'website' AS website "
        f"FROM partner_profiles WHERE {where} ORDER BY company_name LIMIT :lim OFFSET :off"), pp).mappings()]
    return {"total": total, "page": page, "page_size": page_size,
            "has_more": (page * page_size) < total, "items": items}
