# backend/api/quota.py
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import logging
from typing import Optional
from datetime import datetime, timedelta, date
import pytz
from sqlalchemy import func
from backend.db.session import get_db
from backend.db.models import QuotaUsage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["quota"])

class QuotaResponse(BaseModel):
    daily_limit: int
    estimated_used: int
    estimated_remaining: int
    reset_time: str
    credits_remaining: int
    comments_remaining: int
    videos_remaining: int
    last_updated: str

def record_quota_usage(operation_type: str, units_used: int, video_id: Optional[str] = None, user_ip: Optional[str] = None, session_id: Optional[str] = None) -> bool:
    try:
        db = next(get_db())
        
        usage_record = QuotaUsage(
            date=date.today(),
            operation_type=operation_type,
            units_used=units_used,
            video_id=video_id,
            user_ip=user_ip,
            session_id=session_id,
            # ✅ Use meta_data instead of metadata
            meta_data={"timestamp": datetime.utcnow().isoformat()}
        )
        
        db.add(usage_record)
        db.commit()
        db.close()
        
        logger.info(f"Recorded quota usage: {operation_type} = {units_used} units")
        return True
        
    except Exception as e:
        logger.error(f"Failed to record quota usage: {e}")
        return False

def get_daily_quota_usage() -> int:
    """Get accurate daily quota usage from database"""
    try:
        db = next(get_db())
        today = date.today()
        
        total_used = db.query(func.sum(QuotaUsage.units_used)).filter(
            QuotaUsage.date == today
        ).scalar() or 0
        
        db.close()
        return int(total_used)
        
    except Exception as e:
        logger.error(f"Failed to get quota usage: {e}")
        return 0

@router.get("/quota", response_model=QuotaResponse)
def get_quota_status():
    """Get real-time YouTube API quota status"""
    try:
        daily_limit = 10000
        actual_used = get_daily_quota_usage()
        estimated_remaining = max(0, daily_limit - actual_used)
        
        # Calculate reset time (midnight Pacific)
        pacific = pytz.timezone('US/Pacific')
        now = datetime.now(pacific)
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        reset_time = tomorrow.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        # User-friendly calculations
        videos_remaining = estimated_remaining // 2
        comments_remaining = estimated_remaining * 100
        
        return QuotaResponse(
            daily_limit=daily_limit,
            estimated_used=actual_used,
            estimated_remaining=estimated_remaining,
            reset_time=reset_time,
            credits_remaining=estimated_remaining,
            comments_remaining=comments_remaining,
            videos_remaining=videos_remaining,
            last_updated=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get quota status: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve quota information")

@router.post("/quota/track")
def track_quota_usage(request: Request, operation: str, units: int, video_id: Optional[str] = None):
    """Track quota usage endpoint"""
    try:
        user_ip = request.client.host if request else None
        session_id = request.headers.get("X-Session-ID", "anonymous") if request else None
        
        success = record_quota_usage(
            operation_type=operation,
            units_used=units,
            video_id=video_id,
            user_ip=user_ip,
            session_id=session_id
        )
        
        if success:
            return {"status": "success", "message": f"Tracked {units} units for {operation}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to track usage")
            
    except Exception as e:
        logger.error(f"Failed to track quota usage: {e}")
        raise HTTPException(status_code=500, detail="Could not track quota usage")
