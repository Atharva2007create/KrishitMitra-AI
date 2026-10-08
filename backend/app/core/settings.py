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
    aws_s3_bucket_images: str = ""
    gemini_api_key: str = ""
    gemini_secret_arn: str = ""
    embedding_model: str = "gemini-embedding-2"
    embedding_dimension: int = 768
    gemini_model: str = "gemini-3.8-flash"
    gemini_fallback_model: str = "gemini-3.7-flash"
    gemini_temperature: float = 0.2
    gemini_max_output_tokens: int = 2048
    ai_request_timeout: float = 45.0
    ai_max_retries: int = 3
    faq_default_language: str = "en"
    faq_max_per_category: int = 10
    assistance_max_question_length: int = 2000
    attachment_max_size_mb: int = 10
    presigned_upload_ttl_seconds: int = 900
    government_http_timeout_seconds: float = 12.0
    government_http_max_retries: int = 2
    government_http_max_response_bytes: int = 5_000_000
    imd_api_base_url: str = "https://api.imd.gov.in/api/v1"
    imd_api_auth_header: str = "Authorization"
    imd_api_auth_value: str = ""
    data_gov_api_base_url: str = "https://api.data.gov.in/resource"
    data_gov_api_key: str = ""
    agmarknet_resource_id: str = "9ef84268-d588-465a-a308-a864a43d0070"
    live_data_cache_seconds: int = 900
    weather_max_age_seconds: int = 21_600
    image_analysis_model: str = "gemini-3.8-flash"
    image_analysis_lambda_name: str = "krishimitra-dev-image-analysis"
    image_retention_days: int = 30
    assistance_rate_limit_per_minute: int = 10
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

    @field_validator(
        "government_http_max_retries",
        "government_http_max_response_bytes",
        "live_data_cache_seconds",
        "weather_max_age_seconds",
        "image_retention_days",
    )
    @classmethod
    def validate_positive_phase5_value(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Phase 5 limits must be positive")
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
