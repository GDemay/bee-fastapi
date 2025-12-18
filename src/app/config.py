"""Application configuration."""

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    PRODUCTION = "production"
    TEST = "test"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Environment = Field(default=Environment.LOCAL)
    app_debug: bool = Field(default=False)
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)

    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/user_registration"
    )
    database_pool_min_size: int = Field(default=5)
    database_pool_max_size: int = Field(default=20)

    resend_api_key: str = Field(default="")
    resend_from_email: str = Field(default="noreply@example.com")

    activation_code_expiry_seconds: int = Field(default=60)

    @property
    def is_local(self) -> bool:
        return self.app_env == Environment.LOCAL

    @property
    def is_production(self) -> bool:
        return self.app_env == Environment.PRODUCTION

    @property
    def is_test(self) -> bool:
        return self.app_env == Environment.TEST

    @property
    def asyncpg_url(self) -> str:
        url = str(self.database_url)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def raw_asyncpg_url(self) -> str:
        url = str(self.database_url)
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
