import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class OpportunityStatus(StrEnum):
    new = "new"
    interested = "interested"
    rejected = "rejected"
    applied = "applied"
    interviewing = "interviewing"
    offer = "offer"
    archived = "archived"


class ProfileIngestionStatus(StrEnum):
    text_received = "text_received"
    profile_extracted = "profile_extracted"
    needs_review = "needs_review"
    active = "active"
    failed = "failed"


class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)


class UserProfile(TimestampMixin, table=True):
    __tablename__ = "user_profile"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    resume_text: str = Field(default="", nullable=False)
    profile_brief: str = Field(default="", nullable=False)
    profile_data: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    preferences: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    ingestion_status: ProfileIngestionStatus = Field(
        default=ProfileIngestionStatus.text_received,
        nullable=False,
    )
    version: int = Field(default=1, nullable=False)
    reviewed: bool = Field(default=False, nullable=False)
    active: bool = Field(default=True, nullable=False)


class Opportunity(TimestampMixin, table=True):
    __tablename__ = "opportunity"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    url: str | None = Field(default=None, index=True)
    source: str | None = None
    title: str | None = Field(default=None, index=True)
    company: str | None = Field(default=None, index=True)
    location: str | None = None
    description: str = Field(default="", nullable=False)
    score: int | None = Field(default=None, ge=0, le=25)
    score_reason: str | None = None
    status: OpportunityStatus = Field(default=OpportunityStatus.new, nullable=False, index=True)
    applied: bool = Field(default=False, nullable=False, index=True)
    applied_at: datetime | None = None
    profile_version: int | None = None
    raw_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

