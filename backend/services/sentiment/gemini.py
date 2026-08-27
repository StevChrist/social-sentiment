# backend/services/sentiment/gemini.py
from __future__ import annotations

import json
import logging
import random
import time
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from backend.core.config import get_settings
from backend.services.sentiment.base import (
    LABELS,
    BaseSentimentService,
    ProgressCallback,
    SentimentPrediction,
)

logger = logging.getLogger(__name__)

_SYSTEM_INSTRUCTION = """You are an expert multilingual sentiment analysis engine for social media (YouTube comments in Indonesian, English, and mixed slang).
Classify each comment into exactly one of three categories: "positive", "neutral", or "negative".

Guidelines:
- "positive": Expresses appreciation, praise, enjoyment, agreement, helpfulness, excitement, satisfaction, or positive emojis.
- "negative": Expresses criticism, disappointment, hate, anger, frustration, sarcasm/mockery against the subject, or negative emojis.
- "neutral": Objective inquiries, factual statements, timestamps, neutral observations, spam without sentiment, or comments lacking sentiment.
- Understand Indonesian slang and abbreviations (e.g., "mantap", "kece", "parah", "zonk", "sampah", "anjir/anjay", "bgt", "bener").
- Return ONLY valid JSON adhering strictly to the schema. Do NOT include explanations, markdown formatting, or chain-of-thought."""

_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "results": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "label": {
                        "type": "STRING",
                        "enum": ["positive", "neutral", "negative"],
                    },
                },
                "required": ["id", "label"],
            },
        }
    },
    "required": ["results"],
}


class GeminiBatchError(RuntimeError):
    """Raised when a Gemini batch analysis fails and cannot be recovered after retries."""
    pass


