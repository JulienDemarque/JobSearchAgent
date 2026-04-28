"""Initial profile and opportunity schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

profile_ingestion_status = postgresql.ENUM(
    "text_received",
    "profile_extracted",
    "needs_review",
    "active",
    "failed",
    name="profileingestionstatus",
    create_type=False,
)

opportunity_status = postgresql.ENUM(
    "new",
    "interested",
    "rejected",
    "applied",
    "interviewing",
    "interviewed",
    "offer",
    "archived",
    name="opportunitystatus",
    create_type=False,
)


def upgrade() -> None:
    profile_ingestion_status.create(op.get_bind(), checkfirst=True)
    opportunity_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "user_profile",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("resume_text", sa.String(), nullable=False),
        sa.Column("profile_brief", sa.String(), nullable=False),
        sa.Column("profile_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ingestion_status", profile_ingestion_status, nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("reviewed", sa.Boolean(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "opportunity",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("score_reason", sa.String(), nullable=True),
        sa.Column("status", opportunity_status, nullable=False),
        sa.Column("applied", sa.Boolean(), nullable=False),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.Column("profile_version", sa.Integer(), nullable=True),
        sa.Column("raw_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint("score >= 0 AND score <= 100", name="ck_opportunity_score_range"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_opportunity_applied", "opportunity", ["applied"])
    op.create_index("ix_opportunity_company", "opportunity", ["company"])
    op.create_index("ix_opportunity_status", "opportunity", ["status"])
    op.create_index("ix_opportunity_title", "opportunity", ["title"])
    op.create_index("ix_opportunity_url", "opportunity", ["url"])


def downgrade() -> None:
    op.drop_index("ix_opportunity_url", table_name="opportunity")
    op.drop_index("ix_opportunity_title", table_name="opportunity")
    op.drop_index("ix_opportunity_status", table_name="opportunity")
    op.drop_index("ix_opportunity_company", table_name="opportunity")
    op.drop_index("ix_opportunity_applied", table_name="opportunity")
    op.drop_table("opportunity")
    op.drop_table("user_profile")
    opportunity_status.drop(op.get_bind(), checkfirst=True)
    profile_ingestion_status.drop(op.get_bind(), checkfirst=True)

