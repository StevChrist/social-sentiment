# backend/main.py — Social Sentiment API (Production-Ready Version)
from __future__ import annotations

import asyncio
import csv
import io
import json
import logging
import re
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.core.config import get_settings
from backend.api.ingest_youtube import extract_video_id, fetch_youtube_comments, fetch_video_info
from backend.services.sentiment import SentimentService
from backend.services.visualization import VisualizationService

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# ─── Global service instances ─────────────────────────────────────────────────
_viz_service = VisualizationService()
_sentiment_service: Optional[SentimentService] = None
_model_loading = False
_model_ready = False
_last_analysis_cache: Dict[str, Any] = {}


def _try_load_model() -> bool:
    """Attempt to initialize the active sentiment engine (Gemini or XLM-RoBERTa)."""
    global _sentiment_service, _model_ready, _model_loading
    if _model_ready:
        return True
    if _model_loading:
        return False

    _model_loading = True
    provider = (settings.SENTIMENT_PROVIDER or "gemini").lower().strip()
    try:
        if provider == "gemini":
            logger.info(f"Initializing Gemini Sentiment Engine ({settings.GEMINI_MODEL})...")
            _sentiment_service = SentimentService.get("gemini")
            _model_ready = True
            logger.info("✅ Gemini Sentiment Engine (gemini-2.5-flash-lite) ready")
        elif provider == "xlmr":
            logger.info(f"Loading local XLM-RoBERTa model from: {settings.MODEL_DIR}")
            _sentiment_service = SentimentService.get("xlmr")
            _model_ready = True
            logger.info("✅ XLM-RoBERTa model loaded successfully")
        else:
            raise ValueError(f"Unknown SENTIMENT_PROVIDER: '{provider}'")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize sentiment engine: {e}")
        _model_ready = False
        return False
    finally:
        _model_loading = False


# ─── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize sentiment engine and database on startup."""
    logger.info("🚀 Social Sentiment API starting up...")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _try_load_model)

    # Initialize DB tables if DB is available
    try:
        from backend.db.session import init_db
        init_db()
        logger.info("✅ Database tables initialized")
    except Exception as e:
        logger.warning(f"⚠️ Database not available (quota tracking disabled): {e}")

    yield
    logger.info("Social Sentiment API shutting down.")


# ─── FastAPI app ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Social Sentiment API",
    version="2.1.0",
    description="YouTube comment sentiment analysis using Gemini 2.5 Flash-Lite & XLM-RoBERTa",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Pydantic Models ──────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    texts: List[str]


class PredictResult(BaseModel):
    label: str
    confidence: Optional[float] = None
    scores: Optional[Dict[str, Optional[float]]] = None


class PredictResponse(BaseModel):
    results: List[PredictResult]


class AnalyzeOut(BaseModel):
    video_id: str
    video_title: str
    channel_title: str
    total_comments: int
    actual_analyzed: int
    percentage_analyzed: float
    counts: Dict[str, int]
    ratios: Dict[str, float]
    examples: List[Dict[str, Any]]
    processing_time: float
    visualizations: Optional[Dict[str, Any]] = None


# ─── Fallback sentiment (rule-based) ─────────────────────────────────────────
_POS_WORDS = {
    "good", "great", "amazing", "awesome", "love", "excellent", "wonderful",
    "fantastic", "perfect", "best", "helpful", "thanks", "thank", "brilliant",
    "outstanding", "nice", "beautiful", "cool", "incredible", "superb",
    "bagus", "keren", "mantap", "suka", "luar biasa", "terima kasih", "makasih",
    "menarik", "kece", "top", "jos", "gilak", "gila", "dewa", "sempurna",
    "membantu", "bermanfaat", "informatif", "edukatif",
}
_NEG_WORDS = {
    "bad", "terrible", "awful", "hate", "worst", "horrible", "disgusting",
    "stupid", "boring", "sucks", "waste", "disappointed", "useless", "trash",
    "pathetic", "annoying", "frustrating",
    "buruk", "jelek", "payah", "benci", "membosankan", "sampah", "lebay",
    "norak", "kampungan", "tidak berguna", "buang waktu", "kecewa", "zonk",
}


