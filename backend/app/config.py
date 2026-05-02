"""Application configuration — loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql+asyncpg://postgres:pass@localhost/Zetra"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Gemini
    gemini_api_key: str = ""
    gemini_text_model: str = "gemini-1.5-flash"
    gemini_vision_model: str = "gemini-1.5-flash"

    # AWS / S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket: str = "Zetra-images"

    # External APIs
    google_places_api_key: str = ""

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    # CLIP model
    clip_model: str = "openai/clip-vit-base-patch32"

    # CV thresholds
    cv_strong_match_threshold: float = 0.25
    cv_likely_match_threshold: float = 0.45
    llm_confidence_threshold: float = 0.75

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]


settings = Settings()
