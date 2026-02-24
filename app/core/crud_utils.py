from datetime import datetime, timezone
from typing import Any, Dict, cast

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_update_dict(obj_in: Any) -> Dict[str, Any]:
    if obj_in is None:
        return {}
    if hasattr(obj_in, "model_dump"):
        return cast(Dict[str, Any], obj_in.model_dump(exclude_unset=True))
    return cast(Dict[str, Any], dict(obj_in))


def _apply_updates(db_obj: Any, update_data: Dict[str, Any]) -> Any:
    for field, value in update_data.items():
        if hasattr(db_obj, field):
            setattr(db_obj, field, value)
    return cast(Any, db_obj)
