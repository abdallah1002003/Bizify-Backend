"""user_profiles: consolidate questionnaire into questionnaire_json

Revision ID: f2c8a91d3e01
Revises: d1f3a5c9b802
Create Date: 2026-05-13

"""
from __future__ import annotations

import json
from typing import Any, Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f2c8a91d3e01"
down_revision: Union[str, None] = "d1f3a5c9b802"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _parse_json_col(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    return value


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column("questionnaire_json", sa.JSON(), nullable=True),
    )
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, interests_json, preferences_json, risk_profile_json, "
            "background_json, personality_json, personalization_profile "
            "FROM user_profiles"
        )
    ).mappings().all()

    for row in rows:
        qj = {
            "user_profile": _parse_json_col(row["background_json"]) or {},
            "career_profile": _parse_json_col(row["personality_json"]) or {},
            "interests": _parse_json_col(row["interests_json"]),
            "preferences": _parse_json_col(row["preferences_json"]),
            "risk_profile": _parse_json_col(row["risk_profile_json"]),
            "personalization_profile": row["personalization_profile"],
        }
        conn.execute(
            sa.text(
                "UPDATE user_profiles SET questionnaire_json = :qj WHERE id = :id"
            ),
            {"qj": qj, "id": row["id"]},
        )

    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.drop_column("interests_json")
        batch_op.drop_column("preferences_json")
        batch_op.drop_column("risk_profile_json")
        batch_op.drop_column("background_json")
        batch_op.drop_column("personality_json")
        batch_op.drop_column("personalization_profile")


def downgrade() -> None:
    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.add_column(sa.Column("interests_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("preferences_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("risk_profile_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("background_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("personality_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("personalization_profile", sa.Text(), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, questionnaire_json FROM user_profiles")
    ).mappings().all()
    for row in rows:
        raw = row["questionnaire_json"]
        data = _parse_json_col(raw) if raw is not None else {}
        if not isinstance(data, dict):
            data = {}

        conn.execute(
            sa.text(
                "UPDATE user_profiles SET "
                "interests_json = :interests, "
                "preferences_json = :preferences, "
                "risk_profile_json = :risk, "
                "background_json = :bg, "
                "personality_json = :pers, "
                "personalization_profile = :pp "
                "WHERE id = :id"
            ),
            {
                "interests": data.get("interests"),
                "preferences": data.get("preferences"),
                "risk": data.get("risk_profile"),
                "bg": data.get("user_profile") or {},
                "pers": data.get("career_profile") or {},
                "pp": data.get("personalization_profile"),
                "id": row["id"],
            },
        )

    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.drop_column("questionnaire_json")
