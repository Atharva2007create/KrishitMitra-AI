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

    @field_validator("api_version")
    @classmethod
    def validate_api_version(cls, value: str) -> str:
        if not value.startswith("v"):
            raise ValueError("API_VERSION must start with 'v'")
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
