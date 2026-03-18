"""Add change_events table for deploy and config correlation.

Revision ID: 002_change_events
Revises: 001_initial
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "002_change_events"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "change_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("change_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("version", sa.String(length=100), nullable=True),
        sa.Column("extra_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_change_events_tenant_time", "change_events", ["tenant_id", "timestamp"])
    op.create_index("idx_change_events_asset_time", "change_events", ["asset_id", "timestamp"])


def downgrade() -> None:
    op.drop_index("idx_change_events_asset_time", table_name="change_events")
    op.drop_index("idx_change_events_tenant_time", table_name="change_events")
    op.drop_table("change_events")
