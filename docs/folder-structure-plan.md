# Folder Structure Plan

## Goal

Keep the repository as a small monorepo with clear ownership boundaries:

- `backend/` for Python API, agent, migrations, and backend package management.
- `ui/` for the customized Agent Chat UI / Next.js app.
- `docs/` for product, architecture, and project planning.
- root for cross-project orchestration and repo-level docs.

## Proposed Structure

```text
JobSearchAgent/
  README.md
  docker-compose.yml
  .gitignore
  .cursor/
    rules/
  docs/
    architecture-plan.md
    folder-structure-plan.md
    todo.md
    user-stories.md
  backend/
    pyproject.toml
    uv.lock
    .env.example
    alembic.ini
    langgraph.json
    alembic/
      env.py
      versions/
    src/
      job_search_agent/
        agent/
        api/
        db/
        config.py
        dev.py
  ui/
    package.json
    pnpm-lock.yaml
    next.config.*
    src/
```

## Root Responsibilities

- Keep `README.md` as the project entrypoint.
- Keep `docker-compose.yml` at the root for shared local infrastructure such as Postgres.
- Keep repo-wide Cursor rules in `.cursor/rules/`.
- Keep product docs in `docs/`.

## Backend Responsibilities

- Own Python dependencies, lockfile, package source, migrations, and LangGraph config.
- Run backend commands from `backend/`:
  - `uv sync --extra dev`
  - `uv run alembic upgrade head`
  - `uv run api`
  - `uv run langgraph dev --port 12024`
- Keep backend `.env` in `backend/.env`, ignored by git.

## UI Responsibilities

- Start from Agent Chat UI.
- Connect chat to the LangGraph dev server.
- Render the opportunities table from FastAPI.
- Use `pnpm` unless the scaffold strongly prefers another package manager.

## Migration Status

Completed:

- Created `backend/`.
- Moved Python/backend files into `backend/`.
- Kept `docker-compose.yml`, `docs/`, `README.md`, and `.cursor/` at the root.
- Verified backend dependency sync, lint, compile, Alembic, API import, and graph import from `backend/`.

Remaining:

- Scaffold `ui/` after the backend move is verified.

## Migration Steps Reference

1. Create `backend/`.
2. Move Python/backend files into `backend/`:
   - `pyproject.toml`
   - `uv.lock`
   - `.env.example`
   - `.env`
   - `alembic.ini`
   - `langgraph.json`
   - `alembic/`
   - `src/`
3. Update README commands to run from `backend/`.
4. Update `docker-compose.yml` if any paths need to point into `backend/`.
5. Run backend checks from `backend/`.
6. Scaffold `ui/` after the backend move is verified.

## Notes

- Moving `.env` is a local-only operation; it remains ignored.
- Keeping `docker-compose.yml` at root avoids duplicating infrastructure when the UI is added.
- The backend can later be containerized without changing the source layout.

