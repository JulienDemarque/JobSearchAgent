# JobSearchAgent Architecture Plan

## Product Goal

Build a personal AI agent that tracks job opportunities, searches saved opportunities, evaluates fit, and helps move each opportunity through the application process.

The codebase should stay close to LangChain, Deep Agents, LangGraph runtime, and LangSmith conventions so it can serve as a clear reference implementation.

## Current LangChain/LangSmith Notes

- LangGraph is the lower-level orchestration runtime for long-running, stateful agents. It provides durable execution, streaming, memory, human-in-the-loop support, and LangSmith integration.
- LangChain agents and Deep Agents can sit above LangGraph. We do not need to hand-author a graph unless the product needs explicit workflow control.
- Deep Agents is a strong fit to evaluate because it adds planning, task decomposition, filesystem/context management, subagents, long-term memory, permissions, and human-in-the-loop behavior on top of LangChain/LangGraph primitives.
- LangSmith should be used for tracing, debugging, evaluation datasets, experiments, online evaluators, monitoring, and deployment.
- LangSmith Deployment runs Agent Server. Agent Server exposes assistants, threads, runs, streaming, persistence, and task queue APIs.
- Agent Server persists core resources, checkpoints, and long-term memory in Postgres by default. In managed deployments, do not configure graph checkpointers or stores manually in application graph code.
- FastAPI can still be used through LangSmith custom routes by registering an app in `langgraph.json` under `http.app`.
- LangSmith Studio is the developer UI for local and deployed agents. It is useful for graph inspection, debugging, state inspection, and testing.
- For an end-user chat frontend, use LangChain Agent Chat UI or a small custom frontend. Agent Chat UI is a Next.js app that connects to local or deployed LangGraph agents and supports tool-call rendering.

Primary docs:

- LangGraph overview: https://docs.langchain.com/oss/python/langgraph/overview
- Local LangGraph server: https://docs.langchain.com/oss/python/langgraph/local-server
- LangSmith Deployment: https://docs.langchain.com/langsmith/deployment
- Agent Server: https://docs.langchain.com/langsmith/agent-server
- Custom FastAPI routes: https://docs.langchain.com/langsmith/custom-routes
- LangSmith evaluation: https://docs.langchain.com/langsmith/evaluation
- LangSmith observability: https://docs.langchain.com/langsmith/observability
- Agent Chat UI: https://docs.langchain.com/oss/python/langchain/ui
- Deep Agents overview: https://docs.langchain.com/oss/python/deepagents/overview
- LangSmith pricing: https://www.langchain.com/pricing

## Proposed Architecture

Use a Python monorepo-style app with these parts:

- `agent`: Deep Agents or LangChain agent harness, prompts, tools, scoring workflow, search/retrieval workflow, and application-assistance workflow. Use explicit LangGraph graphs only where control flow needs them.
- `api`: FastAPI custom routes for app-specific APIs not covered by Agent Server, such as CRUD routes for opportunities and import endpoints.
- `db`: Postgres models, repositories, migrations, and seed data.
- `evals`: LangSmith evaluation datasets, evaluators, and regression experiments.
- `ui`: customized Agent Chat UI. Keep chat as the command surface and add an opportunities table/detail workspace backed by app APIs.

## Data Model V1

Start with `opportunity`:

- `id`
- `url`
- `source`
- `title`
- `company`
- `location`
- `description`
- `score`
- `score_reason`
- `status`
- `applied`
- `applied_at`
- `created_at`
- `updated_at`
- `raw_metadata`

Likely follow-up tables:

- `company`
- `contact`
- `application_event`
- `resume_profile`
- `opportunity_note`
- `search_query`

Add a single early profile table before scoring:

- `user_profile`

For MVP, keep resume, extracted profile facts, and job preferences in `user_profile`. Scoring should use a compact reviewed profile brief in model context plus the full resume text only when needed.

## Agent Capabilities V1

- Add opportunity from URL or pasted description.
- Extract structured job data.
- Score job fit against a profile/resume.
- Search and filter opportunities by company, status, score, keywords, and applied state.
- Summarize why an opportunity is or is not worth applying to.
- Mark opportunity status changes, including applied.
- Generate application prep notes, cover-letter bullets, and interview research.
- Ingest a resume and job preferences so scoring and generated materials are grounded in the user's actual background.

