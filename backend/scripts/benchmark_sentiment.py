# backend/scripts/benchmark_sentiment.py
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.core.config import get_settings
from backend.services.sentiment.base import LABELS, BaseSentimentService
from backend.services.sentiment.gemini import GeminiSentimentService
from backend.services.sentiment.xlmr import XLMRoBERTaSentimentService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("benchmark")

# ── Built-in Curated Ground-Truth Benchmark Dataset ──────────────────────────
# Curated diverse sample covering Indonesian & English, slang, emojis, short/long,
# neutral inquiries, sarcasm, constructive feedback, and strong sentiment.
DEFAULT_BENCHMARK_DATA: List[Dict[str, str]] = [
    # Indonesian Positive
    {"text": "Kontennya sangat informatif dan penjelasannya mudah dipahami, terima kasih bang!", "label": "positive"},
    {"text": "Mantap bgt ilmunya min, langsung saya praktekin dan berhasil 👍🔥", "label": "positive"},
    {"text": "Keren parah editingnya, cinematic banget dan adem diliatnya", "label": "positive"},
    {"text": "Suka banget sama cara penyampaiannya yang lugas dan gak bertele-tele.", "label": "positive"},
    {"text": "Gokil sih ini penjelasan terbagus di YouTube Indo, auto subscribe!", "label": "positive"},
    {"text": "Makasih banyak tutornya sangat membantu buat tugas akhir saya.", "label": "positive"},
    {"text": "Top markotop, daging semua isinya tanpa banyak basa-basi.", "label": "positive"},
    {"text": "Alhamdulillah nemu video ini, sangat mencerahkan dan detail.", "label": "positive"},
    
    # Indonesian Negative
    {"text": "Video sampah gak ada isinya sama sekali cuma buang-buang kuota.", "label": "negative"},
    {"text": "Suaranya kecil banget kresek-kresek, gak niat bikin konten apa gimana sih?", "label": "negative"},
    {"text": "Clickbait parah judul sama isinya beda jauh, jangan ditonton guys zonk bgt.", "label": "negative"},
    {"text": "Penjelasannya muter-muter bikin pusing dan gak jelas intinya apa.", "label": "negative"},
    {"text": "Kecewa banget, informasi yang disampein banyak yang salah dan hoax.", "label": "negative"},
    {"text": "Gak recommended, tutorialnya gak bisa dipake dan bikin error.", "label": "negative"},
    {"text": "Boring banget suaranya bikin ngantuk, kualitasnya buruk.", "label": "negative"},
    {"text": "Nyesel buang waktu nonton video ga bermutu kayak gini.", "label": "negative"},

    # Indonesian Neutral
    {"text": "Bang lagu background di menit 03:45 judulnya apa ya?", "label": "neutral"},
    {"text": "01:20 Pembukaan\n04:15 Tutorial\n08:30 Kesimpulan", "label": "neutral"},
    {"text": "Ini bisa dijalankan di Windows 10 atau cuma khusus Linux bang?", "label": "neutral"},
    {"text": "Video ini diupload tanggal 15 Januari kemarin ya.", "label": "neutral"},
    {"text": "Spesifikasi laptop yang dipakai apa aja mas?", "label": "neutral"},
    {"text": "Pertama kali nonton channel ini, izin simak materinya.", "label": "neutral"},
    {"text": "Apakah tools ini berbayar atau open source?", "label": "neutral"},
    {"text": "Lokasi syutingnya di daerah mana ya?", "label": "neutral"},

    # English Positive
    {"text": "This is hands down the best explanation of this topic on the entire platform. Kudos!", "label": "positive"},
    {"text": "Incredible work! Your clear and concise delivery saved me hours of debugging.", "label": "positive"},
    {"text": "Loved the breakdown at the end, super helpful and well structured.", "label": "positive"},
    {"text": "Awesome video, keep up the amazing content brother! 🚀👏", "label": "positive"},
    {"text": "Finally someone who explains the 'why' and not just the 'how'. Brilliant!", "label": "positive"},
    {"text": "Subscribed instantly! Perfect pace, great visuals, and zero fluff.", "label": "positive"},
    {"text": "Thank you so much, this solved the issue I was stuck on for days.", "label": "positive"},

    # English Negative
    {"text": "Complete waste of time. The title is purely misleading clickbait.", "label": "negative"},
    {"text": "Horrible audio quality, couldn't even understand what you were saying over the static.", "label": "negative"},
    {"text": "Outdated information and half of the code samples don't even compile anymore.", "label": "negative"},
    {"text": "Extremely annoying background music and monotonous commentary. Disliked.", "label": "negative"},
    {"text": "The presenter has no idea what they are talking about, factually incorrect in multiple parts.", "label": "negative"},
    {"text": "Terrible pacing, spent 10 minutes talking about sponsor before getting to the point.", "label": "negative"},
    {"text": "Useless video, do not follow these steps or you will break your config.", "label": "negative"},

    # English Neutral
    {"text": "Timestamp for the code walkthrough is at 05:22 guys.", "label": "neutral"},
    {"text": "Does this require Python 3.12 or is 3.10 supported as well?", "label": "neutral"},
    {"text": "What microphone are you using for this recording?", "label": "neutral"},
    {"text": "The GitHub repo link mentioned in the video is in the description.", "label": "neutral"},
    {"text": "Video duration: 12 minutes and 34 seconds.", "label": "neutral"},
    {"text": "Watching this in 2026, let's see how much has changed.", "label": "neutral"},
    {"text": "Can you make a follow-up video covering the database migration part?", "label": "neutral"},
]


