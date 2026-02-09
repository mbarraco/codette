from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+psycopg://codette:codette@localhost:5432/codette"
    api_port: int = 8000
    log_level: str = "INFO"


settings = Settings()
