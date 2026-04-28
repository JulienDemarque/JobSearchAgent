"""Add interviewed opportunity status.

Revision ID: 0002_add_interviewed_status
Revises: 0001_initial_schema
Create Date: 2026-04-28
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_add_interviewed_status"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE opportunitystatus ADD VALUE IF NOT EXISTS 'interviewed'")


def downgrade() -> None:
    # PostgreSQL cannot drop enum values directly without rebuilding dependent columns.
    pass