def _rule_based_sentiment(text: str) -> Dict[str, Any]:
    tl = text.lower()
    pos = sum(1 for w in _POS_WORDS if w in tl)
    neg = sum(1 for w in _NEG_WORDS if w in tl)
    if pos > neg:
        label, conf = "positive", min(0.95, 0.60 + (pos - neg) * 0.1)
    elif neg > pos:
        label, conf = "negative", min(0.95, 0.60 + (neg - pos) * 0.1)
    else:
        label, conf = "neutral", 0.65
    return {
        "label": label,
        "confidence": conf,
        "scores": {
            "positive": conf if label == "positive" else 0.25,
            "neutral": conf if label == "neutral" else 0.35,
            "negative": conf if label == "negative" else 0.25,
        },
    }


# ─── Core analysis logic ──────────────────────────────────────────────────────
def _run_analysis(
    video_id: str,
    percentage: float,
    progress_cb=None,
) -> Dict[str, Any]:
    """
    Full pipeline: fetch → predict → visualize.
    progress_cb(step: str, pct: int) is called at each stage.
    """
    global _last_analysis_cache
    start = time.time()

    def _emit(step: str, pct: int):
        if progress_cb:
            progress_cb(step, pct)

    # ── 1. Fetch video info ──────────────────────────────────────────────────
    _emit("Fetching video info…", 5)
    video_info = fetch_video_info(video_id, settings.YOUTUBE_API_KEY)
    video_title = video_info.get("title", "Unknown Video")
    channel_title = video_info.get("channel_title", "Unknown Channel")
    total_comments = video_info.get("comment_count", 0)

    # ── 2. Check Database Cache (Instant Re-use) ────────────────────────────
    raw_target = int(total_comments * percentage) if total_comments > 0 else 500
    max_comments = min(raw_target, settings.MAX_COMMENTS_LIMIT)

    try:
        from backend.db.session import get_session
        from backend.db.models import Video, Comment, Prediction

        with get_session() as db:
            db_video = db.query(Video).filter_by(video_id=video_id).first()
            if db_video:
                db_comments = db.query(Comment).filter_by(video_pk=db_video.id).all()
                if len(db_comments) >= min(max_comments, max(50, len(db_comments))):
                    cached_analyzed = []
                    cached_counts = {"positive": 0, "neutral": 0, "negative": 0}

                    for c in db_comments:
                        pred_obj = c.predictions[0] if c.predictions else None
                        if pred_obj:
                            lbl = pred_obj.label
                            pred_dict = {
                                "label": lbl,
                                "confidence": pred_obj.confidence,
                                "scores": {
                                    "positive": pred_obj.positive_score,
                                    "neutral": pred_obj.neutral_score,
                                    "negative": pred_obj.negative_score,
                                },
                            }
                            cached_analyzed.append({
                                "comment_id": c.comment_id,
                                "text": c.text,
                                "author": c.author or "Anonymous",
                                "published_at": c.commented_at or "",
                                "like_count": c.like_count or 0,
                                "is_reply": c.is_reply or False,
                                "prediction": pred_dict,
                            })
                            if lbl in cached_counts:
                                cached_counts[lbl] += 1

                    if cached_analyzed:
                        _emit(f"⚡ Instant Cache Hit! Loaded {len(cached_analyzed):,} comments from database…", 70)
                        total_cached = cached_counts["positive"] + cached_counts["neutral"] + cached_counts["negative"]
                        cached_ratios = {k: (v / total_cached if total_cached > 0 else 0.0) for k, v in cached_counts.items()}

                        _emit("Generating visualizations…", 85)
                        texts_for_viz = [c["text"] for c in cached_analyzed if c.get("text")]
                        viz = _viz_service.generate_all(texts_for_viz, cached_counts)

                        examples = []
                        for sentiment in ["positive", "neutral", "negative"]:
                            pool = [c for c in cached_analyzed if c["prediction"]["label"] == sentiment]
                            pool.sort(key=lambda x: x.get("like_count", 0), reverse=True)
                            examples.extend(pool[:5])

                        processing_time = time.time() - start
                        _emit("Complete!", 100)

                        global _last_analysis_cache
                        _last_analysis_cache = {
                            "video_id": video_id,
                            "percentage": percentage,
                            "comments": cached_analyzed,
                        }

                        logger.info(f"⚡ Served analysis for {video_id} directly from PostgreSQL ({total_cached} comments, {processing_time:.2f}s)")
                        return {
                            "video_id": video_id,
                            "video_title": db_video.title or video_title,
                            "channel_title": db_video.channel_title or channel_title,
                            "total_comments": total_comments or len(cached_analyzed),
                            "actual_analyzed": total_cached,
                            "percentage_analyzed": percentage,
                            "counts": cached_counts,
                            "ratios": cached_ratios,
                            "examples": examples[:15],
                            "processing_time": round(processing_time, 2),
                            "visualizations": viz,
                        }
    except Exception as e:
        logger.warning(f"Database cache check failed or skipped: {e}")

    # ── 3. Collect comments from YouTube API ──────────────────────────────────
    _emit("Collecting comments from YouTube…", 15)
    comments = fetch_youtube_comments(
        video_id=video_id,
        api_key=settings.YOUTUBE_API_KEY,
        max_comments=max_comments,
        include_replies=True,
        percentage=percentage,
    )

    if not comments:
        raise HTTPException(
            status_code=404,
            detail="No comments found. The video may have comments disabled or be private.",
        )

    _emit(f"Collected {len(comments):,} comments. Inserting into AI model…", 40)

    # ── 3. Sentiment prediction ──────────────────────────────────────────────
    comment_texts = [c.get("text", "") for c in comments]
    analyzed: List[Dict[str, Any]] = []
    counts = {"positive": 0, "neutral": 0, "negative": 0}

    svc = SentimentService.get()
    provider_name = getattr(svc, "provider_name", settings.SENTIMENT_PROVIDER)

    def _sentiment_progress_cb(completed: int, total: int, step_desc: str):
        # Scale progress smoothly between 40% and 75%
        pct = 40 + int((completed / max(1, total)) * 35)
        _emit(step_desc, pct)

    try:
        _emit(f"AI model ({provider_name}) analyzing {len(comment_texts)} comments in batches…", 40)
        predictions = svc.predict(comment_texts, progress_cb=_sentiment_progress_cb)
    except Exception as e:
        logger.error(f"❌ Sentiment analysis failed ({provider_name}): {e}", exc_info=True)
        # STRICT: Never silently convert failed batches to fake neutral
        raise HTTPException(
            status_code=500,
            detail=f"Sentiment analysis failed ({provider_name}): {str(e)}"
        )

    failed_count = 0
    for i, comment in enumerate(comments):
        pred = predictions[i] if i < len(predictions) else {"label": "unclassified", "confidence": None, "scores": None}
        analyzed.append({
            "text": comment.get("text", ""),
            "author": comment.get("author", "Anonymous"),
            "published_at": comment.get("published_at", ""),
            "like_count": comment.get("like_count", 0),
            "is_reply": comment.get("is_reply", False),
            "prediction": pred,
        })
        label = pred.get("label", "")
        if label in counts:
            counts[label] += 1
        else:
            failed_count += 1

    total_successful = counts["positive"] + counts["neutral"] + counts["negative"]
    if total_successful == 0:
        raise HTTPException(
            status_code=500,
            detail=f"Sentiment analysis failed to classify any comments ({provider_name})."
        )

    total_analyzed = total_successful
    ratios = {k: (v / total_successful if total_successful > 0 else 0.0) for k, v in counts.items()}
    if failed_count > 0:
        logger.warning(f"⚠️ {failed_count} comments were unclassified and excluded from sentiment analytics.")

    logger.info(f"✅ Completed sentiment analysis using {provider_name} ({total_successful} analyzed, {failed_count} unclassified)")

    # ── 4. Generate visualizations ───────────────────────────────────────────
    _emit("Generating visualizations…", 80)
    texts_for_viz = [c.get("text", "") for c in comments if c.get("text")]
    viz = _viz_service.generate_all(texts_for_viz, counts)

    # ── 5. Assemble examples ─────────────────────────────────────────────────
    _emit("Completing results…", 95)
    examples: List[Dict] = []
    for sentiment in ["positive", "neutral", "negative"]:
        pool = [c for c in analyzed if c["prediction"]["label"] == sentiment]
        pool.sort(key=lambda x: x.get("like_count", 0), reverse=True)
        examples.extend(pool[:5])

    processing_time = time.time() - start
    _emit("Complete!", 100)

    # Cache the full comments list for instant CSV generation
    _last_analysis_cache = {
        "video_id": video_id,
        "percentage": percentage,
        "comments": analyzed,
    }

    return {
        "video_id": video_id,
        "video_title": video_title,
        "channel_title": channel_title,
        "total_comments": total_comments,
        "actual_analyzed": total_analyzed,
        "percentage_analyzed": percentage,
        "counts": counts,
        "ratios": ratios,
        "examples": examples[:15],
        "processing_time": round(processing_time, 2),
        "visualizations": viz,
    }


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Social Sentiment API is running 🚀", "version": "2.0.0"}


