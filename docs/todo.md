# Project Checklist

## Current State

- Backend scaffolded with FastAPI, SQLModel, Alembic, and Postgres.
- Backend code moved into `backend/`.
- Agent scaffolded with Deep Agents, LangSmith/LangGraph config, OpenAI model config, and optional Tavily search.
- Domain tables exist for `user_profile` and `opportunity`.
- Agent can ingest pasted resume text, create opportunities, bulk import opportunities, list opportunities, and retrieve the active profile brief.
- Opportunity scoring uses a 25-point rubric with sub-scores stored in `raw_metadata`.
- Agent Chat UI scaffolded into `ui/`.
- UI includes a first opportunities table backed by FastAPI and built with TanStack Query/Table.
- UI desktop panels are resizable, and the opportunities table shows score and applied state.

## Next Active Milestone: UI Iteration

- Run the UI against the local backend and LangGraph server.
- Improve table behavior based on real imported data.
- Add mobile/tablet layout for the opportunities workspace.
- Add event-driven refresh after agent imports or updates opportunities.
- Add row details for score reason and raw metadata.
- Add opportunity URL extraction tool:
  - Fetch a known job posting URL and extract page content into title, company, description, location, and metadata.
  - This means reading data at the URL/domain, not just interpreting the URL string.
  - Tavily can help with research, but page extraction should remain a separate capability.

## Backlog

- Docker Compose dev environment:
  - Run Postgres, backend FastAPI, LangGraph dev/server, and frontend from one Compose command.
  - Keep LangSmith external; pass `LANGSMITH_API_KEY`, `LANGSMITH_TRACING`, and project config through environment variables.
  - Add backend and UI Dockerfiles or dev-focused Compose service definitions.
  - Add health checks and service dependencies so API waits for Postgres.
  - Document a single command such as `docker compose up` for full local development.
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
  - Update status, applied state, notes, score, and metadata.
  - Delete or archive bad imports.
- Scoring reliability:
  - Keep the main agent responsible for scoring for now.
  - Add a dedicated scoring workflow only if behavior becomes inconsistent.
- Tests:
  - Repository tests.
  - API route tests.
  - Tool schema tests.
  - Bulk import and scoring tests.

