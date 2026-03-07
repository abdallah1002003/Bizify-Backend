import pytest
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

async def _create_user(db, prefix: str) -> models.User:
    user = models.User(
        name=f"{prefix}-user",
        email=f"{prefix}_{uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash("testpass123"),
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def _create_idea(db, owner_id, title: str) -> models.Idea:
    idea = models.Idea(
        owner_id=owner_id,
        title=title,
        description="test idea",
    )
    db.add(idea)
    await db.commit()
    await db.refresh(idea)
    return idea

# ---------------------------------------------------------------------------
# Idea Comparison Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_idea_comparison_crud(async_db):
    user = await _create_user(async_db, "comp_cr")
    
    # 1. create_idea_comparison
    input_data = {"name": "Test Comparison", "user_id": user.id}
    comp = await idea_comparison.IdeaComparisonService(async_db).create_idea_comparison( input_data)
    assert comp.name == "Test Comparison"
    assert comp.user_id == user.id
    
    # 2. get_idea_comparison
    found = await idea_comparison.IdeaComparisonService(async_db).get_idea_comparison( comp.id)
    assert found is not None
    assert found.id == comp.id
    
    # 3. get_idea_comparisons
    all_comps = await idea_comparison.IdeaComparisonService(async_db).get_idea_comparisons( skip=0, limit=10)
    assert len(all_comps) >= 1
    
    # 4. update_idea_comparison
    updated = await idea_comparison.IdeaComparisonService(async_db).update_idea_comparison( comp, {"name": "Updated Name"})
    assert updated.name == "Updated Name"
    
    # 5. create_comparison (convenience)
    conv_comp = await idea_comparison.IdeaComparisonService(async_db).create_comparison( "Convenience", user.id)
    assert conv_comp.name == "Convenience"
    
    # 6. delete_idea_comparison
    await idea_comparison.IdeaComparisonService(async_db).delete_idea_comparison( conv_comp.id)
    assert await idea_comparison.IdeaComparisonService(async_db).get_idea_comparison( conv_comp.id) is None
    
    # delete non-existent
    assert await idea_comparison.IdeaComparisonService(async_db).delete_idea_comparison( uuid4()) is None

# ---------------------------------------------------------------------------
# Comparison Item Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_comparison_item_crud_and_ranking(async_db):
    user = await _create_user(async_db, "item_user")
    idea1 = await _create_idea(async_db, user.id, "Idea 1")
    idea2 = await _create_idea(async_db, user.id, "Idea 2")
    comp = await idea_comparison.IdeaComparisonService(async_db).create_comparison( "Ranking Comp", user.id)
    
    # 1. add_item_to_comparison (first item - rank 0)
    item1 = await idea_comparison_item.ComparisonItemService(async_db).add_item_to_comparison( comp.id, idea1.id)
    assert item1.rank_index == 0
    assert item1.comparison_id == comp.id
    assert item1.idea_id == idea1.id
    
    # 2. add_item_to_comparison (second item - rank 1)
    item2 = await idea_comparison_item.ComparisonItemService(async_db).add_item_to_comparison( comp.id, idea2.id)
    assert item2.rank_index == 1
    
    # 3. get_comparison_item
    found = await idea_comparison_item.ComparisonItemService(async_db).get_comparison_item( item1.id)
    assert found.id == item1.id
    
    # 4. get_comparison_items
    all_items = await idea_comparison_item.ComparisonItemService(async_db).get_comparison_items()
    assert len(all_items) >= 2
    
    # 5. update_comparison_item
    updated = await idea_comparison_item.ComparisonItemService(async_db).update_comparison_item( item1, {"rank_index": 10})
    assert updated.rank_index == 10
    
    # 6. create_comparison_item (direct)
    direct = await idea_comparison_item.ComparisonItemService(async_db).create_comparison_item( {"comparison_id": comp.id, "idea_id": idea1.id, "rank_index": 5})
    assert direct.rank_index == 5
    
    # 7. delete_comparison_item
    await idea_comparison_item.ComparisonItemService(async_db).delete_comparison_item( direct.id)
    assert await idea_comparison_item.ComparisonItemService(async_db).get_comparison_item( direct.id) is None
    assert await idea_comparison_item.ComparisonItemService(async_db).delete_comparison_item( uuid4()) is None

# ---------------------------------------------------------------------------
# Comparison Metric Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_comparison_metric_crud(async_db):
    user = await _create_user(async_db, "metric_user")
    comp = await idea_comparison.IdeaComparisonService(async_db).create_comparison( "Metric Comp", user.id)
    
    # 1. create_comparison_metric
    metric_data = {
        "comparison_id": comp.id,
        "metric_name": "Cost",
        "value": 100.0
    }
    metric = await idea_comparison_metric.ComparisonMetricService(async_db).create_comparison_metric( metric_data)
    assert metric.metric_name == "Cost"
    assert metric.value == 100.0
    
    # 2. get_comparison_metric
    found = await idea_comparison_metric.ComparisonMetricService(async_db).get_comparison_metric( metric.id)
    assert found.id == metric.id
    
    # 3. get_comparison_metrics
    all_metrics = await idea_comparison_metric.ComparisonMetricService(async_db).get_comparison_metrics()
    assert len(all_metrics) >= 1
    
    # 4. update_comparison_metric
    updated = await idea_comparison_metric.ComparisonMetricService(async_db).update_comparison_metric( metric, {"value": 200.0})
    assert updated.value == 200.0
    
    # 5. delete_comparison_metric
    await idea_comparison_metric.ComparisonMetricService(async_db).delete_comparison_metric( metric.id)
    assert await idea_comparison_metric.ComparisonMetricService(async_db).get_comparison_metric( metric.id) is None
    assert await idea_comparison_metric.ComparisonMetricService(async_db).delete_comparison_metric( uuid4()) is None