def load_dataset(file_path: Optional[str] = None) -> List[Dict[str, str]]:
    """Load benchmark dataset from CSV/JSON or use built-in curated ground-truth set."""
    if not file_path or not os.path.exists(file_path):
        logger.info(
            f"Using built-in curated ground-truth dataset ({len(DEFAULT_BENCHMARK_DATA)} samples)."
        )
        return DEFAULT_BENCHMARK_DATA

    data: List[Dict[str, str]] = []
    if file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            if isinstance(raw, list):
                data = raw
    elif file_path.endswith(".csv"):
        import csv
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                text = row.get("text") or row.get("comment") or row.get("sentence") or ""
                label = row.get("label") or row.get("sentiment") or ""
                if text and label in LABELS:
                    data.append({"text": text, "label": label.lower().strip()})

    logger.info(f"Loaded {len(data)} samples from {file_path}")
    return data if data else DEFAULT_BENCHMARK_DATA


def evaluate_predictions(
    ground_truth: List[str], predictions: List[str], labels: List[str] = LABELS
) -> Dict[str, Any]:
    """Calculate comprehensive classification metrics against ground truth."""
    acc = accuracy_score(ground_truth, predictions)
    macro_f1 = f1_score(ground_truth, predictions, labels=labels, average="macro", zero_division=0)
    weighted_f1 = f1_score(ground_truth, predictions, labels=labels, average="weighted", zero_division=0)
    macro_prec = precision_score(ground_truth, predictions, labels=labels, average="macro", zero_division=0)
    macro_rec = recall_score(ground_truth, predictions, labels=labels, average="macro", zero_division=0)

    # Per class metrics
    rep = classification_report(ground_truth, predictions, labels=labels, output_dict=True, zero_division=0)
    cm = confusion_matrix(ground_truth, predictions, labels=labels).tolist()

    return {
        "accuracy": float(acc),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
        "macro_precision": float(macro_prec),
        "macro_recall": float(macro_rec),
        "per_class": {lbl: rep.get(lbl, {}) for lbl in labels},
        "confusion_matrix": cm,
        "labels_order": labels,
    }


