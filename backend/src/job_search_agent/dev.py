import uvicorn


def run_api() -> None:
    uvicorn.run(
        "job_search_agent.api.app:app",
        host="127.0.0.1",
        port=18080,
        reload=True,
    )

