from __future__ import annotations

from pydantic import BaseSettings, Field


class GatewaySettings(BaseSettings):
    """Configuration for the memori-gateway service."""

    memori_db_dsn: str = Field(..., env="MEMORI_DB_DSN")
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    gateway_api_key: str = Field(..., env="GATEWAY_API_KEY")
    memori_default_model: str = Field("gpt-4o-mini", env="MEMORI_DEFAULT_MODEL")
    memori_auto_ingest: bool = Field(True, env="MEMORI_AUTO_INGEST")
    memori_conscious_ingest: bool = Field(False, env="MEMORI_CONSCIOUS_INGEST")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = GatewaySettings()
