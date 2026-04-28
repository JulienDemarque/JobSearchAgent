# Project Checklist

## Current State

- Backend scaffolded with FastAPI, SQLModel, Alembic, and Postgres.
- Backend code moved into `backend/`.
- Full dev stack can run through Docker Compose for Postgres, migrations, FastAPI, LangGraph, and UI.
- Agent scaffolded with Deep Agents, LangSmith/LangGraph config, OpenAI model config, and optional Tavily search.
- Domain tables exist for `user_profile` and `opportunity`.
- Opportunity workflow statuses include `new`, `interested`, `applied`, `interviewing`, `interviewed`, `offer`, `rejected`, and `archived`.
- Agent can ingest pasted resume text, create opportunities, bulk import opportunities, search/list/update opportunities, and retrieve the active profile brief.
- Agent can fetch a job posting URL, extract readable page text and metadata, then use that output to create or enrich opportunities.
- Opportunity scoring uses a 25-point rubric with sub-scores stored in `raw_metadata`.
- Agent Chat UI scaffolded into `ui/`.
- UI includes a first opportunities table backed by FastAPI and built with TanStack Query/Table.
- UI desktop panels are resizable, and the opportunities table shows score and applied state.
- Opportunities table supports search, status/applied filtering, minimum score filtering, sorting, compact dates, event-driven refresh after chat runs, modal row details, and quick status updates.
- Focused backend repository tests cover opportunity create, search, update, and applied timestamp behavior.

## Next Active Milestone: UI Iteration

- Improve table behavior based on real imported data.
- Test URL extraction against real job boards and tune blocked-page/error behavior.

## Backlog

- LangSmith Studio local connectivity:
  - Studio currently fails to connect reliably to the local LangGraph server.
  - Lower priority now that the app has a local UI.
  - Revisit tunnel/localhost/CORS/auth behavior when Studio is needed again.
- Profile extraction and review flow:
  - Extract `profile_brief` and `profile_data` from `user_profile.resume_text`.
  - Store target roles, strong skills, constraints, deal breakers, and other structured facts in `profile_data`.
  - Keep explicit user preferences in `preferences`.
  - Add a user approval flow before setting `reviewed=true`.
- Status/update tools:
  - Delete or archive bad imports.
- Scoring reliability:
  - Keep the main agent responsible for scoring for now.
  - Add a dedicated scoring workflow only if behavior becomes inconsistent.
- Tests:
  - API route tests.
  - Tool schema tests.
  - Bulk import and scoring tests.

