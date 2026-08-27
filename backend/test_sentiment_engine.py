# backend/test_sentiment_engine.py
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
import json

from backend.services.sentiment.base import LABELS, BaseSentimentService
from backend.services.sentiment.gemini import GeminiSentimentService, GeminiBatchError
from backend.services.sentiment.factory import SentimentService
from backend.core.config import get_settings


class TestSentimentEngine(unittest.TestCase):

    def setUp(self):
        SentimentService.reset()

    def test_factory_gemini_selection(self):
        with patch.dict("os.environ", {"SENTIMENT_PROVIDER": "gemini", "GEMINI_API_KEY": "fake_test_key"}):
            get_settings.cache_clear()
            svc = SentimentService.get("gemini")
            self.assertIsInstance(svc, GeminiSentimentService)
            self.assertTrue("flash-lite" in svc.provider_name)

    def test_dual_constraint_chunking(self):
        svc = GeminiSentimentService(
            api_key="fake_key",
            model_name="gemini-2.5-flash-lite",
            batch_size=3,
            max_chars_per_batch=100,
        )
        texts = [
            "Short comment 1",
            "Short comment 2",
            "Short comment 3",
            "Short comment 4",
            "This is a relatively longer comment that should easily exceed the maximum character limit when accumulated",
            "Final comment",
        ]
        chunks = svc._chunk_texts_dual_constraint(texts)
        # Verify all texts are partitioned with their correct indices preserved
        total_items_in_chunks = sum(len(c) for c in chunks)
        self.assertEqual(total_items_in_chunks, len(texts))
        
        # Check indices match 0..5
        all_indices = [idx for chunk in chunks for idx, _ in chunk]
        self.assertEqual(all_indices, list(range(len(texts))))

    @patch("backend.services.sentiment.gemini.time.sleep", return_value=None)
    def test_strict_failure_handling(self, mock_sleep):
        svc = GeminiSentimentService(
            api_key="fake_key",
            model_name="gemini-3.5-flash-lite",
            batch_size=20,
            max_retries=2,
        )
        
        # Mock client to throw rate limit / error
        svc.client = MagicMock()
        svc.client.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED: Rate limit exceeded")

        with self.assertRaises(GeminiBatchError) as ctx:
            svc.predict(["Komentar uji 1", "Komentar uji 2"])
        
        self.assertIn("failed", str(ctx.exception).lower())

    def test_structured_json_response_parsing(self):
        svc = GeminiSentimentService(
            api_key="fake_key",
            model_name="gemini-2.5-flash-lite",
            batch_size=5,
        )
        
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "results": [
                {"id": "0", "label": "positive"},
                {"id": "1", "label": "negative"},
                {"id": "2", "label": "neutral"},
            ]
        })
        svc.client = MagicMock()
        svc.client.models.generate_content.return_value = mock_response

        texts = ["Bagus bgt", "Jelek parah", "Jam berapa ini?"]
        preds = svc.predict(texts)

        self.assertEqual(len(preds), 3)
        self.assertEqual(preds[0]["label"], "positive")
        self.assertIsNone(preds[0]["confidence"])
        self.assertEqual(preds[1]["label"], "negative")
        self.assertEqual(preds[2]["label"], "neutral")


if __name__ == "__main__":
    unittest.main()
