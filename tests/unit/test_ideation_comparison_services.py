from uuid import uuid4

import app.models as models
from app.models.enums import UserRole
from app.core.security import get_password_hash
from app.services.ideation import (
    idea_comparison,
    idea_comparison_item,
    idea_comparison_metric,
)

class DummyModel:
    def __init__(self, **data):
        self._data = data

    def model_dump(self, exclude_unset: bool = True):
        _ = exclude_unset
        return dict(self._data)

def _create_user(db, prefix: str) -> models.User:
    user = models.User(
        name=f"{prefix}-user",
        email=f"{prefix}_{uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash("testpass123"),
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def _create_idea(db, owner_id, title: str) -> models.Idea:
    idea = models.Idea(
        owner_id=owner_id,
        title=title,
        description="test idea",
    )
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea

# ---------------------------------------------------------------------------
# Idea Comparison Tests
# ---------------------------------------------------------------------------

def test_idea_comparison_crud(db):
    user = _create_user(db, "comp_cr")
    
    # 1. create_idea_comparison
    input_data = {"name": "Test Comparison", "user_id": user.id}
    comp = idea_comparison.create_idea_comparison(db, input_data)
    assert comp.name == "Test Comparison"
    assert comp.user_id == user.id
    
    # 2. get_idea_comparison
    found = idea_comparison.get_idea_comparison(db, comp.id)
    assert found is not None
    assert found.id == comp.id
    
    # 3. get_idea_comparisons
    all_comps = idea_comparison.get_idea_comparisons(db, skip=0, limit=10)
    assert len(all_comps) >= 1
    
    # 4. update_idea_comparison
    updated = idea_comparison.update_idea_comparison(db, comp, {"name": "Updated Name"})
    assert updated.name == "Updated Name"
    
    # 5. create_comparison (convenience)
    conv_comp = idea_comparison.create_comparison(db, "Convenience", user.id)
    assert conv_comp.name == "Convenience"
    
    # 6. delete_idea_comparison
    idea_comparison.delete_idea_comparison(db, conv_comp.id)
    assert idea_comparison.get_idea_comparison(db, conv_comp.id) is None
    
    # delete non-existent
    assert idea_comparison.delete_idea_comparison(db, uuid4()) is None

# ---------------------------------------------------------------------------
# Comparison Item Tests
# ---------------------------------------------------------------------------

def test_comparison_item_crud_and_ranking(db):
    user = _create_user(db, "item_user")
    idea1 = _create_idea(db, user.id, "Idea 1")
    idea2 = _create_idea(db, user.id, "Idea 2")
    comp = idea_comparison.create_comparison(db, "Ranking Comp", user.id)
    
    # 1. add_item_to_comparison (first item - rank 0)
    item1 = idea_comparison_item.add_item_to_comparison(db, comp.id, idea1.id)
    assert item1.rank_index == 0
    assert item1.comparison_id == comp.id
    assert item1.idea_id == idea1.id
    
    # 2. add_item_to_comparison (second item - rank 1)
    item2 = idea_comparison_item.add_item_to_comparison(db, comp.id, idea2.id)
    assert item2.rank_index == 1
    
    # 3. get_comparison_item
    found = idea_comparison_item.get_comparison_item(db, item1.id)
    assert found.id == item1.id
    
    # 4. get_comparison_items
    all_items = idea_comparison_item.get_comparison_items(db)
    assert len(all_items) >= 2
    
    # 5. update_comparison_item
    updated = idea_comparison_item.update_comparison_item(db, item1, {"rank_index": 10})
    assert updated.rank_index == 10
    
    # 6. create_comparison_item (direct)
    direct = idea_comparison_item.create_comparison_item(db, {"comparison_id": comp.id, "idea_id": idea1.id, "rank_index": 5})
    assert direct.rank_index == 5
    
    # 7. delete_comparison_item
    idea_comparison_item.delete_comparison_item(db, direct.id)
    assert idea_comparison_item.get_comparison_item(db, direct.id) is None
    assert idea_comparison_item.delete_comparison_item(db, uuid4()) is None

# ---------------------------------------------------------------------------
# Comparison Metric Tests
# ---------------------------------------------------------------------------

def test_comparison_metric_crud(db):
    user = _create_user(db, "metric_user")
    comp = idea_comparison.create_comparison(db, "Metric Comp", user.id)
    
    # 1. create_comparison_metric
    metric_data = {
        "comparison_id": comp.id,
        "metric_name": "Cost",
        "value": 100.0
    }
    metric = idea_comparison_metric.create_comparison_metric(db, metric_data)
    assert metric.metric_name == "Cost"
    assert metric.value == 100.0
    
    # 2. get_comparison_metric
    found = idea_comparison_metric.get_comparison_metric(db, metric.id)
    assert found.id == metric.id
    
    # 3. get_comparison_metrics
    all_metrics = idea_comparison_metric.get_comparison_metrics(db)
    assert len(all_metrics) >= 1
    
    # 4. update_comparison_metric
    updated = idea_comparison_metric.update_comparison_metric(db, metric, {"value": 200.0})
    assert updated.value == 200.0
    
    # 5. delete_comparison_metric
    idea_comparison_metric.delete_comparison_metric(db, metric.id)
    assert idea_comparison_metric.get_comparison_metric(db, metric.id) is None
    assert idea_comparison_metric.delete_comparison_metric(db, uuid4()) is None
