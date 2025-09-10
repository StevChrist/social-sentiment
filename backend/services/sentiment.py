# backend/services/sentiment.py
from __future__ import annotations
from typing import List, Dict, Optional
import os
import json
import logging
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from backend.core.config import get_settings

logger = logging.getLogger(__name__)

_LABELS = ["negative", "neutral", "positive"]

class SentimentService:
    _instance: Optional["SentimentService"] = None

    def __init__(self, model_dir: str, neutral_threshold: Optional[float] = None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        try:
            # Use slow tokenizer for stability
            self.tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=False)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(self.device)
            self.model.eval()
            logger.info(f"Model loaded successfully from {model_dir}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

        # Load neutral threshold
        t = neutral_threshold
        if t is None:
            cfg_path = os.path.join(model_dir, "inference_config.json")
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                        t = config.get("t_neu")
                except Exception as e:
                    logger.warning(f"Failed to load inference config: {e}")
        
        self.t_neu = float(t) if t is not None else 0.5
        logger.info(f"Neutral threshold set to: {self.t_neu}")

    @classmethod
    def get(cls) -> "SentimentService":
        if cls._instance is None:
            settings = get_settings()
            cls._instance = SentimentService(settings.MODEL_DIR, settings.NEUTRAL_THRESHOLD)
        return cls._instance

    def predict(self, texts: List[str], max_len: int = 160, batch_size: int = 32) -> List[Dict]:
        """
        Predict sentiment for list of texts.
        
        Returns:
            List of dict: {label, confidence, scores:{negative, neutral, positive}}
        """
        if not texts:
            return []
        
        results: List[Dict] = []
        
        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                
                try:
                    # Tokenize batch
                    encoded = self.tokenizer(
                        batch, 
                        truncation=True, 
                        max_length=max_len,
                        padding=True, 
                        return_tensors="pt"
                    ).to(self.device)
                    
                    # Get predictions
                    logits = self.model(**encoded).logits.detach().cpu().numpy()
                    
                    # Apply softmax
                    exp_logits = np.exp(logits - logits.max(axis=1, keepdims=True))
                    probs = exp_logits / exp_logits.sum(axis=1, keepdims=True)
                    
                    # Process each prediction
                    for prob in probs:
                        # Apply neutral threshold
                        if prob[1] >= self.t_neu:
                            pred_id = 1
                        else:
                            pred_id = int(np.argmax(prob))
                        
                        results.append({
                            "label": _LABELS[pred_id],
                            "confidence": float(prob[pred_id]),
                            "scores": {
                                "negative": float(prob[0]), 
                                "neutral": float(prob[1]), 
                                "positive": float(prob[2])
                            }
                        })
                        
                except Exception as e:
                    logger.error(f"Error in batch prediction: {e}")
                    # Add error placeholders for this batch
                    for _ in batch:
                        results.append({
                            "label": "neutral",
                            "confidence": 0.0,
                            "scores": {"negative": 0.0, "neutral": 1.0, "positive": 0.0}
                        })
        
        return results

    def predict_single(self, text: str) -> Dict:
        """Predict sentiment for single text"""
        return self.predict([text])[0]
