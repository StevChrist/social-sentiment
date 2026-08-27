<div align="center">

# 🎯 SocialSentiment

**AI-powered YouTube Comment Sentiment Analysis**

[![Website](https://img.shields.io/badge/Website-Live-22C55E?style=for-the-badge&logo=google-chrome&logoColor=white)](https://social-sentiment.stevchrist.site)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)

🔗 **Live Website:** [https://social-sentiment.stevchrist.site](https://social-sentiment.stevchrist.site)

</div>

---

## 📖 Description

**SocialSentiment** is an AI-powered web application that analyzes the sentiment of YouTube video comments in real time. By simply pasting a YouTube video URL, the platform automatically fetches public comments and classifies each one as **Positive**, **Neutral**, or **Negative** using Google's **Gemini 2.5 Flash-Lite** model in production via batch processing and structured JSON schemas. The platform also preserves a fine-tuned **XLM-RoBERTa** multilingual deep learning model for offline research and evaluation benchmarks. Results are presented through interactive visualizations — including a Word Cloud, Pie Chart, and Bar Chart — along with a downloadable CSV report.

---

## 🛠️ Programming Languages & Technologies

### Backend
| Technology | Description |
|---|---|
| **Python 3.12+** | Core backend language |
| **FastAPI** | REST API framework with SSE streaming |
| **Google Gemini 2.5 Flash-Lite** | Production AI sentiment engine (Free Tier with batching) |
| **Google GenAI SDK** | Structured JSON output classification |
| **XLM-RoBERTa (PyTorch)** | Multilingual model for offline evaluation & benchmarks |
| **SQLAlchemy + PostgreSQL** | Database ORM and quota/result storage |
| **Matplotlib + WordCloud** | Server-side chart and word cloud generation |
| **Docker Compose** | PostgreSQL containerization |
| **Uvicorn** | ASGI server |

### Frontend
| Technology | Description |
|---|---|
| **Next.js 15 (App Router)** | React framework for the web UI |
| **TypeScript** | Type-safe frontend development |
| **Vanilla CSS** | Custom dark-themed glassmorphism styling |
| **Server-Sent Events (SSE)** | Real-time analysis progress streaming |
| **Axios** | HTTP client for API calls |
| **React Toastify** | Toast notification system |

---

## 🚀 How to Use the Website

### Step 1 — Open the Website
Visit 👉 [https://social-sentiment.stevchrist.site](https://social-sentiment.stevchrist.site)

### Step 2 — Paste a YouTube URL
In the **"Try the Social Sentiment"** section, paste any YouTube video URL into the input box.

> ✅ Supported formats:
> - `https://www.youtube.com/watch?v=VIDEO_ID`
> - `https://youtu.be/VIDEO_ID`
> - Direct Video ID: `dQw4w9WgXcQ`

### Step 3 — Choose Analysis Depth
Select how many comments you want to analyze:

| Option | Description |
|---|---|
| **25%** | Quick — Up to 250 comments |
| **50%** | Balanced — Up to 500 comments *(recommended)* |
| **75%** | Deep — Up to 750 comments |
| **100%** | Full — Capped at 1,000 comments max |

### Step 4 — Click Analyze
Click the **"Analyze"** button. A live progress indicator will show each stage:
1. 📥 Fetching comments from YouTube
2. 🤖 Running comments through the XLM-RoBERTa AI model
3. 🎨 Generating visualizations
4. ✅ Completing results

### Step 5 — View Results
Once complete, you'll see:
- 📊 **Sentiment Statistics** — Positive / Neutral / Negative counts and percentages
- 🌟 **Word Cloud** — Most frequent words in the comments
- 🥧 **Sentiment Distribution Pie Chart**
- 📊 **Comment Counts Bar Chart**
- 🏷️ **Top Keywords** extracted from comments
- 💬 **Sample Comments** from each sentiment category
- 🤖 **Model Performance** — Validation Accuracy: 83.3% | Macro F1: 82.3%

### Step 6 — Download CSV (Optional)
Click **"⬇ Download CSV"** to export all analyzed comments with their sentiment labels, confidence scores, and metadata.

---

## 🔐 API Credits & Limits

To prevent server overload, the system enforces daily usage limits:

| Limit | Value |
|---|---|
| **Daily Credits** | 100 units/day |
| **Max Comments per Analysis** | 1,000 comments |
| **Reset Time** | Midnight (Pacific Time) |

The **API Credits** card on the website updates in real time and shows your remaining quota.

---

## ℹ️ About & Architecture
 
**SocialSentiment** combines cutting-edge Large Language Models with modern full-stack web development:
- ⚡ **Production Engine:** Uses Google Gemini 2.5 Flash-Lite Free Tier with dual-constraint batching, delivering fast analysis with minimal server memory footprint (<250MB RAM).
- 🔬 **Offline Benchmark Suite:** Evaluates Gemini 2.5 Flash-Lite against fine-tuned XLM-RoBERTa on ground-truth datasets with metrics for Accuracy, Macro F1, Confusion Matrices, Cohen's Kappa, and throughput.
 
### Running Offline Benchmarks
```bash
# Run benchmark comparing Ground Truth vs XLM-RoBERTa and Gemini
python -m backend.scripts.benchmark_sentiment

# Or run with a custom CSV dataset
python -m backend.scripts.benchmark_sentiment --dataset path/to/dataset.csv --gemini-batch-size 20
```
 
---
 
## 🙏 Credits
 
| Resource | Usage |
|---|---|
| [Google Gemini 2.5 Flash-Lite](https://ai.google.dev/) | Production sentiment classification model |
| [Google GenAI SDK](https://github.com/google-gemini/google-genai) | Structured output inference client |
| [XLM-RoBERTa (Facebook AI)](https://huggingface.co/FacebookAI/xlm-roberta-base) | Base multilingual transformer model for offline research |
| [HuggingFace Transformers](https://huggingface.co/docs/transformers) | Model loading and inference pipeline |
| [YouTube Data API v3](https://developers.google.com/youtube/v3) | Fetching video comments |
| [FastAPI](https://fastapi.tiangolo.com/) | High-performance Python API framework |
| [Next.js](https://nextjs.org/) | React web framework |
| [Matplotlib](https://matplotlib.org/) | Chart generation |
| [WordCloud](https://github.com/amueller/word_cloud) | Word cloud generation |
 
---
 
<div align="center">
 
**StevChrist**
 
</div>
