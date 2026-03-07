
from __future__ import annotations

import logging
from typing import Any, Dict

from app.core.crud_utils import _utc_now
logger = logging.getLogger(__name__)

__all__ = [
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
