import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "PM-CDSS (Personalized Medicine Clinical Decision Support System)"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    INSTITUTION_NAME: str = "Levy Mwanawasa Teaching Hospital, Zambia"

    # Environment
    ENVIRONMENT: str = "development"

    # Database Settings
    POSTGRES_USER: str = "pm_user"
    POSTGRES_PASSWORD: str = "pm_password"
    POSTGRES_DB: str = "pm_cdss"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://pm_user:pm_password@localhost:5432/pm_cdss"

    # JWT Settings
    JWT_SECRET_KEY: str = "penmed-cdss-super-secure-production-ready-jwt-key-cavendish-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Settings
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if not v.strip():
                return ["*"]
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
