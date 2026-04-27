from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from job_search_agent.api.routes import router

app = FastAPI(title="JobSearchAgent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:13000",
        "http://127.0.0.1:13000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

