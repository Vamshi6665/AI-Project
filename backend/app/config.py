"""Central configuration. Every setting comes from environment variables (or backend/.env).

Switch the LLM provider with one variable:
    LLM_PROVIDER=mock       -> no keys needed, heuristic extraction (local dev, tests)
    LLM_PROVIDER=openai     -> OpenAI API directly (Day 1 testing)
    LLM_PROVIDER=sagemaker  -> gpt-oss-20b on your SageMaker endpoint (Day 2, the resume version)
    LLM_PROVIDER=bedrock    -> gpt-oss-20b on Amazon Bedrock (fallback if GPU quota is pending)
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- app ---
    app_name: str = "Clinical AI - PDF Extraction API"
    environment: Literal["local", "dev", "prod"] = "local"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"  # comma-separated

    # --- auth (JWT) ---
    jwt_secret: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    demo_username: str = "demo"
    demo_password: str = "demo123"

    # --- upload limits ---
    max_upload_mb: int = 10
    max_pages: int = 30
    max_chars_to_llm: int = 24000  # ~6k tokens; keeps latency and cost predictable

    # --- LLM provider ---
    llm_provider: Literal["mock", "openai", "sagemaker", "bedrock"] = "mock"
    llm_timeout_seconds: int = 120
    llm_max_tokens: int = 4096
    llm_reasoning_effort: Literal["low", "medium", "high"] = "low"

    # OpenAI (direct API)
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"

    # AWS
    aws_region: str = "us-east-1"
    sagemaker_endpoint_name: str = "clinical-ai-gptoss-20b"
    bedrock_model_id: str = "openai.gpt-oss-20b-1:0"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def model_label(self) -> str:
        return {
            "mock": "mock-heuristic",
            "openai": self.openai_model,
            "sagemaker": f"gpt-oss-20b @ SageMaker:{self.sagemaker_endpoint_name}",
            "bedrock": self.bedrock_model_id,
        }[self.llm_provider]


@lru_cache
def get_settings() -> Settings:
    return Settings()
