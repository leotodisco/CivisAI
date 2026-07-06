from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional
from functools import lru_cache
from enum import Enum


BASE_DIR = Path(__file__).resolve().parents[3]
ASSETS_DIR = BASE_DIR / "assets"


class LLM_MODE(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"


class Settings(BaseSettings):
    frontend_url: str = Field(default="http://localhost:5173")
    db_url: str = Field(default="")
    redis_db_url: str = Field(default="redis")

    redis_db_pwd: str = Field(default="")
    redis_db_user: str = Field(default="")
    redis_db_port: str = Field(default="")

    assets_folder_path: Path = ASSETS_DIR
    documents_raw_name: str = Field(default="raw_documents.json")
    documents_chunked_name: str = Field(default="processed_documents.json")

    llm_mode: LLM_MODE = Field(default=LLM_MODE.OLLAMA)
    ollama_url: Optional[str] = Field(default="http://ollama:11434")
    openai_api_key: Optional[str] = Field(default=None)
    llm_name: str = Field(default="")
    openai_api_key: Optional[str] = Field(default="")
    embeddings_model_name: str = Field(
        default="intfloat/multilingual-e5-small")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings():
    return Settings()
