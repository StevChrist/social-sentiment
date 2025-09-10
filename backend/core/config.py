# backend/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
from pydantic import Field, field_validator

class Settings(BaseSettings):
    APP_NAME: str = "Social Sentiment API"
    ENV: str = "dev"
    
    # Database
    DATABASE_URL: Optional[str] = Field(default=None, description="Database connection URL")
    
    # YouTube
    YOUTUBE_API_KEY: Optional[str] = Field(default=None, description="YouTube API key")
    
    # Model
    MODEL_DIR: str = Field(default="artifacts/xlmr-sentiment-best-balanced", description="Model directory path")
    NEUTRAL_THRESHOLD: Optional[float] = Field(default=None, description="Custom neutral threshold")
    
    # API Settings
    MAX_COMMENTS_LIMIT: int = 10000
    DEFAULT_MAX_COMMENTS: int = 300
    BATCH_SIZE: int = 32
    MAX_TEXT_LENGTH: int = 160
    
    @field_validator('NEUTRAL_THRESHOLD', mode='before')
    @classmethod
    def validate_threshold(cls, v):
        """Validate and convert NEUTRAL_THRESHOLD"""
        if v == '' or v is None:
            return None
        try:
            val = float(v)
            if 0.0 <= val <= 1.0:
                return val
            return None
        except (ValueError, TypeError):
            return None
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

@lru_cache()
def get_settings() -> Settings:
    return Settings()
