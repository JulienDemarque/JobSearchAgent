import re
import uuid
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from sqlmodel import Session

from job_search_agent.api.schemas import (
    OpportunityCreate,
    OpportunityUpdate,
    UserProfileCreate,
    UserProfileUpdate,
)
from job_search_agent.db.models import OpportunityStatus
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
    get_opportunity as repo_get_opportunity,
)
from job_search_agent.db.repositories import (
    list_opportunities as repo_list_opportunities,
)
from job_search_agent.db.repositories import (
    update_opportunity as repo_update_opportunity,
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
    applied: bool = Field(
        default=False,
        description="Whether the user has already applied to this opportunity.",
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


class ExtractOpportunityFromUrlInput(BaseModel):
    """A known job posting URL to fetch and extract readable page content from."""

    url: str = Field(
        min_length=1,
        description="The full URL of the job posting page to fetch.",
    )


class GetOpportunityInput(BaseModel):
    """A tracked opportunity ID to inspect before updating or drafting materials."""

    opportunity_id: uuid.UUID = Field(
        description="The ID of the opportunity to retrieve.",
    )


class ListOpportunitiesInput(BaseModel):
    """Optional filters for searching tracked opportunities."""

    query: str | None = Field(
        default=None,
        description=(
            "Free-text search across title, company, location, URL, source, and description."
        ),
    )
    status: OpportunityStatus | None = Field(
        default=None,
        description="Filter by workflow status.",
    )
    applied: bool | None = Field(
        default=None,
        description="Filter by whether the user has applied.",
    )
    min_score: int | None = Field(
        default=None,
        ge=0,
        le=25,
        description="Minimum fit score from 0 to 25.",
    )
    max_score: int | None = Field(
        default=None,
        ge=0,
        le=25,
        description="Maximum fit score from 0 to 25.",
    )
    company: str | None = Field(
        default=None,
        description="Case-insensitive company name filter.",
    )
    source: str | None = Field(
        default=None,
        description="Case-insensitive source filter, such as LinkedIn or company careers page.",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of opportunities to return.",
    )


class UpdateOpportunityInput(BaseModel):
    """Partial updates for an existing tracked opportunity."""

    opportunity_id: uuid.UUID = Field(
        description="The ID of the opportunity to update.",
    )
    url: str | None = Field(
        default=None,
        description="Updated canonical job posting URL.",
    )
    source: str | None = Field(
        default=None,
        description="Updated source, such as LinkedIn, Indeed, or company careers page.",
    )
    title: str | None = Field(
        default=None,
        description="Updated job title or role name.",
    )
    company: str | None = Field(
        default=None,
        description="Updated company or employer name.",
    )
    location: str | None = Field(
        default=None,
        description="Updated location, remote policy, or region.",
    )
    description: str | None = Field(
        default=None,
        description="Updated job description, notes, or extracted posting summary.",
    )
    score: int | None = Field(
        default=None,
        ge=0,
        le=25,
        description="Updated total fit score from 0 to 25.",
    )
    score_reason: str | None = Field(
        default=None,
        description="Updated score explanation and sub-score rationale.",
    )
    status: OpportunityStatus | None = Field(
        default=None,
        description="Updated workflow status.",
    )
    applied: bool | None = Field(
        default=None,
        description="Whether the user has applied to this opportunity.",
    )
    raw_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Metadata to merge into existing raw_metadata by default.",
    )
    merge_raw_metadata: bool = Field(
        default=True,
        description="Merge raw_metadata with existing metadata instead of replacing it.",
    )


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_meta_content(soup: BeautifulSoup, *names: str) -> str | None:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find(
            "meta",
            attrs={"name": name},
        )
        content = tag.get("content") if tag else None
        if content:
            return _normalize_whitespace(content)
    return None


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


def extract_opportunity_from_url(input: ExtractOpportunityFromUrlInput) -> dict[str, Any]:
    """Fetch a job posting URL and return readable page content for opportunity extraction.

    Use this before creating or enriching an opportunity when the user provides a job URL and
    asks you to inspect the posting.
    """
    try:
        response = httpx.get(
            input.url,
            follow_redirects=True,
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                ),
            },
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return {
            "ok": False,
            "url": input.url,
            "error": str(exc),
        }

    soup = BeautifulSoup(response.text, "html.parser")
    for element in soup(["script", "style", "noscript", "svg", "iframe"]):
        element.decompose()

    title = _normalize_whitespace(soup.title.string) if soup.title and soup.title.string else None
    description = _extract_meta_content(
        soup,
        "description",
        "og:description",
        "twitter:description",
    )
    canonical_url = response.url
    visible_text = _normalize_whitespace(soup.get_text(" "))

    return {
        "ok": True,
        "url": str(canonical_url),
        "domain": urlparse(str(canonical_url)).netloc,
        "title": title,
        "meta_description": description,
        "text_excerpt": visible_text[:8000],
        "content_length": len(visible_text),
    }


