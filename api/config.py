"""
API Configuration Management
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API Configuration"""

    # App settings
    app_name: str = "East-lake Knowledge Base API"
    app_version: str = "1.0.0"
    debug: bool = False

    # API Keys
    anthropic_api_key: str | None = None
    github_token: str | None = None

    # GitHub Repository
    github_owner: str = "huangtao900103"
    github_repo: str = "East-lake"

    # API Security
    api_key_header: str = "X-API-Key"
    admin_api_key: str | None = None

    # Rate limiting
    rate_limit_per_minute: int = 60

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"

    # Vector store
    vector_store_path: str = "./data/vector_store"

    # Cache
    cache_ttl: int = 3600  # seconds

    class Config:
        env_prefix = "EASTLAKE_"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings"""
    return Settings(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        github_token=os.getenv("GITHUB_TOKEN"),
        admin_api_key=os.getenv("ADMIN_API_KEY"),
    )


settings = get_settings()