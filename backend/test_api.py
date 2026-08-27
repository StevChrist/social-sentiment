import requests
import json

if __name__ == "__main__":
    url = "http://127.0.0.1:8000/api/predict"

    test_data = {
        "texts": [
            "Amazing tutorial! Very helpful 👍",
            "Worst video ever, dislike!",
            "The content is average",
            "Video bagus, terima kasih!",
            "Jelek banget videonya",
            "Lumayan lah",
        ]
    }

    try:
        response = requests.post(url, json=test_data)
        result = response.json()

        print("=== SENTIMENT ANALYSIS RESULTS ===")
        for i, (text, pred) in enumerate(zip(test_data["texts"], result.get("results", []))):
            print(f"\n{i+1}. Text: {text}")
            print(f"   Label: {pred.get('label', '').upper()}")
            conf = pred.get("confidence")
            conf_str = f"{conf:.3f}" if isinstance(conf, (int, float)) else "N/A"
            print(f"   Confidence: {conf_str}")
            scores = pred.get("scores") or {}
            print(
                f"   Scores: Neg={scores.get('negative', 'N/A')}, "
                f"Neu={scores.get('neutral', 'N/A')}, "
                f"Pos={scores.get('positive', 'N/A')}"
            )
    except Exception as e:
        print(f"Failed to connect to live server: {e}")
        print("Tip: Run the backend server first via 'uvicorn backend.main:app' or use 'backend.test_api_endpoints' for unit testing.")
