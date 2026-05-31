"""add_partner_rich_fields

Adds rich supplier/manufacturer fields to partner_profiles so real-world
directory data (contacts, location, products, capabilities, provenance) can be
stored and shown in the marketplace "View profile" modal.

Revision ID: e1a2b3c4d5e6
Revises: 3cd21a1f0fdf
Create Date: 2026-05-31 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e1a2b3c4d5e6'
down_revision: Union[str, None] = '3cd21a1f0fdf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCALAR_COLUMNS = [
    # Contact / web
    ('whatsapp', sa.String()),
    ('email', sa.String()),
    ('website', sa.String()),
    ('facebook_url', sa.String()),
    ('facebook_followers', sa.Integer()),
    ('instagram_url', sa.String()),
    ('tiktok_url', sa.String()),
    ('google_maps_url', sa.String()),
    ('google_rating', sa.Float()),
    ('review_count', sa.Integer()),
    # Location
    ('address', sa.String()),
    ('area', sa.String()),
    ('city', sa.String()),
    ('governorate', sa.String()),
    # Business classification
    ('industry', sa.String()),
    ('business_model', sa.String()),
    ('minimum_order_quantity', sa.String()),
    ('delivery_available', sa.Boolean()),
    ('estimated_size', sa.String()),
    # Manufacturer-specific
    ('factory_name', sa.String()),
    ('factory_address', sa.String()),
    ('factory_area', sa.String()),
    ('production_capacity', sa.String()),
    ('private_label_available', sa.Boolean()),
    ('exporting', sa.Boolean()),
    ('year_founded', sa.Integer()),
    ('employee_count', sa.Integer()),
    # Provenance
    ('verification_score', sa.Integer()),
    ('last_verified_date', sa.String()),
]

JSON_COLUMNS = [
    'industry_tags',
    'product_tags',
    'products',
    'brands_distributed',
    'distribution_areas',
    'manufacturing_capabilities',
    'certifications',
    'export_countries',
    'source_urls',
]


def upgrade() -> None:
    with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
        for name, col_type in SCALAR_COLUMNS:
            batch_op.add_column(sa.Column(name, col_type, nullable=True))
        for name in JSON_COLUMNS:
            batch_op.add_column(sa.Column(name, sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
        for name in JSON_COLUMNS:
            batch_op.drop_column(name)
        for name, _ in SCALAR_COLUMNS:
            batch_op.drop_column(name)
