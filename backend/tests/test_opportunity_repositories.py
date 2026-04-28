import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from job_search_agent.api.schemas import OpportunityCreate, OpportunityUpdate
from job_search_agent.db.models import Opportunity, OpportunityStatus
from job_search_agent.db.repositories import (
    create_opportunity,
    list_opportunities,
    update_opportunity,
)
from job_search_agent.db.session import engine


def _database_available() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


pytestmark = pytest.mark.skipif(
    not _database_available(),
    reason="Postgres is not available. Run `docker compose up -d postgres` first.",
)


@pytest.fixture
def session():
    with Session(engine) as session:
        yield session


@pytest.fixture
def created_opportunity_ids(session: Session):
    ids: list[uuid.UUID] = []
    yield ids
    for opportunity_id in ids:
        opportunity = session.get(Opportunity, opportunity_id)
        if opportunity is not None:
            session.delete(opportunity)
    session.commit()


def test_create_and_search_opportunity(session: Session, created_opportunity_ids: list[uuid.UUID]):
    token = f"pytest-{uuid.uuid4()}"
    opportunity = create_opportunity(
        session,
        OpportunityCreate(
            title=f"Senior Agent Engineer {token}",
            company=f"Acme {token}",
            location="Remote",
            description="Build useful job-search automation.",
            score=19,
            raw_metadata={"test_token": token},
        ),
    )
    created_opportunity_ids.append(opportunity.id)

    results = list_opportunities(
        session,
        query=token,
        status=OpportunityStatus.new,
        applied=False,
        min_score=15,
        limit=10,
    )

    assert [result.id for result in results] == [opportunity.id]


def test_update_opportunity_status_and_applied_state(
    session: Session,
    created_opportunity_ids: list[uuid.UUID],
):
    token = f"pytest-{uuid.uuid4()}"
    opportunity = create_opportunity(
        session,
        OpportunityCreate(
            title=f"Backend Engineer {token}",
            company="Example Co",
            score=12,
        ),
    )
    created_opportunity_ids.append(opportunity.id)

    applied = update_opportunity(
        session,
        opportunity,
        OpportunityUpdate(status=OpportunityStatus.applied, applied=True),
    )

    assert applied.status == OpportunityStatus.applied
    assert applied.applied is True
    assert applied.applied_at is not None

    interviewed = update_opportunity(
        session,
        applied,
        OpportunityUpdate(status=OpportunityStatus.interviewed, applied=False),
    )

    assert interviewed.status == OpportunityStatus.interviewed
    assert interviewed.applied is False
    assert interviewed.applied_at is None
