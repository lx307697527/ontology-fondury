from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://fondry:fondry@localhost:5432/fondry"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = "sk-xxx"
    llm_model: str = "gpt-4o-mini"

    chunk_size: int = 1200
    chunk_overlap: int = 150
    max_objects_per_graph: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()