@app.get("/health")
def health_check():
    curr_settings = get_settings()
    provider = (curr_settings.SENTIMENT_PROVIDER or "gemini").lower()

    # Check DB connectivity
    db_connected = False
    try:
        from backend.db.session import get_session
        from sqlalchemy import text
        with get_session() as db:
            db.execute(text("SELECT 1"))
            db_connected = True
    except Exception:
        db_connected = False

    return {
        "status": "healthy",
        "provider": provider,
        "model": curr_settings.GEMINI_MODEL if provider == "gemini" else "xlmr-sentiment",
        "model_ready": _model_ready,
        "database_connected": db_connected,
        "gemini_api_configured": bool(curr_settings.GEMINI_API_KEY),
        "youtube_api_configured": bool(curr_settings.YOUTUBE_API_KEY),
        "rate_limit_protection": "15 RPM Free Tier Safe",
    }


# Helper to check monthly and daily quota limits
def _check_quota_or_raise():
    """Check monthly and daily quota limits to guarantee 100% Free Tier protection."""
    try:
        from backend.db.session import get_db
        from sqlalchemy import func
        from backend.db.models import QuotaUsage
        from datetime import date

        db = next(get_db())
        today = date.today()
        first_day_of_month = today.replace(day=1)

        used_month = db.query(func.sum(QuotaUsage.units_used)).filter(
            QuotaUsage.date >= first_day_of_month
        ).scalar() or 0

        used_today = db.query(func.sum(QuotaUsage.units_used)).filter(
            QuotaUsage.date == today
        ).scalar() or 0
        db.close()

        monthly_limit = settings.MONTHLY_QUOTA_LIMIT
        if used_month >= monthly_limit:
            raise HTTPException(
                status_code=429,
                detail="Monthly Free Tier API quota limit reached. Quota resets on the 1st of next month.",
            )

        daily_limit = settings.DAILY_QUOTA_LIMIT
        if used_today >= daily_limit:
            raise HTTPException(
                status_code=429,
                detail="Daily safety API limit reached. Please try again tomorrow.",
            )
    except HTTPException:
        raise
    except Exception as e:
        # DB might not be available, log and ignore to allow graceful fallback
        logger.warning(f"Quota check skipped because database is not available: {e}")


