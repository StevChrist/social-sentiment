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
    
    # Gemini Engine Settings (Production)
    SENTIMENT_PROVIDER: str = Field(default="gemini", description="Provider: 'gemini' or 'xlmr'")
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API Key")
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash-lite", description="Gemini model name")
    GEMINI_BATCH_SIZE: int = Field(default=100, description="Max comments per Gemini API batch")
    GEMINI_MAX_CHARS_PER_BATCH: int = Field(default=50000, description="Max character count per Gemini API batch")
    GEMINI_MAX_RETRIES: int = Field(default=5, description="Max retries on 429/5xx")
    GEMINI_REQUEST_TIMEOUT: float = Field(default=60.0, description="Request timeout in seconds")
    
    # Local XLM-RoBERTa Model (Offline / Benchmark / Fallback)
    MODEL_DIR: str = Field(default="artifacts/xlmr-sentiment-best-balanced", description="Model directory path")
    NEUTRAL_THRESHOLD: Optional[float] = Field(default=None, description="Custom neutral threshold")
    
    # API Quota & Safety Settings (Configured for Safe Free Tier Usage)
    MONTHLY_QUOTA_LIMIT: int = 3000  # 3,000 units/month (~300,000 comments/month, 100% Free Tier safe)
    DAILY_QUOTA_LIMIT: int = 150     # 150 units/day daily safety cap
    MAX_COMMENTS_LIMIT: int = 10000  # Up to 10,000 comments for 50%, 75%, 100% analysis
    DEFAULT_MAX_COMMENTS: int = 1000
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