def run_benchmark(
    dataset: List[Dict[str, str]],
    run_xlmr: bool = True,
    run_gemini: bool = True,
    gemini_batch_size: int = 20,
) -> Dict[str, Any]:
    """
    Run full offline benchmark:
    - Ground Truth vs XLM-RoBERTa
    - Ground Truth vs Gemini 2.5 Flash-Lite
    - Gemini vs XLM-RoBERTa Agreement & Cohen's Kappa
    """
    texts = [item["text"] for item in dataset]
    ground_truth = [item["label"] for item in dataset]
    n_samples = len(texts)

    results: Dict[str, Any] = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "sample_count": n_samples,
            "labels": LABELS,
        },
        "models": {},
        "comparative": {},
    }

    xlmr_preds: Optional[List[str]] = None
    gemini_preds: Optional[List[str]] = None

    try:
        import psutil
        process = psutil.Process()
        def _get_rss_mb():
            return process.memory_info().rss / (1024 * 1024)
    except Exception:
        def _get_rss_mb():
            return None

    # ── 1. Benchmark XLM-RoBERTa (Local PyTorch) ─────────────────────────────
    if run_xlmr:
        logger.info("\n" + "=" * 60)
        logger.info("EVALUATING MODEL: XLM-RoBERTa (Local PyTorch)")
        logger.info("=" * 60)
        try:
            settings = get_settings()
            mem_before = _get_rss_mb()
            xlmr_service = XLMRoBERTaSentimentService(
                model_dir=settings.MODEL_DIR,
                neutral_threshold=settings.NEUTRAL_THRESHOLD,
            )

            start_t = time.perf_counter()
            pred_dicts = xlmr_service.predict(texts)
            elapsed = time.perf_counter() - start_t
            mem_after = _get_rss_mb()

            xlmr_preds = [p["label"] for p in pred_dicts]
            xlmr_metrics = evaluate_predictions(ground_truth, xlmr_preds)
            xlmr_metrics["timing"] = {
                "total_seconds": round(elapsed, 3),
                "latency_per_sample_ms": round((elapsed / n_samples) * 1000, 2),
                "throughput_samples_per_sec": round(n_samples / max(0.001, elapsed), 2),
            }
            if mem_before is not None and mem_after is not None:
                xlmr_metrics["memory"] = {
                    "initial_rss_mb": round(mem_before, 2),
                    "peak_rss_mb": round(mem_after, 2),
                    "rss_delta_mb": round(max(0.0, mem_after - mem_before), 2),
                }
            results["models"]["xlmr-sentiment"] = xlmr_metrics
            logger.info(
                f"XLM-RoBERTa -> Accuracy: {xlmr_metrics['accuracy']:.2%}, "
                f"Macro F1: {xlmr_metrics['macro_f1']:.2%}, "
                f"Time: {elapsed:.2f}s, Peak RSS: {mem_after or 0.0:.1f} MB"
            )
        except Exception as e:
            logger.error(f"XLM-RoBERTa evaluation failed: {e}", exc_info=True)
            results["models"]["xlmr-sentiment"] = {"error": str(e)}

    # ── 2. Benchmark Gemini 2.5 Flash-Lite (Batch API) ───────────────────────
    if run_gemini:
        logger.info("\n" + "=" * 60)
        logger.info(f"EVALUATING MODEL: Gemini 2.5 Flash-Lite (Batch size = {gemini_batch_size})")
        logger.info("=" * 60)
        try:
            settings = get_settings()
            mem_before_gem = _get_rss_mb()
            gemini_service = GeminiSentimentService(
                api_key=settings.GEMINI_API_KEY,
                model_name=settings.GEMINI_MODEL or "gemini-2.5-flash-lite",
                batch_size=gemini_batch_size,
            )

            start_t = time.perf_counter()
            pred_dicts = gemini_service.predict(texts)
            elapsed = time.perf_counter() - start_t
            mem_after_gem = _get_rss_mb()

            gemini_preds = [p["label"] for p in pred_dicts]
            gemini_metrics = evaluate_predictions(ground_truth, gemini_preds)
            total_batches = (n_samples + gemini_batch_size - 1) // gemini_batch_size
            gemini_metrics["timing"] = {
                "total_seconds": round(elapsed, 3),
                "latency_per_sample_ms": round((elapsed / n_samples) * 1000, 2),
                "throughput_samples_per_sec": round(n_samples / max(0.001, elapsed), 2),
                "batch_size": gemini_batch_size,
                "total_api_requests": total_batches,
            }
            if mem_before_gem is not None and mem_after_gem is not None:
                gemini_metrics["memory"] = {
                    "initial_rss_mb": round(mem_before_gem, 2),
                    "peak_rss_mb": round(mem_after_gem, 2),
                    "rss_delta_mb": round(max(0.0, mem_after_gem - mem_before_gem), 2),
                }
            results["models"]["gemini-2.5-flash-lite"] = gemini_metrics
            logger.info(
                f"Gemini 2.5 Flash-Lite -> Accuracy: {gemini_metrics['accuracy']:.2%}, "
                f"Macro F1: {gemini_metrics['macro_f1']:.2%}, "
                f"Time: {elapsed:.2f}s, Peak RSS: {mem_after_gem or 0.0:.1f} MB"
            )
        except Exception as e:
            logger.error(f"Gemini 2.5 Flash-Lite evaluation failed: {e}", exc_info=True)
            results["models"]["gemini-2.5-flash-lite"] = {"error": str(e)}

    # ── 3. Inter-Model Agreement (Gemini vs XLM-RoBERTa) ──────────────────────
    if xlmr_preds and gemini_preds and len(xlmr_preds) == len(gemini_preds):
        agreement_count = sum(1 for x, g in zip(xlmr_preds, gemini_preds) if x == g)
        agreement_rate = agreement_count / len(xlmr_preds)
        kappa = cohen_kappa_score(xlmr_preds, gemini_preds, labels=LABELS)
        cross_cm = confusion_matrix(xlmr_preds, gemini_preds, labels=LABELS).tolist()

        results["comparative"]["gemini_vs_xlmr"] = {
            "agreement_rate": float(agreement_rate),
            "agreement_count": agreement_count,
            "total_samples": len(xlmr_preds),
            "cohens_kappa": float(kappa),
            "cross_confusion_matrix": cross_cm,
            "matrix_format": "Rows = XLM-RoBERTa, Columns = Gemini 2.5 Flash-Lite",
        }
        logger.info(
            f"🤝 Agreement Rate (Gemini vs XLM-R): {agreement_rate:.2%} | "
            f"Cohen's Kappa: {kappa:.3f}"
        )

    return results