def _opportunity_to_dict(opportunity) -> dict[str, Any]:
    return {
        "id": str(opportunity.id),
        "url": opportunity.url,
        "source": opportunity.source,
        "title": opportunity.title,
        "company": opportunity.company,
        "location": opportunity.location,
        "description": opportunity.description,
        "score": opportunity.score,
        "score_reason": opportunity.score_reason,
        "status": opportunity.status,
        "applied": opportunity.applied,
        "applied_at": opportunity.applied_at.isoformat() if opportunity.applied_at else None,
        "profile_version": opportunity.profile_version,
        "raw_metadata": opportunity.raw_metadata,
        "created_at": opportunity.created_at.isoformat(),
        "updated_at": opportunity.updated_at.isoformat(),
    }


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
            "applied": opportunity.applied,
            "status": opportunity.status,
        }


def get_opportunity(input: GetOpportunityInput) -> dict[str, Any]:
    """Return one tracked opportunity by ID before updating, scoring, or drafting materials."""
    with Session(engine) as session:
        opportunity = repo_get_opportunity(session, input.opportunity_id)
        if opportunity is None:
            return {
                "found": False,
                "id": str(input.opportunity_id),
                "message": "Opportunity not found.",
            }
        return {"found": True, "opportunity": _opportunity_to_dict(opportunity)}


def update_opportunity(input: UpdateOpportunityInput) -> dict[str, Any]:
    """Update one tracked opportunity by ID.

    Use this for edits to status, applied state, score, notes, extracted URL details,
    or other fields. By default, raw_metadata is merged with existing metadata.
    """
    with Session(engine) as session:
        opportunity = repo_get_opportunity(session, input.opportunity_id)
        if opportunity is None:
            return {
                "updated": False,
                "id": str(input.opportunity_id),
                "message": "Opportunity not found.",
            }

        data = input.model_dump(
            exclude={"opportunity_id", "merge_raw_metadata"},
            exclude_unset=True,
        )
        if input.merge_raw_metadata and "raw_metadata" in data and data["raw_metadata"] is not None:
            data["raw_metadata"] = {
                **(opportunity.raw_metadata or {}),
                **data["raw_metadata"],
            }

        updated = repo_update_opportunity(
            session,
            opportunity,
            OpportunityUpdate.model_validate(data),
        )
        return {"updated": True, "opportunity": _opportunity_to_dict(updated)}


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
                    "applied": opportunity.applied,
                    "status": opportunity.status,
                }
                for opportunity in created
            ],
        }


def list_opportunities(input: ListOpportunitiesInput) -> dict[str, Any]:
    """List or search tracked opportunities with optional filters."""
    with Session(engine) as session:
        opportunities = repo_list_opportunities(
            session,
            query=input.query,
            status=input.status,
            applied=input.applied,
            min_score=input.min_score,
            max_score=input.max_score,
            company=input.company,
            source=input.source,
            limit=input.limit,
        )
        return {
            "result_count": len(opportunities),
            "filters": input.model_dump(exclude_none=True),
            "opportunities": [
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
            ],
        }
