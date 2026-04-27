import uuid
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session, select

from job_search_agent.api.schemas import OpportunityCreate, OpportunityUpdate, UserProfileUpdate
from job_search_agent.db.models import Opportunity, UserProfile


def touch(model: Opportunity | UserProfile) -> None:
    model.updated_at = datetime.now(UTC)


def create_user_profile(
    session: Session,
    *,
    resume_text: str,
    preferences: dict[str, Any] | None = None,
) -> UserProfile:
    profile = UserProfile(resume_text=resume_text, preferences=preferences or {})
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def get_active_user_profile(session: Session) -> UserProfile | None:
    statement = (
        select(UserProfile)
        .where(UserProfile.active.is_(True))
        .order_by(UserProfile.updated_at.desc())
    )
    return session.exec(statement).first()


def update_user_profile(
    session: Session,
    profile: UserProfile,
    update: UserProfileUpdate,
) -> UserProfile:
    data = update.model_dump(exclude_unset=True)
    if data:
        for key, value in data.items():
            setattr(profile, key, value)
        profile.version += 1
        touch(profile)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


def create_opportunity(session: Session, opportunity: OpportunityCreate) -> Opportunity:
    model = Opportunity(**opportunity.model_dump())
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def create_opportunities(
    session: Session,
    opportunities: list[OpportunityCreate],
) -> list[Opportunity]:
    models = [Opportunity(**opportunity.model_dump()) for opportunity in opportunities]
    session.add_all(models)
    session.commit()
    for model in models:
        session.refresh(model)
    return models


def list_opportunities(session: Session) -> list[Opportunity]:
    statement = select(Opportunity).order_by(Opportunity.updated_at.desc())
    return list(session.exec(statement).all())


def get_opportunity(session: Session, opportunity_id: uuid.UUID) -> Opportunity | None:
    return session.get(Opportunity, opportunity_id)


def update_opportunity(
    session: Session,
    opportunity: Opportunity,
    update: OpportunityUpdate,
) -> Opportunity:
    data = update.model_dump(exclude_unset=True)
    if data:
        for key, value in data.items():
            setattr(opportunity, key, value)
        if "applied" in data and data["applied"] and opportunity.applied_at is None:
            opportunity.applied_at = datetime.now(UTC)
        touch(opportunity)
        session.add(opportunity)
        session.commit()
        session.refresh(opportunity)
    return opportunity

