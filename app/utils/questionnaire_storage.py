from typing import Any, Dict, List, Optional

def coerce_dict(data: Any) -> Dict[str, Any]:
    """Ensure the input is a dictionary, even if it is None or a string."""
    if isinstance(data, dict):
        return data
    return {}

def merge_questionnaire(old_json: Optional[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
    """Merge new blocks into the existing questionnaire JSON."""
    result = coerce_dict(old_json).copy()
    for key, value in kwargs.items():
        result[key] = value
    return result

def get_user_profile_block(json_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract the user_profile block from questionnaire JSON."""
    data = coerce_dict(json_data)
    return coerce_dict(data.get("user_profile"))

def get_career_profile_block(json_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract the career_profile block from questionnaire JSON."""
    data = coerce_dict(json_data)
    return coerce_dict(data.get("career_profile"))

def strip_personalization(json_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Remove the personalization_profile block to force regeneration."""
    if not json_data:
        return None
    data = coerce_dict(json_data).copy()
    if "personalization_profile" in data:
        del data["personalization_profile"]
    return data
