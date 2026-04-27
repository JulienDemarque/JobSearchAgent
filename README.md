# JobSearchAgent

Personal AI job-search agent built around LangChain, LangGraph, LangSmith, FastAPI, and Postgres.

## Local Setup

```bash
uv sync --extra dev
cp .env.example .env
docker compose up -d postgres
uv run alembic upgrade head
uv run api
```

The API will be available at `http://localhost:18080`.

The default OpenAI model is configured through `OPENAI_MODEL` in `.env`.
This project currently defaults to `openai:gpt-5.4` for stronger long-context parsing and tool use.
Set `TAVILY_API_KEY` in `.env` to enable the LangChain Tavily web search tool.

If running Uvicorn directly, pass the port explicitly:

```bash
uv run uvicorn job_search_agent.api.app:app --reload --port 18080
```

For LangGraph/LangSmith local agent development, use the `agent` graph in `langgraph.json`:

```bash
uv run langgraph dev --port 12024
```

Default local ports:

- Postgres: `localhost:55432`
- FastAPI: `http://localhost:18080`
- LangGraph dev server: `http://localhost:12024`

Current planning docs:

- [Architecture plan](docs/architecture-plan.md)
- [User stories](docs/user-stories.md)

