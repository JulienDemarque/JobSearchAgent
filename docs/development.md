# Development Guide

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
```

UI:

```bash
cd ui
pnpm --filter web lint
pnpm --filter web build
```

