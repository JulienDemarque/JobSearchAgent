# Development Guide

## Full Docker Compose Stack

For day-to-day local use, start everything from the repo root:

```bash
cp backend/.env.example backend/.env
docker compose up
```

This starts:

- Postgres on `localhost:55432`
- FastAPI on `http://localhost:18080`
- LangGraph dev server on `http://localhost:12024`
- UI on `http://localhost:13000`

Compose runs Alembic migrations before starting the API and LangGraph services.
LangSmith stays external; set `LANGSMITH_API_KEY`, `LANGSMITH_TRACING`,
`LANGSMITH_PROJECT`, `OPENAI_API_KEY`, and `TAVILY_API_KEY` in `backend/.env`
when you need them.

The Compose LangGraph service uses `backend/langgraph.docker.json` so container
environment variables take precedence over the local `backend/.env` database URL.

To stop the stack:

```bash
docker compose down
```

If one of the default ports is already in use, override the host port:

```bash
UI_PORT=13001 docker compose up
```

## Backend

Run shared infrastructure from the repo root:

```bash
docker compose up -d postgres
```

Run the backend from `backend/`:

```bash
cd backend
uv sync --extra dev
cp .env.example .env
uv run alembic upgrade head
uv run api
```

The API runs at `http://localhost:18080`.

The default OpenAI model is configured through `OPENAI_MODEL` in `backend/.env`.
Set `TAVILY_API_KEY` in `backend/.env` to enable Tavily search.

## Agent Server

Run the local LangGraph server from `backend/`:

```bash
cd backend
uv run langgraph dev --port 12024
```

The UI connects to this server at `http://localhost:12024` with assistant ID `agent`.

## UI

Run the UI from `ui/`:

```bash
cd ui
nvm use
corepack enable
cp .env.example .env.local
pnpm dev --filter=web
```

The UI runs at `http://localhost:13000`.

The UI expects:

- `NEXT_PUBLIC_API_URL=http://localhost:12024`
- `NEXT_PUBLIC_ASSISTANT_ID=agent`
- `NEXT_PUBLIC_BACKEND_API_URL=http://localhost:18080`

## Ports

- Postgres: `localhost:55432`
- FastAPI: `http://localhost:18080`
- LangGraph dev server: `http://localhost:12024`
- UI: `http://localhost:13000`

## Checks

Backend:

```bash
cd backend
uv run ruff check .
uv run python -m compileall src alembic
uv run pytest
```

UI:

```bash
cd ui
pnpm --filter web lint
pnpm --filter web build
```

