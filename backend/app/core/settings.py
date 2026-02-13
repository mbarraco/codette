from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    storage_bucket: str
    api_port: int = 8000
    log_level: str = "INFO"

    gcp_project: str | None = None
    gcp_location: str = "us-central1"
    runner_job_name: str = "codette-runner"
    grader_job_name: str = "codette-grader"


class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.test", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str
    storage_bucket: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
