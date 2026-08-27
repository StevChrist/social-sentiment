# backend/services/sentiment/factory.py
from __future__ import annotations

import logging
from typing import Optional

from backend.core.config import get_settings
from backend.services.sentiment.base import BaseSentimentService
from backend.services.sentiment.gemini import GeminiSentimentService
from backend.services.sentiment.xlmr import XLMRoBERTaSentimentService

logger = logging.getLogger(__name__)


class SentimentService:
    """Factory manager for sentiment analysis services."""

    _instances: dict[str, BaseSentimentService] = {}

    @classmethod
    def get(cls, provider: Optional[str] = None) -> BaseSentimentService:
        """
        Get or instantiate the configured sentiment service provider.
        
        Args:
            provider: 'gemini' | 'xlmr' (defaults to settings.SENTIMENT_PROVIDER)
        """
        settings = get_settings()
        if not settings.GEMINI_API_KEY:
            get_settings.cache_clear()
            settings = get_settings()

        selected_provider = (provider or settings.SENTIMENT_PROVIDER or "gemini").lower().strip()

        if selected_provider in cls._instances:
            return cls._instances[selected_provider]

        if selected_provider == "gemini":
            logger.info(f"Initializing SentimentService with Provider: GEMINI ({settings.GEMINI_MODEL})")
            svc = GeminiSentimentService(
                api_key=settings.GEMINI_API_KEY,
                model_name=settings.GEMINI_MODEL,
                batch_size=settings.GEMINI_BATCH_SIZE,
                max_chars_per_batch=settings.GEMINI_MAX_CHARS_PER_BATCH,
                max_retries=settings.GEMINI_MAX_RETRIES,
                timeout=settings.GEMINI_REQUEST_TIMEOUT,
            )
            cls._instances[selected_provider] = svc
            return svc

        elif selected_provider == "xlmr":
            logger.info("Initializing SentimentService with Provider: XLM-RoBERTa (Local PyTorch)")
            svc = XLMRoBERTaSentimentService(
                model_dir=settings.MODEL_DIR,
                neutral_threshold=settings.NEUTRAL_THRESHOLD,
                batch_size=settings.BATCH_SIZE,
            )
            cls._instances[selected_provider] = svc
            return svc

        else:
            raise ValueError(
                f"Unknown SENTIMENT_PROVIDER '{selected_provider}'. "
                f"Valid options are 'gemini' or 'xlmr'."
            )

    @classmethod
    def reset(cls) -> None:
        """Clear cached service instances (useful for testing or switching provider dynamically)."""
        cls._instances.clear()
