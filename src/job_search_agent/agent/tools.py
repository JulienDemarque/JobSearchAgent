from typing import Any

from pydantic import BaseModel, Field
from sqlmodel import Session

from job_search_agent.api.schemas import (
    OpportunityCreate,
    UserProfileCreate,
    UserProfileUpdate,
)
from job_search_agent.db.repositories import (
    create_opportunities as repo_create_opportunities,
)
from job_search_agent.db.repositories import (
    create_opportunity as repo_create_opportunity,
)
from job_search_agent.db.repositories import (
    create_user_profile,
    get_active_user_profile,
    update_user_profile,
)
from job_search_agent.db.repositories import (
    list_opportunities as repo_list_opportunities,
)
from job_search_agent.db.session import engine


class OpportunityToolInput(BaseModel):
    """A single job opportunity parsed from user-provided text, CSV, or a table."""

    url: str | None = Field(
        default=None,
        description="Canonical job posting URL, if present.",
    )
    title: str | None = Field(
        default=None,
        description="Job title or role name, if present.",
    )
    company: str | None = Field(
        default=None,
        description="Company or employer name, if present.",
    )
    location: str | None = Field(
        default=None,
        description="Job location, remote policy, or region, if present.",
    )
    description: str = Field(
        default="",
        description="Short job description, notes, or raw row text when no description exists.",
    )
    score: int | None = Field(
        default=None,
        ge=0,
        le=25,
        description="Total fit score from 0 to 25, if provided or scored.",
    )
    score_reason: str | None = Field(
        default=None,
        description="Short explanation for the total fit score and sub-score rationale.",
    )
    source: str | None = Field(
        default=None,
        description="Where this opportunity came from, such as LinkedIn, Indeed, or pasted CSV.",
    )
    raw_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Original row values, priority, score sub-fields, or extra columns that do not fit "
            "the standard fields."
        ),
    )


class IngestResumeTextInput(BaseModel):
    """Pasted resume text and optional matching preferences from the user."""

    resume_text: str = Field(
        min_length=1,
        description="The user's pasted plain-text resume.",
    )
    preferences: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional job-search preferences such as target roles or locations.",
    )


class UpdateActiveProfileBriefInput(BaseModel):
    """Reviewed or draft profile summary extracted from the active resume."""

    profile_brief: str = Field(
        min_length=1,
        description="Compact profile summary to include in frequent matching prompts.",
    )
    profile_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured resume/profile facts extracted from the user's resume.",
    )
    reviewed: bool = Field(
        default=False,
        description="Whether the user has reviewed and approved this profile brief.",
    )


class BulkCreateOpportunitiesInput(BaseModel):
    """A batch of job opportunities parsed from a CSV, table, or long list."""

    opportunities: list[OpportunityToolInput] = Field(
        min_length=1,
        description="All opportunities to create in one batch.",
    )


def ingest_resume_text(input: IngestResumeTextInput) -> dict[str, Any]:
    """Store pasted resume text and optional job preferences as the active user profile."""
    payload = UserProfileCreate(
        resume_text=input.resume_text,
        preferences=input.preferences,
    )
    with Session(engine) as session:
        profile = create_user_profile(
            session,
            resume_text=payload.resume_text,
            preferences=payload.preferences,
        )
        return {
            "id": str(profile.id),
            "version": profile.version,
            "ingestion_status": profile.ingestion_status,
            "reviewed": profile.reviewed,
        }


def get_active_profile_brief() -> dict[str, Any]:
    """Return the compact profile brief and preferences for opportunity matching."""
    with Session(engine) as session:
        profile = get_active_user_profile(session)
        if profile is None:
            return {"found": False, "message": "No active user profile exists yet."}
        return {
            "found": True,
            "id": str(profile.id),
            "version": profile.version,
            "profile_brief": profile.profile_brief,
            "preferences": profile.preferences,
            "reviewed": profile.reviewed,
        }


def update_active_profile_brief(input: UpdateActiveProfileBriefInput) -> dict[str, Any]:
    """Update the active profile brief after extracting or reviewing resume details."""
    with Session(engine) as session:
        profile = get_active_user_profile(session)
        if profile is None:
            return {"updated": False, "message": "No active user profile exists yet."}
        updated = update_user_profile(
            session,
            profile,
            UserProfileUpdate(
                profile_brief=input.profile_brief,
                profile_data=input.profile_data,
                reviewed=input.reviewed,
            ),
        )
        return {"updated": True, "id": str(updated.id), "version": updated.version}


def create_opportunity(input: OpportunityToolInput) -> dict[str, Any]:
    """Create a tracked job opportunity from a link or pasted job description."""
    with Session(engine) as session:
        opportunity = repo_create_opportunity(
            session,
            OpportunityCreate.model_validate(input.model_dump()),
        )
        return {
            "id": str(opportunity.id),
            "url": opportunity.url,
            "title": opportunity.title,
            "company": opportunity.company,
            "score": opportunity.score,
            "status": opportunity.status,
        }


def bulk_create_opportunities(input: BulkCreateOpportunitiesInput) -> dict[str, Any]:
    """Create many tracked job opportunities from a pasted CSV, table, or long list.

    Use this instead of repeatedly calling create_opportunity when the user provides
    multiple opportunities in one message. Map arbitrary user-provided columns into
    the typed fields, and preserve unknown columns in raw_metadata.
    """
    validated = [
        OpportunityCreate.model_validate(opportunity.model_dump())
        for opportunity in input.opportunities
    ]
    with Session(engine) as session:
        created = repo_create_opportunities(session, validated)
        return {
            "created_count": len(created),
            "opportunity_ids": [str(opportunity.id) for opportunity in created],
            "opportunities": [
                {
                    "id": str(opportunity.id),
                    "url": opportunity.url,
                    "title": opportunity.title,
                    "company": opportunity.company,
                    "score": opportunity.score,
                    "status": opportunity.status,
                }
                for opportunity in created
            ],
        }


def list_opportunities() -> list[dict[str, Any]]:
    """List tracked opportunities for search, filtering, and table display."""
    with Session(engine) as session:
        opportunities = repo_list_opportunities(session)
        return [
            {
                "id": str(opportunity.id),
                "url": opportunity.url,
                "title": opportunity.title,
                "company": opportunity.company,
                "location": opportunity.location,
                "score": opportunity.score,
                "status": opportunity.status,
                "applied": opportunity.applied,
                "updated_at": opportunity.updated_at.isoformat(),
            }
            for opportunity in opportunities
        ]
