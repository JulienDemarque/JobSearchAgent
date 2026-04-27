import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from job_search_agent.db.models import OpportunityStatus, ProfileIngestionStatus


class UserProfileCreate(BaseModel):
    resume_text: str = Field(min_length=1)
    preferences: dict[str, Any] = Field(default_factory=dict)


class UserProfileUpdate(BaseModel):
    resume_text: str | None = None
    profile_brief: str | None = None
    profile_data: dict[str, Any] | None = None
    preferences: dict[str, Any] | None = None
    ingestion_status: ProfileIngestionStatus | None = None
    reviewed: bool | None = None
    active: bool | None = None


class UserProfileRead(BaseModel):
    id: uuid.UUID
    resume_text: str
    profile_brief: str
    profile_data: dict[str, Any]
    preferences: dict[str, Any]
    ingestion_status: ProfileIngestionStatus
    version: int
    reviewed: bool
    active: bool
    created_at: datetime
    updated_at: datetime


class OpportunityCreate(BaseModel):
    url: str | None = None
    source: str | None = None
    title: str | None = None
    company: str | None = None
    location: str | None = None
    description: str = ""
    score: int | None = Field(default=None, ge=0, le=25)
    score_reason: str | None = None
    applied: bool = False
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class OpportunityBulkCreate(BaseModel):
    opportunities: list[OpportunityCreate] = Field(min_length=1)


class OpportunityUpdate(BaseModel):
    url: str | None = None
    source: str | None = None
    title: str | None = None
    company: str | None = None
    location: str | None = None
    description: str | None = None
    score: int | None = Field(default=None, ge=0, le=25)
    score_reason: str | None = None
    status: OpportunityStatus | None = None
    applied: bool | None = None
    raw_metadata: dict[str, Any] | None = None


class OpportunityRead(BaseModel):
    id: uuid.UUID
    url: str | None
    source: str | None
    title: str | None
    company: str | None
    location: str | None
    description: str
    score: int | None
    score_reason: str | None
    status: OpportunityStatus
    applied: bool
    applied_at: datetime | None
    profile_version: int | None
    raw_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

