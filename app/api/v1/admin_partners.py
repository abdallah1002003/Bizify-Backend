"""Admin review workflow for imported partner suppliers.

Lets an admin filter imported suppliers (by category, business_model, contact_status,
approval_status, search), see live facet counts, bulk approve/reject/archive, and
override business_model / partner_type per row.

Model:
  partner_type        : SUPPLIER | MENTOR        (Manufacturer is NOT a partner type)
  details_json.business_model : Manufacturer | Distributor | Exporter | Trader | Unknown
  details_json.provenance='imported', contact_status, category, category_slug, archived
  approval_status     : PENDING | APPROVED | REJECTED   (imported land as PENDING/hidden)
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import RoleChecker, get_db
from app.models.user import User, UserRole

router = APIRouter()
_ADMIN = RoleChecker([UserRole.ADMIN])

CANON_BM = ["Manufacturer", "Distributor", "Exporter", "Trader", "Unknown"]
# fold any legacy/null business_model into the canonical set (everything non-canonical -> Unknown)
BM_EXPR = ("CASE WHEN details_json->>'business_model' IN "
           "('Manufacturer','Distributor','Exporter','Trader') "
           "THEN details_json->>'business_model' ELSE 'Unknown' END")


class BulkAction(BaseModel):
    action: str           # approve | reject | archive | unarchive
    ids: list[str]


class PartnerOverride(BaseModel):
    business_model: Optional[str] = None   # one of CANON_BM
    partner_type: Optional[str] = None     # SUPPLIER | MENTOR


@router.get("/imported-partners")
def list_imported_partners(
    imported_only: bool = True,
    partner_type: str = "SUPPLIER",
    category: Optional[str] = None,          # category_slug
    business_model: Optional[str] = None,    # canonical
    contact_status: Optional[str] = None,    # direct | pending
    approval_status: Optional[str] = None,   # PENDING | APPROVED | REJECTED
    q: Optional[str] = None,
    include_archived: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin: User = Depends(_ADMIN),
) -> dict[str, Any]:
    # base filter shared by list + facets (tab + search + archived); facet-specific
    # selections (category/bm/contact/status) are applied to the LIST only.
    base = ["partner_type = :pt"]
    params: dict[str, Any] = {"pt": partner_type}
    if imported_only:
        base.append("details_json->>'provenance' = 'imported'")
    if not include_archived:
        base.append("COALESCE(details_json->>'archived','false') <> 'true'")
    if q:
        base.append("company_name ILIKE :q"); params["q"] = f"%{q}%"
    base_sql = " AND ".join(base)

    list_where = list(base)
    if category:
        list_where.append("details_json->>'category_slug' = :cat"); params["cat"] = category
    if business_model:
        list_where.append(f"({BM_EXPR}) = :bm"); params["bm"] = business_model
    if contact_status:
        list_where.append("details_json->>'contact_status' = :cs"); params["cs"] = contact_status
    if approval_status:
        list_where.append("approval_status::text = :ast"); params["ast"] = approval_status
    list_sql = " AND ".join(list_where)

    total = db.execute(text(f"SELECT COUNT(*) FROM partner_profiles WHERE {list_sql}"), params).scalar() or 0
    params_p = {**params, "lim": page_size, "off": (page - 1) * page_size}
    items = [dict(r) for r in db.execute(text(
        f"SELECT id, company_name, partner_type, approval_status::text AS approval_status, "
        f"details_json->>'category' AS category, details_json->>'category_slug' AS category_slug, "
        f"{BM_EXPR} AS business_model, details_json->>'contact_status' AS contact_status, "
        f"details_json->>'city' AS city, details_json->>'country' AS country, "
        f"details_json->>'phone' AS phone, details_json->>'whatsapp' AS whatsapp, "
        f"details_json->>'website' AS website, details_json->>'about' AS about, "
        f"details_json->'tags' AS tags, details_json->>'type_confidence' AS type_confidence, "
        f"details_json->>'type_reason' AS type_reason, details_json->>'source_url' AS source_url, "
        f"COALESCE(details_json->>'archived','false') AS archived "
        f"FROM partner_profiles WHERE {list_sql} ORDER BY company_name LIMIT :lim OFFSET :off"),
        params_p).mappings()]

    def facet(expr: str) -> dict:
        rows = db.execute(text(
            f"SELECT {expr} AS k, COUNT(*) AS c FROM partner_profiles WHERE {base_sql} GROUP BY k"), params).all()
        return {str(k): c for k, c in rows if k is not None}

    facets = {
        "business_model": facet(BM_EXPR),
        "category": facet("details_json->>'category'"),
        "contact_status": facet("details_json->>'contact_status'"),
        "approval_status": facet("approval_status::text"),
    }
    return {"total": total, "page": page, "page_size": page_size, "items": items, "facets": facets}


@router.post("/imported-partners/bulk")
def bulk_action(
    body: BulkAction,
    db: Session = Depends(get_db),
    admin: User = Depends(_ADMIN),
) -> dict[str, Any]:
    if not body.ids:
        raise HTTPException(status_code=400, detail="No ids provided")
    ids = body.ids
    now = datetime.utcnow()
    if body.action == "approve":
        sql = ("UPDATE partner_profiles SET approval_status='APPROVED', approved_by=:adm, "
               "approved_at=:now WHERE id = ANY(CAST(:ids AS uuid[]))")
        params = {"adm": admin.id, "now": now, "ids": ids}
    elif body.action == "reject":
        sql = ("UPDATE partner_profiles SET approval_status='REJECTED', approved_by=:adm, "
               "approved_at=:now WHERE id = ANY(CAST(:ids AS uuid[]))")
        params = {"adm": admin.id, "now": now, "ids": ids}
    elif body.action == "archive":
        sql = ("UPDATE partner_profiles SET details_json = COALESCE(details_json,'{}'::jsonb) "
               "|| jsonb_build_object('archived', true) WHERE id = ANY(CAST(:ids AS uuid[]))")
        params = {"ids": ids}
    elif body.action == "unarchive":
        sql = ("UPDATE partner_profiles SET details_json = COALESCE(details_json,'{}'::jsonb) "
               "|| jsonb_build_object('archived', false) WHERE id = ANY(CAST(:ids AS uuid[]))")
        params = {"ids": ids}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action '{body.action}'")
    res = db.execute(text(sql), params)
    db.commit()
    return {"action": body.action, "affected": res.rowcount}


@router.patch("/imported-partners/{partner_id}")
def override_partner(
    partner_id: str,
    body: PartnerOverride,
    db: Session = Depends(get_db),
    _admin: User = Depends(_ADMIN),
) -> dict[str, Any]:
    sets, params = [], {"id": partner_id}
    if body.partner_type:
        if body.partner_type not in ("SUPPLIER", "MENTOR"):
            raise HTTPException(status_code=400, detail="partner_type must be SUPPLIER or MENTOR")
        sets.append("partner_type = :pt"); params["pt"] = body.partner_type
    if body.business_model:
        if body.business_model not in CANON_BM:
            raise HTTPException(status_code=400, detail=f"business_model must be one of {CANON_BM}")
        sets.append("details_json = COALESCE(details_json,'{}'::jsonb) || "
                    "jsonb_build_object('business_model', :bm, 'classification_source', 'admin_override')")
        params["bm"] = body.business_model
    if not sets:
        raise HTTPException(status_code=400, detail="Nothing to update")
    res = db.execute(text(f"UPDATE partner_profiles SET {', '.join(sets)} WHERE id=:id"), params)
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Partner not found")
    return {"id": partner_id, "updated": True}
