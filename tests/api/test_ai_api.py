from fastapi.testclient import TestClient

import app.models as models
from app.models.enums import BusinessStage, StageType


def test_create_and_list_agent_runs(client: TestClient, db, auth_headers: dict, test_user):
    agent = models.Agent(name="Runner", phase="research")
    db.add(agent)
    db.commit()
    db.refresh(agent)

    business = models.Business(owner_id=test_user.id, stage=BusinessStage.EARLY, context_json={"market": "ai"})
    db.add(business)
    db.commit()
    db.refresh(business)

    roadmap = models.BusinessRoadmap(business_id=business.id)
    db.add(roadmap)
    db.commit()
    db.refresh(roadmap)

    stage = models.RoadmapStage(
        roadmap_id=roadmap.id,
        order_index=1,
        stage_type=StageType.RESEARCH,
    )
    db.add(stage)
    db.commit()
    db.refresh(stage)

    create_payload = {
        "stage_id": str(stage.id),
        "agent_id": str(agent.id),
    }
    create_res = client.post("/api/v1/agent_runs/", json=create_payload, headers=auth_headers)
    assert create_res.status_code == 200

    list_res = client.get("/api/v1/agent_runs/", headers=auth_headers)
    assert list_res.status_code == 200
    runs = list_res.json()
    assert len(runs) == 1
    assert runs[0]["stage_id"] == str(stage.id)
