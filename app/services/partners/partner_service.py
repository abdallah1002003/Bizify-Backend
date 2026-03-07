<<<<<<< HEAD

=======
>>>>>>> origin/main
from __future__ import annotations

import logging
from typing import Any, Dict

from app.core.crud_utils import _utc_now
<<<<<<< HEAD
logger = logging.getLogger(__name__)

__all__ = [
=======
from app.services.partners.partner_profile import (
    get_partner_profile,
    get_partner_profiles,
    create_partner_profile,
    update_partner_profile,
    delete_partner_profile,
    approve_partner_profile,
    match_partners_by_capability,
)
from app.services.partners.partner_request import (
    get_partner_request,
    get_partner_requests,
    submit_partner_request,
    create_partner_request,
    update_partner_request,
    delete_partner_request,
    transition_request_status,
    accept_partner_request,
)

logger = logging.getLogger(__name__)

__all__ = [
    "get_partner_profile",
    "get_partner_profiles",
    "create_partner_profile",
    "update_partner_profile",
    "delete_partner_profile",
    "approve_partner_profile",
    "match_partners_by_capability",
    "get_partner_request",
    "get_partner_requests",
    "submit_partner_request",
    "create_partner_request",
    "update_partner_request",
    "delete_partner_request",
    "transition_request_status",
    "accept_partner_request",
>>>>>>> origin/main
    "get_detailed_status",
    "reset_internal_state",
]


def get_detailed_status() -> Dict[str, Any]:
    return {
        "module": "partner_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


def reset_internal_state() -> None:
    logger.info("partner_service reset_internal_state called")
