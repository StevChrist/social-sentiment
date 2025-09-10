# backend/api/ingest_youtube.py - UNLIMITED COMMENTS VERSION
import re
from typing import List, Dict, Optional
import requests
import logging
from backend.core.config import get_settings

logger = logging.getLogger(__name__)

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"

def extract_video_id(input_str: str) -> str:
    """Extract video ID from YouTube URL - FIXED VERSION"""
    if not input_str or not isinstance(input_str, str):
        raise ValueError("Invalid input: must be a non-empty string")

    input_str = input_str.strip()
    
    patterns = [
        r'(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/watch\?.*v=)([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        try:
            match = re.search(pattern, input_str)
            if match and match.group(1):
                video_id = match.group(1)
                logger.info(f"Extracted video ID: {video_id} from pattern: {pattern}")
                return video_id
        except (AttributeError, IndexError) as e:
            logger.warning(f"Pattern {pattern} failed: {e}")
            continue
    
    if re.match(r'^[a-zA-Z0-9_-]{11}$', input_str):
        logger.info(f"Input appears to be a video ID: {input_str}")
        return input_str
    
    raise ValueError(f"Could not extract video ID from: {input_str}")

def get_total_comment_count(video_id: str, api_key: Optional[str] = None) -> int:
    """Get total comment count for a video"""
    settings = get_settings()
    key = api_key or settings.YOUTUBE_API_KEY
    
    if not key:
        raise ValueError("YOUTUBE_API_KEY not configured")
    
    params = {
        "part": "statistics",
        "id": video_id,
        "key": key,
    }
    
    try:
        r = requests.get(YOUTUBE_VIDEO_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        
        if data.get("items"):
            stats = data["items"][0].get("statistics", {})
            return int(stats.get("commentCount", 0))
        else:
            logger.warning(f"No video found for ID: {video_id}")
            return 0
    except Exception as e:
        logger.error(f"Failed to get comment count for {video_id}: {e}")
        return 0

def fetch_youtube_comments(
    video_id: str,
    api_key: Optional[str] = None,
    max_comments: int = None,  # ✅ None = unlimited
    include_replies: bool = True,
    percentage: float = 1.0
) -> List[Dict]:
    """Fetch YouTube comments with UNLIMITED capability"""
    settings = get_settings()
    key = api_key or settings.YOUTUBE_API_KEY
    
    if not key:
        raise ValueError("YOUTUBE_API_KEY not configured")
    
    # Get total comment count first
    total_comments = get_total_comment_count(video_id, key)
    if total_comments == 0:
        logger.warning(f"No comments found for video: {video_id}")
        return []
    
    # ✅ Calculate actual max based on percentage and total comments
    if percentage == 1.0 and max_comments is None:  # 100% = ALL COMMENTS
        actual_max = float('inf')  # ✅ No limit!
        logger.info(f"🚀 Fetching ALL {total_comments} comments (100% - UNLIMITED)")
    elif max_comments is None:
        actual_max = int(total_comments * percentage)
        logger.info(f"📊 Fetching {actual_max} out of {total_comments} comments ({percentage*100}%)")
    else:
        actual_max = min(max_comments, int(total_comments * percentage))
        logger.info(f"⚠️ Limited to {actual_max} comments (requested: {max_comments})")
    
    params = {
        "part": "snippet,replies" if include_replies else "snippet",
        "videoId": video_id,
        "key": key,
        "maxResults": 100,  # Max per request is 100
        "order": "time",  # Get chronological order
        "textFormat": "plainText",
    }
    
    comments: List[Dict] = []
    next_page = None
    request_count = 0
    max_requests = 200  # ✅ Increased limit for big videos
    
    while len(comments) < actual_max and request_count < max_requests:
        if next_page:
            params["pageToken"] = next_page
        
        try:
            request_count += 1
            if request_count % 10 == 0:  # Log every 10 requests
                logger.info(f"🔄 Request #{request_count} - Fetched {len(comments)} comments...")
            
            r = requests.get(YOUTUBE_API_URL, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            if not data.get("items"):
                logger.warning("No more comments available")
                break
            
            # Process each comment thread
            for item in data.get("items", []):
                if len(comments) >= actual_max:
                    break
                
                try:
                    top = item["snippet"]["topLevelComment"]["snippet"]
                    comments.append({
                        "comment_id": item["snippet"]["topLevelComment"]["id"],
                        "text": top.get("textDisplay", ""),
                        "author": top.get("authorDisplayName", ""),
                        "like_count": int(top.get("likeCount", 0)),
                        "published_at": top.get("publishedAt", ""),
                        "is_reply": False,
                        "raw_json": item
                    })
                    
                    # Process replies if enabled and within limit
                    if include_replies and len(comments) < actual_max:
                        for rep in item.get("replies", {}).get("comments", []):
                            if len(comments) >= actual_max:
                                break
                            
                            try:
                                rs = rep["snippet"]
                                comments.append({
                                    "comment_id": rep["id"],
                                    "text": rs.get("textDisplay", ""),
                                    "author": rs.get("authorDisplayName", ""),
                                    "like_count": int(rs.get("likeCount", 0)),
                                    "published_at": rs.get("publishedAt", ""),
                                    "is_reply": True,
                                    "raw_json": rep
                                })
                            except (KeyError, TypeError) as e:
                                logger.warning(f"Skipping malformed reply: {e}")
                                continue
                                
                except (KeyError, TypeError) as e:
                    logger.warning(f"Skipping malformed comment: {e}")
                    continue
            
            # Get next page token
            next_page = data.get("nextPageToken")
            if not next_page:
                logger.info("✅ Reached end of comments (no more pages)")
                break
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching comments: {e}")
            break
        except Exception as e:
            logger.error(f"Unexpected error fetching comments: {e}")
            break
    
    final_count = len(comments)
    actual_percentage = (final_count / total_comments * 100) if total_comments > 0 else 0
    
    logger.info(f"✅ Successfully fetched {final_count} comments ({actual_percentage:.1f}% of total)")
    
    return comments

def fetch_video_info(video_id: str, api_key: Optional[str] = None) -> Dict:
    """Fetch video metadata"""
    settings = get_settings()
    key = api_key or settings.YOUTUBE_API_KEY
    
    if not key:
        raise ValueError("YOUTUBE_API_KEY not configured")
    
    params = {
        "part": "snippet,statistics",
        "id": video_id,
        "key": key,
    }
    
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
            logger.warning(f"No video found for ID: {video_id}")
            return {
                "video_id": video_id,
                "title": "Video Not Found",
                "channel_title": "Unknown Channel",
                "comment_count": 0
            }
    except Exception as e:
        logger.error(f"Error fetching video info for {video_id}: {e}")
        return {
            "video_id": video_id,
            "title": "Error Loading Video",
            "channel_title": "Unknown Channel",
            "comment_count": 0
        }