## User Stories V1

- As a user, I can paste one or more job-offer links into chat and ask the agent to add them to my pipeline.
- As a user, I can paste a raw job description into chat and have the agent create an opportunity even when no link is available.
- As a user, I can see all tracked opportunities in a table with company, title, link, score, status, applied state, and updated time.
- As a user, I can ask the agent to enrich incomplete rows by extracting title, company, location, description, seniority, compensation, and source metadata.
- As a user, I can ask why a job has its score and see a concise fit explanation tied to my profile/resume.
- As a user, I can tell the agent to mark opportunities as interested, rejected, applied, interviewing, offer, or archived.
- As a user, I can ask the agent to search/filter the table, such as "show unapplied backend roles above 80".
- As a user, I can open an opportunity detail view with extracted job facts, notes, scoring rationale, application status, and generated application materials.
- As a user, I can ask the agent to draft cover-letter bullets or a full cover letter for a selected opportunity.
- As a user, I can approve important mutations before the agent changes application status, sends outreach, or overwrites generated materials.

## Tooling Decision

Start with direct LangChain tools exposed to the chosen agent harness because the first tool users are internal agent steps. This keeps the implementation simple and traceable.

Default candidate: Deep Agents. It matches the product shape well because job search work involves multi-step planning, research notes, file/profile context, possible subagents for sourcing and scoring, memory across conversations, and approval gates before mutating application status.

Fallback candidate: LangChain `create_agent` if the first version is mostly a straightforward chat-plus-tools loop.

Use hand-written LangGraph only for parts that need explicit control flow, branching, interrupts, or durable workflow semantics beyond what Deep Agents gives us cleanly.

Add MCP later if the opportunity database, search, browser/importer, or resume/profile tools need to be shared with other agents, IDEs, or external clients. LangSmith Deployment supports MCP, so this can evolve without changing the core product model.

## Resume And Preferences Context

This should be designed before opportunity scoring. The agent needs stable knowledge of the user's resume and preferences, but the full resume should not be blindly pasted into every prompt forever.

Recommended approach:

- Store the canonical resume text in `user_profile.resume_text`.
- Store structured profile data in `user_profile.profile_data`.
- Store preferences in `user_profile.preferences`.
- Maintain a compact "profile brief" that is short enough to include in most agent/scoring prompts.
- Add tools for retrieving the active profile brief, full resume text, and preferences.
- Use the profile brief for first-pass scoring, then retrieve the full resume text for score explanations, cover letters, and interview prep when needed.
- Version the profile so scores can later record which profile version produced them.

OpenAI is the first model provider. The API key should live in `.env` and never be committed.

## Resume Ingestion

MVP should support pasted plain-text resumes in chat. This avoids file upload, object storage, PDF parsing, and OCR while still proving the core matching workflow.

PDF upload should be a follow-up feature once the profile/scoring loop works.

MVP pasted-text pipeline:

1. User pastes resume text into chat and asks the agent to save it as their active resume.
2. Agent calls a tool such as `ingest_resume_text(text)` to store the canonical text.
3. Normalize text lightly: preserve section headings, normalize whitespace, and remove obvious copy/paste artifacts.
4. Ask the model to produce structured profile data from the resume text: roles, seniority, skills, industries, projects, education, languages, location, links, notable achievements, and constraints.
5. Generate a compact profile brief for frequent prompt context. This should be concise, editable, and regenerated whenever the resume or preferences change.
6. Show the extracted profile brief and key structured fields to the user for review before using them for scoring.
7. Mark a reviewed profile version as active. Opportunity scores should reference the active profile version used to produce them.

Later PDF pipeline:

