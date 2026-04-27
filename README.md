# JobSearchAgent

Personal AI job-search agent built around LangChain, LangGraph, LangSmith, FastAPI, and Postgres.

## Local Setup

Start the backend:

```bash
docker compose up -d postgres
cd backend
uv sync --extra dev
cp .env.example .env
uv run alembic upgrade head
uv run api
```

Start the agent server:

```bash
uv run langgraph dev --port 12024
```

Start the UI:

```bash
cd ui
nvm use
corepack enable
cp .env.example .env.local
pnpm dev --filter=web
```

Open `http://localhost:13000`.

More details: [Development guide](docs/development.md).

Current planning docs:

- [Architecture plan](docs/architecture-plan.md)
- [Development guide](docs/development.md)
- [Folder structure plan](docs/folder-structure-plan.md)
- [User stories](docs/user-stories.md)
- [Project checklist](docs/todo.md)

