import requests
import json

url = "http://127.0.0.1:8000/api/predict"

test_data = {
    "texts": [
        "Amazing tutorial! Very helpful 👍",
        "Worst video ever, dislike!",
        "The content is average",
        "Video bagus, terima kasih!",
        "Jelek banget videonya",
        "Lumayan lah"
    ]
}

response = requests.post(url, json=test_data)
result = response.json()

print("=== SENTIMENT ANALYSIS RESULTS ===")
for i, (text, pred) in enumerate(zip(test_data["texts"], result["results"])):
    print(f"\n{i+1}. Text: {text}")
    print(f"   Label: {pred['label'].upper()}")
    print(f"   Confidence: {pred['confidence']:.3f}")
    print(f"   Scores: Neg={pred['scores']['negative']:.3f}, "
          f"Neu={pred['scores']['neutral']:.3f}, "
          f"Pos={pred['scores']['positive']:.3f}")