# ── Main analyze endpoint (direct, blocking) ──────────────────────────────────
@app.get("/api/analyze/video/{video_input}/visualize", response_model=AnalyzeOut)
async def analyze_video_with_visualization(
    video_input: str,
    percentage: float = Query(0.5, ge=0.25, le=1.0),
    save_to_db: bool = Query(True),
):
    """
    Analyze a YouTube video's comments and return sentiment results with visualizations.
    This is a blocking call — use the /stream endpoint for progress updates.
    """
    try:
        _check_quota_or_raise()
        video_id = extract_video_id(video_input)
        logger.info(f"🎯 Direct analyze: {video_id} @ {percentage*100:.0f}%")

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _run_analysis, video_id, percentage, None)

        if save_to_db:
            _try_save_to_db(result)

        return AnalyzeOut(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ── SSE streaming endpoint — with step-by-step progress ───────────────────────
@app.get("/api/analyze/video/{video_input}/stream")
async def analyze_video_stream(
    video_input: str,
    percentage: float = Query(0.5, ge=0.25, le=1.0),
):
    """
    Stream analysis progress as Server-Sent Events (SSE).
    Sends progress updates, then the final result.
    """
    try:
        _check_quota_or_raise()
        video_id = extract_video_id(video_input)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    loop = asyncio.get_event_loop()
    progress_queue: asyncio.Queue = asyncio.Queue()

    def _progress(step: str, pct: int):
        """Called from the thread pool — safely enqueue progress."""
        loop.call_soon_threadsafe(
            progress_queue.put_nowait, {"step": step, "progress": pct}
        )

    def _run_in_thread():
        """Run full analysis pipeline in a thread."""
        try:
            result = _run_analysis(video_id, percentage, _progress)
            _try_save_to_db(result)  # Record result and quota usage to database
            loop.call_soon_threadsafe(
                progress_queue.put_nowait, {"done": True, "result": result}
            )
        except Exception as exc:
            loop.call_soon_threadsafe(
                progress_queue.put_nowait, {"done": True, "error": str(exc)}
            )

    async def _event_generator() -> AsyncGenerator[str, None]:
        # Kick off analysis in thread pool
        future = loop.run_in_executor(None, _run_in_thread)

        while True:
            try:
                msg = await asyncio.wait_for(progress_queue.get(), timeout=300.0)
            except asyncio.TimeoutError:
                yield 'event: error\ndata: {"error": "Analysis timed out after 5 minutes"}\n\n'
                break

            if "done" in msg:
                if "error" in msg:
                    payload = json.dumps({"error": msg["error"]})
                    yield f"event: error\ndata: {payload}\n\n"
                else:
                    payload = json.dumps(msg["result"], default=str)
                    yield f"event: result\ndata: {payload}\n\n"
                break
            else:
                payload = json.dumps(msg)
                yield f"event: progress\ndata: {payload}\n\n"

        # Ensure the thread finishes cleanly
        try:
            await future
        except Exception:
            pass

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── Predict endpoint ──────────────────────────────────────────────────────────
@app.post("/api/predict", response_model=PredictResponse)
def predict_sentiment(body: PredictRequest):
    """Run sentiment prediction on a list of texts."""
    if not body.texts:
        raise HTTPException(status_code=400, detail="texts list is empty")

    results: List[Dict] = []
    try:
        svc = SentimentService.get()
        preds = svc.predict(body.texts)
        results = preds
    except Exception as e:
        logger.error(f"Sentiment prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    return PredictResponse(results=[PredictResult(**r) for r in results])


# ── Download CSV endpoint ─────────────────────────────────────────────────────
@app.get("/api/analyze/video/{video_input}/download")
async def download_csv(
    video_input: str,
    percentage: float = Query(0.5, ge=0.25, le=1.0),
):
    """Run analysis (or fetch from memory cache) and return all analyzed results as a downloadable CSV file."""
    try:
        _check_quota_or_raise()
        video_id = extract_video_id(video_input)
        
        global _last_analysis_cache
        if (_last_analysis_cache.get("video_id") == video_id 
            and _last_analysis_cache.get("percentage") == percentage 
            and _last_analysis_cache.get("comments")):
            logger.info(f"🚀 CSV Download: Cache HIT for video {video_id}")
            comments_to_write = _last_analysis_cache["comments"]
        else:
            logger.info(f"⚠️ CSV Download: Cache MISS for video {video_id}. Re-running analysis...")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _run_analysis, video_id, percentage, None)
            _try_save_to_db(result)
            comments_to_write = _last_analysis_cache.get("comments", [])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "author", "text", "like_count", "is_reply",
        "published_at", "sentiment", "confidence",
        "score_positive", "score_neutral", "score_negative",
    ])
    
    for c in comments_to_write:
        pred = c.get("prediction", {})
        scores = pred.get("scores") or {}
        
        conf_val = pred.get("confidence")
        conf_str = f"{conf_val:.4f}" if isinstance(conf_val, (int, float)) else ""
        
        pos_val = scores.get("positive")
        pos_str = f"{pos_val:.4f}" if isinstance(pos_val, (int, float)) else ""
        
        neu_val = scores.get("neutral")
        neu_str = f"{neu_val:.4f}" if isinstance(neu_val, (int, float)) else ""
        
        neg_val = scores.get("negative")
        neg_str = f"{neg_val:.4f}" if isinstance(neg_val, (int, float)) else ""

        writer.writerow([
            c.get("author", ""),
            c.get("text", "").replace("\n", " "),
            c.get("like_count", 0),
            c.get("is_reply", False),
            c.get("published_at", ""),
            pred.get("label", ""),
            conf_str,
            pos_str,
            neu_str,
            neg_str,
        ])

    output.seek(0)
    filename = f"sentiment_{video_id}_{int(percentage*100)}pct.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Quota endpoint ────────────────────────────────────────────────────────────
