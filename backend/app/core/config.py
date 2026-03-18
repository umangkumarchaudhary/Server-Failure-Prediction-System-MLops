"""Application configuration using Pydantic Settings."""
from typing import Any, List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # App
    PROJECT_NAME: str = "SensorMind"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    AUTOMATION_ENABLED: bool = True
    AUTOMATION_NOTIFY_ON_DRIFT: bool = True
    AUTOMATION_RISK_SYNC_INTERVAL_SECONDS: int = 300
    AUTOMATION_DRIFT_CHECK_INTERVAL_SECONDS: int = 900
    AUTOMATION_RISK_LOOKBACK_HOURS: int = 72
    AUTOMATION_DRIFT_METRIC_LIMIT: int = 5000
    AUTOMATION_DRIFT_PREDICTION_LIMIT: int = 1000
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production-2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://predictr:predictr_dev_2026@localhost:5432/predictr_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS - accepts comma-separated string or list
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000"

    @field_validator("DEBUG", "AUTOMATION_ENABLED", "AUTOMATION_NOTIFY_ON_DRIFT", mode="before")
    @classmethod
    def parse_debug_value(cls, value: Any) -> bool:
        """Accept common environment-style debug strings without crashing startup."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production", "prod"}:
                return False
        return bool(value)
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    
    # OpenAI (for AI Copilot)
    OPENAI_API_KEY: str = ""


settings = Settings()
