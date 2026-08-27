# backend/services/sentiment/xlmr.py
from __future__ import annotations

import json
import logging
import os
from typing import List, Optional

from backend.core.config import get_settings
from backend.services.sentiment.base import (
    LABELS,
    BaseSentimentService,
    ProgressCallback,
    SentimentPrediction,
)

logger = logging.getLogger(__name__)


class XLMRoBERTaSentimentService(BaseSentimentService):
    """
    Local XLM-RoBERTa deep learning sentiment analysis service (PyTorch).
    Used for offline research, benchmarks, or local fallback.
    Model weights are loaded into RAM ONLY upon instantiation.
    """

    def __init__(
        self,
        model_dir: Optional[str] = None,
        neutral_threshold: Optional[float] = None,
        batch_size: int = 32,
    ):
        settings = get_settings()
        self.model_dir = model_dir or settings.MODEL_DIR
        self.batch_size = batch_size

        logger.info(f"⏳ Lazy loading PyTorch & XLM-RoBERTa model from {self.model_dir}...")
        
        # Lazy imports so torch/transformers are not required if running production Gemini
        try:
            import torch
            import numpy as np
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as e:
            logger.error(
                "PyTorch or Transformers is not installed in this environment. "
                "For production, use SENTIMENT_PROVIDER=gemini. "
                "For offline XLM-RoBERTa benchmark, install: pip install -r backend/requirements-benchmark.txt"
            )
            raise ImportError(
                "PyTorch/Transformers not found. To use XLM-RoBERTa, install backend/requirements-benchmark.txt"
            ) from e

        self._torch = torch
        self._np = np

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using PyTorch device: {self.device}")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir, use_fast=False)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_dir).to(
                self.device
            )
            self.model.eval()
            logger.info(f"✅ XLM-RoBERTa model loaded successfully from {self.model_dir}")
        except Exception as e:
            logger.error(f"❌ Failed to load XLM-RoBERTa model from {self.model_dir}: {e}")
            raise

        # Load neutral threshold
        t = neutral_threshold
        if t is None:
            cfg_path = os.path.join(self.model_dir, "inference_config.json")
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                        t = config.get("t_neu")
                except Exception as e:
                    logger.warning(f"Failed to load inference config: {e}")

        self.t_neu = float(t) if t is not None else 0.5
        logger.info(f"XLM-RoBERTa neutral threshold set to: {self.t_neu}")

    @property
    def provider_name(self) -> str:
        return "xlmr-sentiment"

    def predict(
        self,
        texts: List[str],
        progress_cb: Optional[ProgressCallback] = None,
        max_len: int = 160,
        **kwargs,
    ) -> List[SentimentPrediction]:
        """Predict sentiment for list of texts using local XLM-RoBERTa."""
        if not texts:
            return []

        results: List[SentimentPrediction] = []
        total = len(texts)
        total_batches = (total + self.batch_size - 1) // self.batch_size

        with self._torch.no_grad():
            for batch_num, i in enumerate(range(0, total, self.batch_size), start=1):
                batch = texts[i : i + self.batch_size]

                if progress_cb:
                    progress_cb(
                        i,
                        total,
                        f"Running XLM-RoBERTa inference: Batch {batch_num}/{total_batches}...",
                    )

                try:
                    encoded = self.tokenizer(
                        batch,
                        truncation=True,
                        max_length=max_len,
                        padding=True,
                        return_tensors="pt",
                    ).to(self.device)

                    logits = self.model(**encoded).logits.detach().cpu().numpy()

                    # Softmax probabilities
                    exp_logits = self._np.exp(logits - logits.max(axis=1, keepdims=True))
                    probs = exp_logits / exp_logits.sum(axis=1, keepdims=True)

                    for prob in probs:
                        if prob[1] >= self.t_neu:
                            pred_id = 1
                        else:
                            pred_id = int(self._np.argmax(prob))

                        results.append({
                            "label": LABELS[pred_id],
                            "confidence": float(prob[pred_id]),
                            "scores": {
                                "negative": float(prob[0]),
                                "neutral": float(prob[1]),
                                "positive": float(prob[2]),
                            },
                        })

                except Exception as e:
                    logger.error(f"Error during XLM-RoBERTa batch inference: {e}")
                    raise

        if progress_cb:
            progress_cb(total, total, "XLM-RoBERTa inference completed.")

        return results