class GeminiSentimentService(BaseSentimentService):
    """
    Sentiment analysis service powered by Google Gemini API (Free Tier).
    Uses batching, dual-constraint chunking, structured JSON outputs,
    and exponential backoff retry.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        batch_size: Optional[int] = None,
        max_chars_per_batch: Optional[int] = None,
        max_retries: Optional[int] = None,
        timeout: Optional[float] = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in your .env file."
            )

        self._model_name = model_name or settings.GEMINI_MODEL or "gemini-2.5-flash-lite"
        self.batch_size = batch_size or settings.GEMINI_BATCH_SIZE or 20
        self.max_chars_per_batch = max_chars_per_batch or settings.GEMINI_MAX_CHARS_PER_BATCH or 12000
        self.max_retries = max_retries if max_retries is not None else settings.GEMINI_MAX_RETRIES
        self.timeout = timeout or settings.GEMINI_REQUEST_TIMEOUT or 30.0

        # Initialize Google GenAI client
        self.client = genai.Client(api_key=self.api_key)
        logger.info(
            f"✅ GeminiSentimentService initialized with model '{self._model_name}', "
            f"batch_size={self.batch_size}, max_chars={self.max_chars_per_batch}"
        )

    @property
    def provider_name(self) -> str:
        return self._model_name

    def _chunk_texts_dual_constraint(
        self, texts: List[str]
    ) -> List[List[tuple[int, str]]]:
        """
        Partition indexed texts into chunks respecting:
        1. Max item count (`self.batch_size`)
        2. Max cumulative character length (`self.max_chars_per_batch`)
        """
        chunks: List[List[tuple[int, str]]] = []
        current_chunk: List[tuple[int, str]] = []
        current_chars = 0

        for idx, text in enumerate(texts):
            clean_text = (text or "").strip()
            # Truncate overly long individual comments for safety
            if len(clean_text) > 1000:
                clean_text = clean_text[:1000]

            item_len = len(clean_text) + 20  # account for JSON formatting overhead

            if current_chunk and (
                len(current_chunk) >= self.batch_size
                or (current_chars + item_len) > self.max_chars_per_batch
            ):
                chunks.append(current_chunk)
                current_chunk = []
                current_chars = 0

            current_chunk.append((idx, clean_text))
            current_chars += item_len

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _call_gemini_with_retry(
        self, batch_items: List[tuple[int, str]], batch_num: int, total_batches: int
    ) -> Dict[str, str]:
        """
        Send a batch of comments to Gemini API with exponential backoff + jitter.
        Returns a dict mapping string ID to sentiment label.
        
        CRITICAL: If the batch fails after max_retries, it raises GeminiBatchError.
        NEVER silently convert failed batches to 'neutral'.
        """
        # Prepare input payload for Gemini
        comments_payload = [{"id": str(idx), "text": text} for idx, text in batch_items]
        prompt = (
            "Analyze the sentiment of the following comments and return the classification per ID:\n"
            + json.dumps(comments_payload, ensure_ascii=False)
        )

        config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=_RESPONSE_SCHEMA,
            temperature=0.0,  # Deterministic classification
        )

        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"🤖 [Batch {batch_num}/{total_batches}] Sending {len(batch_items)} comments "
                    f"to {self._model_name} (Attempt {attempt}/{self.max_retries})..."
                )
                response = self.client.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                    config=config,
                )

                if not response or not response.text:
                    raise ValueError("Received empty response from Gemini API")

                parsed = json.loads(response.text)
                results_list = parsed.get("results", [])

                id_to_label: Dict[str, str] = {}
                for item in results_list:
                    item_id = str(item.get("id"))
                    label = str(item.get("label", "")).lower().strip()
                    if label in LABELS:
                        id_to_label[item_id] = label

                # Validate completeness: every item in batch must be present
                missing_ids = [str(idx) for idx, _ in batch_items if str(idx) not in id_to_label]
                if missing_ids:
                    raise ValueError(
                        f"Incomplete batch response from Gemini: missing IDs {missing_ids[:5]} "
                        f"({len(missing_ids)} missing out of {len(batch_items)})"
                    )

                logger.info(
                    f"✅ [Batch {batch_num}/{total_batches}] Successfully analyzed {len(id_to_label)} comments."
                )
                return id_to_label

            except Exception as e:
                last_exception = e
                err_str = str(e)
                is_rate_limit = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()

                if attempt < self.max_retries:
                    # Check if Gemini provided a specific retry delay in the error message
                    import re
                    retry_match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_str, re.IGNORECASE)
                    if retry_match:
                        suggested_delay = float(retry_match.group(1)) + 2.0
                        backoff = max(suggested_delay, 12.0)
                    elif is_rate_limit:
                        backoff = 12.0 + (attempt * 3.0) + random.uniform(1.0, 3.0)
                    else:
                        backoff = (2.0 ** attempt) + random.uniform(0.5, 1.5)

                    logger.warning(
                        f"⚠️ [Batch {batch_num}/{total_batches}] Error on attempt {attempt}/{self.max_retries}: {e}. "
                        f"Waiting {backoff:.2f}s before retry..."
                    )
                    time.sleep(backoff)
                else:
                    logger.error(
                        f"❌ [Batch {batch_num}/{total_batches}] Failed after {self.max_retries} attempts: {e}"
                    )

        # STRICT: Do not convert to neutral. Fail explicitly.
        raise GeminiBatchError(
            f"Gemini API analysis failed for batch {batch_num}/{total_batches} "
            f"({len(batch_items)} comments) after {self.max_retries} retries. "
            f"Last error: {last_exception}"
        ) from last_exception

    def predict(
        self,
        texts: List[str],
        progress_cb: Optional[ProgressCallback] = None,
        **kwargs,
    ) -> List[SentimentPrediction]:
        """
        Batch prediction using Gemini Flash-Lite with Free Tier 15 RPM rate limit compliance.
        """
        if not texts:
            return []

        total_texts = len(texts)
        chunks = self._chunk_texts_dual_constraint(texts)
        total_batches = len(chunks)

        logger.info(
            f"🚀 Starting Gemini sentiment analysis: {total_texts} comments split into {total_batches} batches "
            f"(Targeting Free Tier 15 RPM rate limit safety)."
        )

        all_predictions: List[Optional[SentimentPrediction]] = [None] * total_texts
        completed_count = 0

        for batch_idx, batch_items in enumerate(chunks, start=1):
            if progress_cb:
                step_msg = (
                    f"Analyzing batch {batch_idx}/{total_batches} "
                    f"({completed_count}/{total_texts} comments processed)..."
                )
                progress_cb(completed_count, total_texts, step_msg)

            # Call Gemini API for this batch (raises GeminiBatchError on unrecoverable failure)
            id_to_label = self._call_gemini_with_retry(batch_items, batch_idx, total_batches)

            for original_idx, _ in batch_items:
                label = id_to_label.get(str(original_idx))
                if label not in LABELS:
                    raise GeminiBatchError(
                        f"Comment index {original_idx} received invalid or missing label from Gemini: {label}"
                    )
                all_predictions[original_idx] = {
                    "label": label,
                    "confidence": None,  # Explicitly null - generative classification without pseudo-probability
                    "scores": {
                        "negative": None,
                        "neutral": None,
                        "positive": None,
                    },
                }

            completed_count += len(batch_items)

            if progress_cb:
                step_msg = f"Completed batch {batch_idx}/{total_batches} ({completed_count}/{total_texts} comments)."
                progress_cb(completed_count, total_texts, step_msg)

            # Free Tier safety pacing: space requests to stay under 15 RPM limit (~4.2s per request)
            if batch_idx < total_batches:
                time.sleep(4.2)

        # Final verification: ensure no None entries
        results: List[SentimentPrediction] = []
        for i, pred in enumerate(all_predictions):
            if pred is None:
                raise GeminiBatchError(f"Comment index {i} was not classified by Gemini.")
            results.append(pred)

        return results
