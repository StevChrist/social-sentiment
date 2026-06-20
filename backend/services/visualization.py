# backend/services/visualization.py - COMPLETE VISUALIZATION SERVICE
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend, must be set before importing pyplot

import matplotlib.pyplot as plt
import numpy as np
from wordcloud import WordCloud, STOPWORDS
import base64
from io import BytesIO
import re
import logging
from typing import List, Dict, Optional, Any
from collections import Counter

logger = logging.getLogger(__name__)

# ─── Stopwords gabungan Indonesia + English ───────────────────────────────────
_STOPWORDS_ID = {
    "yang", "dan", "di", "ke", "dari", "dengan", "untuk", "pada", "adalah",
    "itu", "ini", "atau", "tidak", "ada", "akan", "sudah", "bisa", "juga",
    "saya", "kamu", "dia", "kami", "mereka", "kita", "nya", "ya", "iya",
    "oh", "ah", "eh", "lah", "deh", "nih", "sih", "dong", "kan", "aja",
    "jadi", "juga", "kalau", "karena", "tapi", "namun", "tetapi", "seperti",
    "dalam", "oleh", "atas", "bawah", "lebih", "sangat", "banget", "sekali",
    "semua", "banyak", "satu", "dua", "punya", "buat", "sama", "mau", "mau",
    "lagi", "masih", "udah", "udah", "terus", "nggak", "gak", "ga", "ngga",
    "gimana", "kok", "apakah", "bagaimana", "kapan", "dimana", "siapa", "apa",
    "nya", "mu", "ku", "kah", "lah", "pun", "pula", "bahwa", "agar", "supaya",
    "ketika", "saat", "sedang", "sudah", "pernah", "belum", "hanya", "saja",
    "setelah", "sebelum", "selama", "antara", "melalui", "terhadap", "tentang",
    "video", "channel", "subscribe", "like", "komentar", "konten", "viewer",
    "nonton", "tonton", "lihat", "liat", "dilihat",
}

_STOPWORDS_EN = set(STOPWORDS) | {
    "video", "channel", "subscribe", "like", "comment", "watch", "watching",
    "please", "really", "actually", "just", "also", "still", "even", "much",
    "many", "every", "would", "could", "should", "always", "never", "already",
    "https", "http", "www", "com", "youtube", "youtu",
}

ALL_STOPWORDS = _STOPWORDS_ID | _STOPWORDS_EN

# Dark-themed color palette consistent with frontend
_DARK_BG = "#1A1F2E"
_COLORS = {
    "positive": "#10B981",   # emerald-500
    "neutral": "#F59E0B",    # amber-500
    "negative": "#EF4444",   # red-500
}
_TEXT_COLOR = "#E5E7EB"
_GRID_COLOR = "rgba(255,255,255,0.08)"


def _fig_to_base64(fig: plt.Figure) -> str:
    """Convert a matplotlib figure to a base64-encoded PNG data URL."""
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110,
                facecolor=fig.get_facecolor())
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    buf.close()
    return f"data:image/png;base64,{encoded}"


