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
    """Attempt to load the XLM-RoBERTa model. Returns True on success."""
    global _sentiment_service, _model_ready, _model_loading
    if _model_ready:
        return True
    if _model_loading:
        return False

    _model_loading = True
    try:
        logger.info(f"Loading sentiment model from: {settings.MODEL_DIR}")
        _sentiment_service = SentimentService.get()
        _model_ready = True
        logger.info("✅ XLM-RoBERTa model loaded successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        _model_ready = False
        return False
    finally:
        _model_loading = False


# ─── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model in background on startup so first request isn't slow."""
    logger.info("🚀 Social Sentiment API starting up...")
    # Load model in a thread pool to avoid blocking the event loop
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
    version="2.0.0",
    description="YouTube comment sentiment analysis using XLM-RoBERTa",
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
    confidence: float
    scores: Dict[str, float]


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

    # ── 2. Collect comments ──────────────────────────────────────────────────
    _emit("Collecting comments from YouTube…", 15)
    # Apply safety cap limit from settings to prevent server overload
    raw_target = int(total_comments * percentage) if total_comments > 0 else 500
    max_comments = min(raw_target, settings.MAX_COMMENTS_LIMIT)
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

    try:
        svc = SentimentService.get()
        predictions = svc.predict(comment_texts)
        _emit("AI model running — processing predictions…", 65)

        for i, comment in enumerate(comments):
            pred = predictions[i] if i < len(predictions) else _rule_based_sentiment(comment.get("text", ""))
            analyzed.append({
                "text": comment.get("text", ""),
                "author": comment.get("author", "Anonymous"),
                "published_at": comment.get("published_at", ""),
                "like_count": comment.get("like_count", 0),
                "is_reply": comment.get("is_reply", False),
                "prediction": pred,
            })
            counts[pred["label"]] += 1

        logger.info("✅ Used XLM-RoBERTa for sentiment analysis")

    except Exception as e:
        logger.warning(f"Model failed, using rule-based fallback: {e}")
        _emit("Using rule-based fallback model…", 65)

        for comment in comments:
            pred = _rule_based_sentiment(comment.get("text", ""))
            analyzed.append({
                "text": comment.get("text", ""),
                "author": comment.get("author", "Anonymous"),
                "published_at": comment.get("published_at", ""),
                "like_count": comment.get("like_count", 0),
                "is_reply": comment.get("is_reply", False),
                "prediction": pred,
            })
            counts[pred["label"]] += 1

    total_analyzed = len(analyzed)
    ratios = {k: (v / total_analyzed if total_analyzed > 0 else 0.0) for k, v in counts.items()}

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
    global _last_analysis_cache
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
    return {
        "status": "healthy",
        "model_ready": _model_ready,
        "youtube_api_configured": bool(settings.YOUTUBE_API_KEY),
    }


# Helper to check daily quota limit
def _check_quota_or_raise():
    """Check if daily quota limit of 10000 units is exceeded. Raise 429 if it is."""
    try:
        from backend.db.session import get_db
        from sqlalchemy import func
        from backend.db.models import QuotaUsage
        from datetime import date

        db = next(get_db())
        today = date.today()
        used = db.query(func.sum(QuotaUsage.units_used)).filter(
            QuotaUsage.date == today
        ).scalar() or 0
        db.close()

        daily_limit = settings.DAILY_QUOTA_LIMIT
        if used >= daily_limit:
            raise HTTPException(
                status_code=429,
                detail="Daily API quota limit exceeded. Please try again tomorrow.",
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
        logger.warning(f"Model unavailable, using rule-based: {e}")
        results = [_rule_based_sentiment(t) for t in body.texts]

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
        scores = pred.get("scores", {})
        writer.writerow([
            c.get("author", ""),
            c.get("text", "").replace("\n", " "),
            c.get("like_count", 0),
            c.get("is_reply", False),
            c.get("published_at", ""),
            pred.get("label", ""),
            round(pred.get("confidence", 0), 4),
            round(scores.get("positive", 0), 4),
            round(scores.get("neutral", 0), 4),
            round(scores.get("negative", 0), 4),
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
    """YouTube API quota status (tracks via DB if available, else static estimate)."""
    try:
        from backend.db.session import get_db
        from sqlalchemy import func
        from backend.db.models import QuotaUsage
        from datetime import date

        db = next(get_db())
        today = date.today()
        used = db.query(func.sum(QuotaUsage.units_used)).filter(
            QuotaUsage.date == today
        ).scalar() or 0
        db.close()
    except Exception:
        used = 0  # DB not available — show 0 usage

    daily_limit = settings.DAILY_QUOTA_LIMIT
    remaining = max(0, daily_limit - used)

    from datetime import datetime, timedelta, timezone
    try:
        from zoneinfo import ZoneInfo
        pacific = ZoneInfo("US/Pacific")
        now = datetime.now(pacific)
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        reset_time = tomorrow.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        reset_time = "Tomorrow 00:00 PT"

    return {
        "daily_limit": daily_limit,
        "estimated_used": int(used),
        "estimated_remaining": remaining,
        "reset_time": reset_time,
        "credits_remaining": remaining,
        "comments_remaining": remaining * 100,
        "videos_remaining": remaining // 2,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


# ─── Optional: save to DB ────────────────────────────────────────────────────
def _try_save_to_db(result: Dict) -> None:
    """Attempt to save analysis results to DB. Silently skips if DB unavailable."""
    try:
        from backend.db.session import get_session
        from backend.db.models import Video, Comment, Prediction, QuotaUsage
        from datetime import date

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

            # Save example comments + predictions
            for ex in result.get("examples", []):
                # Skip if already exists
                existing = db.query(Comment).filter_by(
                    comment_id=ex.get("text", "")[:64]
                ).first()
                if existing:
                    continue

                comment = Comment(
                    video_pk=video.id,
                    comment_id=str(hash(ex.get("text", ""))),
                    author=ex.get("author", ""),
                    text=ex.get("text", ""),
                    like_count=ex.get("like_count", 0),
                    is_reply=ex.get("is_reply", False),
                    commented_at=ex.get("published_at", ""),
                )
                db.add(comment)
                db.flush()

                pred = ex.get("prediction", {})
                scores = pred.get("scores", {})
                prediction = Prediction(
                    comment_pk=comment.id,
                    label=pred.get("label", "neutral"),
                    confidence=pred.get("confidence", 0.0),
                    positive_score=scores.get("positive", 0.0),
                    neutral_score=scores.get("neutral", 0.0),
                    negative_score=scores.get("negative", 0.0),
                )
                db.add(prediction)

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

    except Exception as e:
        logger.warning(f"DB save skipped: {e}")
