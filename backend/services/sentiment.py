# backend/services/sentiment.py
"""
Backward compatibility layer for SentimentService.
Routes to backend.services.sentiment package.
"""
from backend.services.sentiment import (
    LABELS,
    BaseSentimentService,
    GeminiBatchError,
    GeminiSentimentService,
    SentimentPrediction,
    SentimentService,
    XLMRoBERTaSentimentService,
)

__all__ = [
    "LABELS",
    "BaseSentimentService",
    "SentimentPrediction",
    "SentimentService",
    "GeminiSentimentService",
    "GeminiBatchError",
    "XLMRoBERTaSentimentService",
]
