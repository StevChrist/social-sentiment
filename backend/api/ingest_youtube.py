# backend/api/ingest_youtube.py - UNLIMITED COMMENTS VERSION (FIXED)
import re
import time
import requests
import logging
from typing import List, Dict, Optional
from backend.core.config import get_settings

logger = logging.getLogger(__name__)

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_COMMENTS_URL = "https://www.googleapis.com/youtube/v3/comments"


def extract_video_id(input_str: str) -> str:
    """Extract video ID from YouTube URL"""
    if not input_str or not isinstance(input_str, str):
        raise ValueError("Invalid input: must be a non-empty string")

    input_str = input_str.strip()
    patterns = [
        r"(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/watch\?.*v=)([a-zA-Z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match and match.group(1):
            return match.group(1)

    if re.match(r"^[a-zA-Z0-9_-]{11}$", input_str):
        return input_str

    raise ValueError(f"Could not extract video ID from: {input_str}")


def get_total_comment_count(video_id: str, api_key: Optional[str] = None) -> int:
    """Get total comment count for a video"""
    settings = get_settings()
    key = api_key or settings.YOUTUBE_API_KEY
    if not key:
        raise ValueError("YOUTUBE_API_KEY not configured")

    params = {"part": "statistics", "id": video_id, "key": key}
    try:
        r = requests.get(YOUTUBE_VIDEO_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data.get("items"):
            stats = data["items"][0].get("statistics", {})
            return int(stats.get("commentCount", 0))
        return 0
    except Exception as e:
        logger.error(f"Failed to get comment count for {video_id}: {e}")
        return 0


def _request(url: str, params: Dict, retries: int = 3) -> Dict:
    """Robust request with retries and exponential backoff"""
    delay = 1.0
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            code = getattr(e.response, "status_code", None)
            retriable = isinstance(
                e,
                (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
            ) or (code in (429, 500, 502, 503, 504))
            logger.warning(
                f"Fetch error (attempt {attempt+1}/{retries}): {e}. Retriable={retriable}"
            )
            if not retriable or attempt == retries - 1:
                raise
            time.sleep(delay)
            delay *= 2


def fetch_youtube_comments(
    video_id: str,
    api_key: Optional[str] = None,
    max_comments: Optional[int] = None,  # None = unlimited
    include_replies: bool = True,
    percentage: float = 1.0,
) -> List[Dict]:
    """Fetch YouTube comments robustly (no hard cap, retry, safe parsing, full replies)."""
    settings = get_settings()
    key = api_key or settings.YOUTUBE_API_KEY
    if not key:
        raise ValueError("YOUTUBE_API_KEY not configured")

    total_comments = get_total_comment_count(video_id, key)
    if total_comments == 0:
        logger.warning(f"No comments found for video: {video_id}")
        return []

    # Target jumlah komentar
    if percentage == 1.0 and max_comments is None:
        target_max = float("inf")
        logger.info(f"🚀 Fetching ALL {total_comments} comments (100% - unlimited)")
    else:
        target_max = (
            int(total_comments * percentage)
            if max_comments is None
            else min(max_comments, int(total_comments * percentage))
        )
        logger.info(
            f"📊 Fetching up to {target_max} comments (of {total_comments}, {percentage*100:.0f}%)"
        )

    comments: List[Dict] = []
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": key,
        "maxResults": 100,
        "order": "time",
        "textFormat": "plainText",
    }
    page_token: Optional[str] = None

    while len(comments) < target_max:
        if page_token:
            params["pageToken"] = page_token
        elif "pageToken" in params:
            params.pop("pageToken")

        data = _request(YOUTUBE_API_URL, params)
        items = data.get("items", [])
        if not items:
            logger.info("✅ Pagination finished (no items)")
            break

        for th in items:
            if len(comments) >= target_max:
                break

            sn = th.get("snippet") or {}
            top = (sn.get("topLevelComment") or {}).get("snippet") or {}
            top_id = (sn.get("topLevelComment") or {}).get("id")
            if not top_id:
                continue

            comments.append(
                {
                    "comment_id": top_id,
                    "text": top.get("textDisplay", "") or "",
                    "author": top.get("authorDisplayName", "") or "",
                    "like_count": int(top.get("likeCount") or 0),
                    "published_at": top.get("publishedAt", "") or "",
                    "is_reply": False,
                    "raw_json": th,
                }
            )
            if len(comments) >= target_max:
                break

            # ---- Replies full pagination ----
            if include_replies:
                reply_token: Optional[str] = None
                reply_params = {
                    "part": "snippet",
                    "parentId": top_id,
                    "maxResults": 100,
                    "textFormat": "plainText",
                    "key": key,
                }
                while len(comments) < target_max:
                    if reply_token:
                        reply_params["pageToken"] = reply_token
                    elif "pageToken" in reply_params:
                        reply_params.pop("pageToken")

                    rd = _request(YOUTUBE_COMMENTS_URL, reply_params)
                    ritems = rd.get("items", [])
                    if not ritems:
                        break

                    for rep in ritems:
                        rsn = rep.get("snippet") or {}
                        comments.append(
                            {
                                "comment_id": rep.get("id"),
                                "text": rsn.get("textDisplay", "") or "",
                                "author": rsn.get("authorDisplayName", "") or "",
                                "like_count": int(rsn.get("likeCount") or 0),
                                "published_at": rsn.get("publishedAt", "") or "",
                                "is_reply": True,
                                "raw_json": rep,
                            }
                        )
                        if len(comments) >= target_max:
                            break

                    reply_token = rd.get("nextPageToken")
                    if not reply_token:
                        break

        page_token = data.get("nextPageToken")
        if not page_token:
            logger.info("✅ Reached end of commentThreads pages")
            break

    fetched = len(comments)
    pct = (fetched / total_comments * 100) if total_comments else 0.0
    logger.info(
        f"✅ Successfully fetched {fetched} comments (~{pct:.1f}% of top-level count {total_comments})."
    )
    return comments


def fetch_video_info(video_id: str, api_key: Optional[str] = None) -> Dict:
    """Fetch video metadata"""
    settings = get_settings()
    key = api_key or settings.YOUTUBE_API_KEY
    if not key:
        raise ValueError("YOUTUBE_API_KEY not configured")

    params = {"part": "snippet,statistics", "id": video_id, "key": key}
    try:
        r = requests.get(YOUTUBE_VIDEO_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data.get("items"):
            item = data["items"][0]
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            return {
                "video_id": video_id,
                "title": snippet.get("title", "Unknown Title"),
                "channel_title": snippet.get("channelTitle", "Unknown Channel"),
                "published_at": snippet.get("publishedAt", ""),
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
            }
        else:
            return {
                "video_id": video_id,
                "title": "Video Not Found",
                "channel_title": "Unknown Channel",
                "comment_count": 0,
            }
    except Exception as e:
        logger.error(f"Error fetching video info for {video_id}: {e}")
        return {
            "video_id": video_id,
            "title": "Error Loading Video",
            "channel_title": "Unknown Channel",
            "comment_count": 0,
        }