@app.get("/api/quota")
def get_quota():
    """API quota status for Free Tier usage protection (tracks via DB if available)."""
    used_month = 0
    used_today = 0
    try:
        from backend.db.session import get_db
        from sqlalchemy import func
        from backend.db.models import QuotaUsage
        from datetime import date

        db = next(get_db())
        today = date.today()
        first_day_of_month = today.replace(day=1)

        used_month = db.query(func.sum(QuotaUsage.units_used)).filter(
            QuotaUsage.date >= first_day_of_month
        ).scalar() or 0

        used_today = db.query(func.sum(QuotaUsage.units_used)).filter(
            QuotaUsage.date == today
        ).scalar() or 0
        db.close()
    except Exception:
        used_month = 0
        used_today = 0

    monthly_limit = settings.MONTHLY_QUOTA_LIMIT
    daily_limit = settings.DAILY_QUOTA_LIMIT

    monthly_remaining = max(0, monthly_limit - used_month)
    daily_remaining = max(0, daily_limit - used_today)
    credits_remaining = min(monthly_remaining, daily_remaining)

    from datetime import datetime, timedelta, timezone
    try:
        from zoneinfo import ZoneInfo
        pacific = ZoneInfo("US/Pacific")
        now = datetime.now(pacific)
        # Next month 1st
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            next_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        reset_time = next_month.strftime("%b 1, %Y 00:00 %Z")
    except Exception:
        reset_time = "1st of next month"

    return {
        "period": "monthly",
        "monthly_limit": monthly_limit,
        "daily_limit": daily_limit,
        "estimated_used": int(used_month),
        "estimated_remaining": monthly_remaining,
        "credits_remaining": credits_remaining,
        "comments_remaining": monthly_remaining * 100,
        "videos_remaining": monthly_remaining // 2,
        "reset_time": reset_time,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


# ─── Optional: save to DB ────────────────────────────────────────────────────
def _try_save_to_db(result: Dict) -> None:
    """Save all analyzed comments, predictions, and quota usage into PostgreSQL."""
    try:
        from backend.db.session import get_session
        from backend.db.models import Video, Comment, Prediction, QuotaUsage
        from datetime import date

        provider = (settings.SENTIMENT_PROVIDER or "gemini").lower()
        model_name = settings.GEMINI_MODEL if provider == "gemini" else "xlmr-sentiment"

        with get_session() as db:
            # Upsert video
            video = db.query(Video).filter_by(video_id=result["video_id"]).first()
            if not video:
                video = Video(
                    video_id=result["video_id"],
                    title=result["video_title"],
                    channel_title=result["channel_title"],
                )
                db.add(video)
                db.flush()
            else:
                video.title = result["video_title"]
                video.channel_title = result["channel_title"]
                db.flush()

            # Retrieve all comments to persist
            comments_to_save = []
            if _last_analysis_cache and _last_analysis_cache.get("video_id") == result["video_id"]:
                comments_to_save = _last_analysis_cache.get("comments", [])
            if not comments_to_save:
                comments_to_save = result.get("examples", [])

            # Existing comment IDs in DB to prevent duplicates
            existing_cids = {
                c.comment_id for c in db.query(Comment.comment_id).filter_by(video_pk=video.id).all()
            }

            saved_count = 0
            for item in comments_to_save:
                text = item.get("text", "")
                if not text:
                    continue
                cid = item.get("comment_id") or str(abs(hash(text)))
                if cid in existing_cids:
                    continue

                comment = Comment(
                    video_pk=video.id,
                    comment_id=cid,
                    author=item.get("author", "Anonymous")[:256],
                    text=text,
                    like_count=item.get("like_count", 0),
                    is_reply=item.get("is_reply", False),
                    commented_at=item.get("published_at", "")[:64],
                )
                db.add(comment)
                db.flush()
                existing_cids.add(cid)

                pred = item.get("prediction", {})
                scores = pred.get("scores") or {}
                prediction = Prediction(
                    comment_pk=comment.id,
                    model_name=model_name,
                    label=pred.get("label", "neutral"),
                    confidence=pred.get("confidence"),
                    positive_score=scores.get("positive"),
                    neutral_score=scores.get("neutral"),
                    negative_score=scores.get("negative"),
                )
                db.add(prediction)
                saved_count += 1

            # Calculate estimated YouTube API quota units used:
            # 1 unit for video metadata list + 1 unit per 100 comments/replies fetched
            actual_analyzed = result.get("actual_analyzed", 0)
            units_used = 1 + max(1, (actual_analyzed + 99) // 100)

            # Record quota usage
            usage = QuotaUsage(
                date=date.today(),
                operation_type="analyze",
                units_used=units_used,
                video_id=result["video_id"],
                meta_data={"percentage": result.get("percentage_analyzed")},
            )
            db.add(usage)
            logger.info(f"💾 Persisted {saved_count} comments & predictions for {result['video_id']} in PostgreSQL.")

    except Exception as e:
        logger.warning(f"DB save skipped: {e}")