def _clean_texts(texts: List[str]) -> List[str]:
    """Basic cleanup: remove URLs, special chars, short tokens."""
    cleaned = []
    for t in texts:
        t = re.sub(r"https?://\S+|www\.\S+", " ", t)
        t = re.sub(r"[^\w\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            cleaned.append(t)
    return cleaned


class VisualizationService:
    """Service for generating all visualizations from analyzed comments."""

    def __init__(self):
        plt.ioff()

    # ─── Word Cloud ──────────────────────────────────────────────────────────

    def generate_wordcloud(self, texts: List[str]) -> Optional[str]:
        """Generate a word cloud from comment texts. Returns base64 PNG data URL."""
        try:
            cleaned = _clean_texts(texts)
            if not cleaned:
                return None

            combined = " ".join(cleaned)
            if not combined.strip():
                return None

            wc = WordCloud(
                width=700,
                height=600,
                background_color="#1A1F2E",
                max_words=120,
                colormap="cool",
                stopwords=ALL_STOPWORDS,
                collocations=False,
                min_font_size=10,
                relative_scaling=0.5,
            ).generate(combined)

            fig, ax = plt.subplots(figsize=(7, 6))
            fig.patch.set_facecolor(_DARK_BG)
            ax.set_facecolor(_DARK_BG)
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            ax.set_title("Most Frequent Words", color=_TEXT_COLOR,
                         fontsize=14, pad=12, fontweight="bold")
            return _fig_to_base64(fig)

        except Exception as e:
            logger.error(f"Word cloud generation failed: {e}")
            return None

    # ─── Pie Chart ───────────────────────────────────────────────────────────

    def generate_pie_chart(self, counts: Dict[str, int]) -> Optional[str]:
        """Generate a dark-themed sentiment pie chart. Returns base64 PNG."""
        try:
            total = sum(counts.values())
            if total == 0:
                return None

            order = ["positive", "neutral", "negative"]
            labels = []
            sizes = []
            colors = []

            for key in order:
                v = counts.get(key, 0)
                if v > 0:
                    labels.append(key.capitalize())
                    sizes.append(v)
                    colors.append(_COLORS[key])

            if not sizes:
                return None

            fig, ax = plt.subplots(figsize=(7, 6))
            fig.patch.set_facecolor(_DARK_BG)
            ax.set_facecolor(_DARK_BG)

            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                colors=colors,
                autopct="%1.1f%%",
                startangle=140,
                pctdistance=0.78,
                textprops={"color": _TEXT_COLOR, "fontsize": 11},
                wedgeprops={"edgecolor": _DARK_BG, "linewidth": 2},
            )
            for at in autotexts:
                at.set_color(_DARK_BG)
                at.set_fontweight("bold")

            ax.set_title("Sentiment Distribution", color=_TEXT_COLOR,
                         fontsize=14, pad=16, fontweight="bold")
            return _fig_to_base64(fig)

        except Exception as e:
            logger.error(f"Pie chart generation failed: {e}")
            return None

    # ─── Bar Chart ───────────────────────────────────────────────────────────

    def generate_bar_chart(self, counts: Dict[str, int]) -> Optional[str]:
        """Generate a dark-themed sentiment bar chart. Returns base64 PNG."""
        try:
            total = sum(counts.values())
            if total == 0:
                return None

            sentiments = ["Positive", "Neutral", "Negative"]
            values = [
                counts.get("positive", 0),
                counts.get("neutral", 0),
                counts.get("negative", 0),
            ]
            colors = [_COLORS["positive"], _COLORS["neutral"], _COLORS["negative"]]

            fig, ax = plt.subplots(figsize=(8, 5))
            fig.patch.set_facecolor(_DARK_BG)
            ax.set_facecolor(_DARK_BG)

            bars = ax.bar(sentiments, values, color=colors,
                          edgecolor=_DARK_BG, linewidth=0.8,
                          width=0.55, zorder=3)

            # Value labels on bars
            for bar, val in zip(bars, values):
                if val > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        bar.get_height() + total * 0.01,
                        f"{val:,}",
                        ha="center", va="bottom",
                        color=_TEXT_COLOR, fontsize=11, fontweight="bold",
                    )

            ax.set_title("Sentiment Analysis Results", color=_TEXT_COLOR,
                         fontsize=14, pad=14, fontweight="bold")
            ax.set_ylabel("Number of Comments", color=_TEXT_COLOR, fontsize=11)
            ax.tick_params(colors=_TEXT_COLOR, labelsize=11)
            for spine in ax.spines.values():
                spine.set_color((1.0, 1.0, 1.0, 0.1))
            ax.set_ylim(0, max(values) * 1.2 if max(values) > 0 else 1)
            ax.yaxis.grid(True, color="#2E3550", linewidth=0.6, zorder=0)
            ax.set_axisbelow(True)

            # Percentage labels below bar names
            pcts = [v / total * 100 if total else 0 for v in values]
            tick_labels = [f"{s}\n{p:.1f}%" for s, p in zip(sentiments, pcts)]
            ax.set_xticklabels(tick_labels, color=_TEXT_COLOR)

            fig.tight_layout()
            return _fig_to_base64(fig)

        except Exception as e:
            logger.error(f"Bar chart generation failed: {e}")
            return None

    # ─── Top Keywords ─────────────────────────────────────────────────────────

    def generate_top_keywords(
        self,
        texts: List[str],
        top_n: int = 20,
    ) -> List[Dict[str, Any]]:
        """Extract the top N keywords from comment texts, excluding stopwords."""
        try:
            cleaned = _clean_texts(texts)
            if not cleaned:
                return []

            all_words: List[str] = []
            for text in cleaned:
                words = text.lower().split()
                for word in words:
                    word = word.strip()
                    if (
                        len(word) > 2
                        and word not in ALL_STOPWORDS
                        and not word.isdigit()
                    ):
                        all_words.append(word)

            counter = Counter(all_words)
            return [
                {"word": word, "frequency": freq}
                for word, freq in counter.most_common(top_n)
            ]

        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []

    # ─── Convenience: generate all at once ───────────────────────────────────

    def generate_all(
        self,
        texts: List[str],
        counts: Dict[str, int],
    ) -> Dict[str, Any]:
        """Generate all visualizations and return as a dict."""
        return {
            "wordcloud_base64": self.generate_wordcloud(texts),
            "pie_chart_base64": self.generate_pie_chart(counts),
            "bar_chart_base64": self.generate_bar_chart(counts),
            "top_keywords": self.generate_top_keywords(texts),
        }
