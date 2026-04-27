from fastapi import FastAPI

from job_search_agent.api.routes import router

app = FastAPI(title="JobSearchAgent API")
app.include_router(router)