def print_formatted_report(res: Dict[str, Any]):
    """Print clean terminal report comparing Ground Truth vs Models."""
    print("\n" + "=" * 75)
    print("SOCIAL SENTIMENT OFFLINE BENCHMARK REPORT")
    print("=" * 75)
    print(f"Timestamp: {res['metadata']['timestamp']} | Total Ground-Truth Samples: {res['metadata']['sample_count']}")
    print("-" * 75)

    headers = f"{'Metric':<25} | {'XLM-RoBERTa (Local)':<22} | {'Gemini 2.5 Flash-Lite':<22}"
    print(headers)
    print("-" * 75)

    m_xlmr = res["models"].get("xlmr-sentiment", {})
    m_gem = res["models"].get("gemini-2.5-flash-lite", {})

    def _fmt(val, is_pct=True):
        if val is None or isinstance(val, str):
            return str(val) if val else "N/A"
        return f"{val:.2%}" if is_pct else f"{val:.4f}"

    print(f"{'Accuracy':<25} | {_fmt(m_xlmr.get('accuracy')):<22} | {_fmt(m_gem.get('accuracy')):<22}")
    print(f"{'Macro F1-Score':<25} | {_fmt(m_xlmr.get('macro_f1')):<22} | {_fmt(m_gem.get('macro_f1')):<22}")
    print(f"{'Weighted F1-Score':<25} | {_fmt(m_xlmr.get('weighted_f1')):<22} | {_fmt(m_gem.get('weighted_f1')):<22}")
    print(f"{'Macro Precision':<25} | {_fmt(m_xlmr.get('macro_precision')):<22} | {_fmt(m_gem.get('macro_precision')):<22}")
    print(f"{'Macro Recall':<25} | {_fmt(m_xlmr.get('macro_recall')):<22} | {_fmt(m_gem.get('macro_recall')):<22}")
    print("-" * 75)

    # Per class F1
    for lbl in LABELS:
        f1_x = m_xlmr.get("per_class", {}).get(lbl, {}).get("f1-score")
        f1_g = m_gem.get("per_class", {}).get(lbl, {}).get("f1-score")
        print(f"{'F1-Score (' + lbl + ')':<25} | {_fmt(f1_x):<22} | {_fmt(f1_g):<22}")

    print("-" * 75)
    t_x = m_xlmr.get("timing", {})
    t_g = m_gem.get("timing", {})
    mem_x = m_xlmr.get("memory", {})
    mem_g = m_gem.get("memory", {})
    print(f"{'Total Inference Time':<25} | {str(t_x.get('total_seconds', 'N/A')) + 's':<22} | {str(t_g.get('total_seconds', 'N/A')) + 's':<22}")
    print(f"{'Throughput':<25} | {str(t_x.get('throughput_samples_per_sec', 'N/A')) + ' samples/s':<22} | {str(t_g.get('throughput_samples_per_sec', 'N/A')) + ' samples/s':<22}")
    print(f"{'Peak RSS Memory':<25} | {str(mem_x.get('peak_rss_mb', 'N/A')) + ' MB':<22} | {str(mem_g.get('peak_rss_mb', 'N/A')) + ' MB':<22}")
    print(f"{'RAM Delta':<25} | {'+' + str(mem_x.get('rss_delta_mb', 'N/A')) + ' MB':<22} | {'+' + str(mem_g.get('rss_delta_mb', 'N/A')) + ' MB':<22}")
    print(f"{'API Requests':<25} | {'0 (Local)':<22} | {str(t_g.get('total_api_requests', 'N/A')) + ' reqs':<22}")
    print("-" * 75)

    comp = res.get("comparative", {}).get("gemini_vs_xlmr", {})
    if comp:
        print(f"Inter-Model Agreement Rate : {comp.get('agreement_rate', 0.0):.2%}")
        print(f"Cohen's Kappa Coefficient  : {comp.get('cohens_kappa', 0.0):.3f}")
    print("=" * 75 + "\n")


def save_reports(res: Dict[str, Any], output_dir: str = "artifacts"):
    """Save benchmark results as JSON and Markdown report."""
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "benchmark_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    logger.info(f"Saved JSON benchmark results to: {json_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Social Sentiment Ground-Truth Offline Benchmark")
    parser.add_argument("--dataset", type=str, default=None, help="Path to ground-truth CSV/JSON dataset")
    parser.add_argument("--gemini-batch-size", type=int, default=20, help="Batch size for Gemini API (e.g. 10, 20, 30, 50)")
    parser.add_argument("--skip-xlmr", action="store_true", help="Skip XLM-RoBERTa benchmark")
    parser.add_argument("--skip-gemini", action="store_true", help="Skip Gemini benchmark")
    args = parser.parse_args()

    ds = load_dataset(args.dataset)
    results = run_benchmark(
        dataset=ds,
        run_xlmr=not args.skip_xlmr,
        run_gemini=not args.skip_gemini,
        gemini_batch_size=args.gemini_batch_size,
    )
    print_formatted_report(results)
    save_reports(results)