1. Upload the original resume file through the UI or a FastAPI route.
2. Store file metadata and a durable copy of the original PDF. For local development this can be filesystem-backed; for deployment use object storage or a Postgres large-object alternative only if the platform makes that simpler.
3. Extract text from the PDF with a deterministic parser first. Prefer a Python library such as `pypdf` or `pdfplumber`; consider OCR only for scanned PDFs.
4. Normalize extracted text: remove repeated headers/footers, preserve section headings, normalize whitespace, and keep page numbers or offsets for traceability.
5. Optionally split the resume into semantic sections if PDF extraction quality makes that useful.
6. Ask the model to produce structured profile data from the extracted text: roles, seniority, skills, industries, projects, education, languages, location, links, notable achievements, and constraints.
7. Store the extracted text and structured profile data on `user_profile`, unless PDF ingestion grows enough to justify separate resume tables.
8. Generate a compact profile brief for frequent prompt context. This should be concise, editable, and regenerated whenever the resume or preferences change.
9. Show the extracted profile brief and key structured fields to the user for review before using them for scoring.
10. Mark a reviewed profile version as active. Opportunity scores should reference the active profile version used to produce them.

Suggested ingestion states for `user_profile.ingestion_status`:

- `text_received`
- `text_extracted`
- `profile_extracted`
- `needs_review`
- `active`
- `failed`

Minimum tables/fields:

- `user_profile`: resume text, profile brief, structured profile JSON, preferences JSON, version, reviewed flag, active flag, timestamps.

Agent/tool behavior:

- `ingest_resume_text(text)` creates or updates the active `user_profile` record for MVP.
- `ingest_resume_file(file)` can be added later for PDF upload.
- `extract_resume_profile(user_profile_id)` extracts structured profile data and a profile brief.
- `get_active_profile_brief()` returns the compact profile context used in most scoring prompts.
- `get_full_resume_text()` retrieves the full resume only for detailed explanations, cover letters, and interview prep.
- `update_job_preferences(...)` lets the user refine matching criteria through chat.

Important constraints:

- Do not include the whole resume in every prompt by default. Use the profile brief first.
- Keep the original pasted or extracted text available for auditability and regeneration.
- Treat model-extracted profile fields as draft until the user reviews them.
- Version profile changes so old scores and cover letters can be traced back to the context that produced them.

## Frontend Decision

Use LangSmith Studio for development and debugging, but plan for a product UI early because the opportunity table is central to the workflow.

Start from Agent Chat UI rather than building from scratch. It is a Next.js app for interacting with LangGraph-compatible agents, can be run locally or deployed, and supports custom rendering patterns such as a side-panel artifact area.

Recommended UI shape:

- Left/main area: chat with the job-search agent.
- Right/workspace area: opportunities table, selected opportunity detail, generated cover letter, or review/approval panel.
- Data path: table reads from FastAPI custom routes backed by Postgres; chat-triggered mutations happen through agent tools that write to the same repositories.
- Sync path: after agent tool calls mutate opportunities, refresh or stream updates into the table.

For production, use the Agent Chat UI API passthrough pattern so the browser does not need a LangSmith API key. Keep `LANGSMITH_API_KEY` server-side and route browser traffic through the Next.js API proxy.

## Implementation Milestones

1. Bootstrap a Python agent project with LangSmith tracing enabled, starting with Deep Agents unless a simpler LangChain agent is enough.
2. Add Postgres, SQLModel, Alembic, and the initial `user_profile` plus `opportunity` models.
3. Add pasted-text resume ingestion and preference capture so the agent has a reviewed profile brief before scoring jobs.
4. Add repository functions and FastAPI custom routes for profile and opportunity CRUD.
5. Add direct tools for create/update/search/list opportunities and retrieve profile context.
6. Add job extraction and scoring agent steps with typed tool inputs and outputs.
7. Add LangSmith eval dataset for scoring quality and extraction correctness.
8. Run locally with the LangGraph/LangSmith local server path supported by the chosen harness and test in LangSmith Studio.
9. Fork or scaffold Agent Chat UI and add the opportunities table workspace.
10. Connect Agent Chat UI for manual end-to-end testing.
11. Deploy through LangSmith Deployment with API passthrough for production UI auth.
12. Decide whether MCP is useful after the direct tools stabilize.

## Open Decisions

- Whether opportunity ingestion should start from pasted text, URL scraping, browser extension, or all three.
- Whether the first UI should be Agent Chat UI only or a small dashboard for opportunity tracking.
