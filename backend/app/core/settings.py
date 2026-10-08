from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "KrishiMitra AI"
    api_version: str = "v1"
    database_url: str = "postgresql+asyncpg://krishimitra:krishimitra@localhost:5432/krishimitra"
    cors_allowed_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    aws_region: str = "ap-south-1"
    aws_cognito_user_pool_id: str = ""
    aws_cognito_client_id: str = ""
    aws_cognito_admin_group: str = "administrators"
    jwt_jwks_cache_seconds: int = 3600
    aws_s3_bucket_documents: str = ""
    gemini_api_key: str = ""
    gemini_secret_arn: str = ""
    embedding_model: str = "gemini-embedding-2"
    embedding_dimension: int = 768
    rag_default_top_k: int = 5
    rag_max_top_k: int = 20
    rag_min_relevance_threshold: float = 0.20
    rag_vector_weight: float = 0.65
    rag_lexical_weight: float = 0.35

    @field_validator("embedding_dimension")
    @classmethod
    def validate_embedding_dimension(cls, value: int) -> int:
        if value != 768:
            raise ValueError("Phase 3 schema is fixed at EMBEDDING_DIMENSION=768")
        return value

    @field_validator("rag_default_top_k", "rag_max_top_k")
    @classmethod
    def validate_positive_limit(cls, value: int) -> int:
        if value < 1:
            raise ValueError("RAG result limits must be positive")
        return value

    @field_validator("api_version")
    @classmethod
    def validate_api_version(cls, value: str) -> str:
        if not value.startswith("v"):
            raise ValueError("API_VERSION must start with 'v'")
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def cognito_issuer(self) -> str:
        return (
            f"https://cognito-idp.{self.aws_region}.amazonaws.com/{self.aws_cognito_user_pool_id}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
