# backend/services/sentiment/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, TypedDict

LABELS = ["negative", "neutral", "positive"]

class SentimentScores(TypedDict, total=False):
    negative: Optional[float]
    neutral: Optional[float]
    positive: Optional[float]

class SentimentPrediction(TypedDict):
    label: str
    confidence: Optional[float]
    scores: Optional[SentimentScores]

ProgressCallback = Callable[[int, int, str], None]
"""ProgressCallback(completed_count, total_count, message)"""


class BaseSentimentService(ABC):
    """Abstract base class for all sentiment analysis providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the provider identifier (e.g. 'gemini-2.5-flash-lite', 'xlmr-sentiment')."""
        pass

    @abstractmethod
    def predict(
        self,
        texts: List[str],
        progress_cb: Optional[ProgressCallback] = None,
        **kwargs,
    ) -> List[SentimentPrediction]:
        """
        Predict sentiment for a list of texts.
        
        Args:
            texts: List of raw comment strings.
            progress_cb: Optional callback receiving (completed, total, step_description).
            
        Returns:
            List of SentimentPrediction dicts matching length of `texts`.
            
        Raises:
            Exception: If prediction fails and cannot be recovered.
        """
        pass

    def predict_single(self, text: str) -> SentimentPrediction:
        """Convenience method to predict sentiment for a single text."""
        res = self.predict([text])
        if not res:
            raise RuntimeError("Empty prediction result returned")
        return res[0]
