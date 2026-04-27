import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from job_search_agent.api.schemas import (
    OpportunityBulkCreate,
    OpportunityCreate,
    OpportunityRead,
    OpportunityUpdate,
    UserProfileCreate,
    UserProfileRead,
    UserProfileUpdate,
)
from job_search_agent.db.repositories import (
    create_opportunities,
    create_opportunity,
    create_user_profile,
    get_active_user_profile,
    get_opportunity,
    list_opportunities,
    update_opportunity,
    update_user_profile,
)
from job_search_agent.db.session import get_session

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/profiles", response_model=UserProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: UserProfileCreate,
    session: SessionDep,
):
    return create_user_profile(
        session,
        resume_text=payload.resume_text,
        preferences=payload.preferences,
    )


@router.get("/profiles/active", response_model=UserProfileRead)
def read_active_profile(session: SessionDep):
    profile = get_active_user_profile(session)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active profile found")
    return profile


@router.patch("/profiles/active", response_model=UserProfileRead)
def patch_active_profile(
    payload: UserProfileUpdate,
    session: SessionDep,
):
    profile = get_active_user_profile(session)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active profile found")
    return update_user_profile(session, profile, payload)


@router.post("/opportunities", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def create_opportunity_route(
    payload: OpportunityCreate,
    session: SessionDep,
):
    return create_opportunity(session, payload)


@router.post(
    "/opportunities/bulk",
    response_model=list[OpportunityRead],
    status_code=status.HTTP_201_CREATED,
)
def create_opportunities_route(
    payload: OpportunityBulkCreate,
    session: SessionDep,
):
    return create_opportunities(session, payload.opportunities)


@router.get("/opportunities", response_model=list[OpportunityRead])
def list_opportunities_route(session: SessionDep):
    return list_opportunities(session)


@router.patch("/opportunities/{opportunity_id}", response_model=OpportunityRead)
def patch_opportunity_route(
    opportunity_id: uuid.UUID,
    payload: OpportunityUpdate,
    session: SessionDep,
):
    opportunity = get_opportunity(session, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    return update_opportunity(session, opportunity, payload)

