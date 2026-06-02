from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_name: str = "EduSpark AI"
    environment: Literal["development", "test", "staging", "production"] = Field(
        default="development",
        validation_alias="ENVIRONMENT",
    )

    database_url: str = Field(..., validation_alias="DATABASE_URL")
    redis_url: str = Field(..., validation_alias="REDIS_URL")

    jwt_secret: SecretStr = Field(..., validation_alias="JWT_SECRET")
    access_token_expires_minutes: int = Field(
        default=30,
        validation_alias="JWT_EXPIRES_MIN",
        ge=5,
        le=60 * 24,
    )
    refresh_token_expires_minutes: int = Field(
        default=60 * 24 * 30,
        validation_alias="REFRESH_EXPIRES_MIN",
        ge=15,
        le=60 * 24 * 365,
    )
    access_token_algorithm: str = Field(default="HS256", validation_alias="ACCESS_TOKEN_ALG")

    allowed_origins: str = Field(default="*", validation_alias="ALLOWED_ORIGINS")

    openai_api_key: SecretStr | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    embedding_dim: int = Field(default=1536, validation_alias="EMBEDDING_DIM", gt=0)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
    )

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: object) -> str:
        if value is None:
            return "development"
        return str(value).strip().lower()

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def normalize_allowed_origins(cls, value: object) -> str:
        if value is None or value == "":
            return "*"
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, list):
            return ",".join(str(origin).strip() for origin in value if str(origin).strip())
        raise TypeError("ALLOWED_ORIGINS must be a comma-separated string or list")

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        secret = self.jwt_secret.get_secret_value()
        if self.environment == "production":
            if len(secret) < 32 or secret == "dev-secret-change-me":
                raise ValueError("JWT_SECRET must be replaced with a strong secret in production")
            if "*" in self.allowed_origins_list:
                raise ValueError("ALLOWED_ORIGINS must be explicit in production")
        return self

    @property
    def jwt_secret_value(self) -> str:
        return self.jwt_secret.get_secret_value()

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()] or ["*"]


settings = Settings()
