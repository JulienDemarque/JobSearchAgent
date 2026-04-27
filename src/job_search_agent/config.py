from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://job_search_agent:job_search_agent@localhost:55432/job_search_agent"
    )
    openai_api_key: str | None = None
    openai_model: str = "openai:gpt-5.4"
    langsmith_api_key: str | None = None
    langsmith_tracing: bool = True
    langsmith_project: str = "job-search-agent"
    tavily_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

