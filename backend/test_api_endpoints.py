# backend/test_api_endpoints.py
from __future__ import annotations

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import json

from backend.main import app
from backend.services.sentiment.factory import SentimentService


class TestAPIEndpoints(unittest.TestCase):

    def setUp(self):
        SentimentService.reset()
        self.client = TestClient(app)

    def test_health_check_gemini_mode(self):
        with patch.dict("os.environ", {
            "SENTIMENT_PROVIDER": "gemini",
            "GEMINI_API_KEY": "fake_gemini_key",
            "GEMINI_MODEL": "gemini-2.5-flash-lite",
        }):
            from backend.core.config import get_settings
            get_settings.cache_clear()

            response = self.client.get("/health")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "healthy")
            self.assertEqual(data["provider"], "gemini")
            self.assertEqual(data["model"], "gemini-2.5-flash-lite")
            self.assertTrue(data["gemini_api_configured"])

    @patch("backend.services.sentiment.gemini.genai.Client")
    def test_predict_endpoint_gemini(self, mock_genai_client):
        # Mock Gemini API response
        mock_instance = MagicMock()
        mock_genai_client.return_value = mock_instance
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "results": [
                {"id": "0", "label": "positive"},
                {"id": "1", "label": "negative"}
            ]
        })
        mock_instance.models.generate_content.return_value = mock_response

        with patch.dict("os.environ", {
            "SENTIMENT_PROVIDER": "gemini",
            "GEMINI_API_KEY": "fake_gemini_key",
        }):
            from backend.core.config import get_settings
            get_settings.cache_clear()
            SentimentService.reset()

            res = self.client.post("/api/predict", json={"texts": ["Mantap banget", "Buruk sekali"]})
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(len(data["results"]), 2)
            self.assertEqual(data["results"][0]["label"], "positive")
            self.assertIsNone(data["results"][0]["confidence"])
            self.assertEqual(data["results"][1]["label"], "negative")


if __name__ == "__main__":
    unittest.main()
