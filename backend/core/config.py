import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator, field_validator

INSECURE_DEFAULT_SECRETS = {
    "reserve-ai-super-secure-production-ready-jwt-secret-key-2026",
    "secret",
    "changeme",
    "password",
    "replace-with-a-secure-randomly-generated-secret-key",
}

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="allow")

    PROJECT_NAME: str = "reServe AI - Smart Food Waste Reduction & Redistribution"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Authentication Rate Limiting
    AUTH_RATE_LIMIT_ENABLED: bool = os.getenv("AUTH_RATE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")
    AUTH_RATE_LIMIT_MAX_REQUESTS: int = int(
        os.getenv("AUTH_RATE_LIMIT_MAX_REQUESTS", "100" if os.getenv("ENVIRONMENT", "development").lower() != "production" else "10")
    )
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./reserve_ai.db")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # External ML & CV microservice addresses
    ML_SERVICE_URL: str = os.getenv("ML_SERVICE_URL", "http://localhost:8001")

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    import json
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(origin).strip() for origin in parsed if str(origin).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return []

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        env = (self.ENVIRONMENT or "development").lower()
        key = self.SECRET_KEY

        if env == "production":
            if not key or key in INSECURE_DEFAULT_SECRETS or len(key) < 32:
                raise ValueError(
                    "Production configuration error: SECRET_KEY must be set to a secure, "
                    "non-default value with at least 32 characters in production."
                )
            if not self.BACKEND_CORS_ORIGINS:
                raise ValueError(
                    "Production configuration error: BACKEND_CORS_ORIGINS must be configured "
                    "with at least one trusted origin in production."
                )
            if any(origin == "*" for origin in self.BACKEND_CORS_ORIGINS):
                raise ValueError(
                    "Production configuration error: Wildcard CORS origin ('*') is strictly "
                    "prohibited when credentials support is enabled."
                )
        else:
            if not key:
                self.SECRET_KEY = "dev-insecure-test-secret-key-for-local-testing-only-32bytes"
            # In non-production, prevent unsafe wildcard origin with credentials
            if isinstance(self.BACKEND_CORS_ORIGINS, list):
                self.BACKEND_CORS_ORIGINS = [o for o in self.BACKEND_CORS_ORIGINS if o != "*"]
        return self

settings = Settings()
