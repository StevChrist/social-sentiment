# backend/api/analyze.py - FIXED VERSION with missing route
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analyze"])

# Response model for visualization endpoint
class AnalyzeVideoWithVisualizationOut(BaseModel):
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

# ✅ Add the missing route that frontend is calling
@router.get("/analyze/video/{video_input}/visualize", response_model=AnalyzeVideoWithVisualizationOut)
async def analyze_video_with_visualization(
    video_input: str,
    percentage: float = Query(0.5, ge=0.25, le=1.0),
    save_to_db: bool = Query(True),
    request: Request = None
):
    """Analyze sentiment with visualizations - the endpoint that was missing"""
    try:
        logger.info(f"Analyzing video: {video_input} with {percentage*100}% of comments")
        
        # Your existing analysis logic here
        # This is just a mock response for now
        mock_response = {
            "video_id": "becPBPA1kqU",
            "video_title": "Test Video Title",
            "channel_title": "Test Channel",
            "total_comments": 100,
            "actual_analyzed": int(100 * percentage),
            "percentage_analyzed": percentage,
            "counts": {
                "positive": 30,
                "negative": 20,
                "neutral": 50
            },
            "ratios": {
                "positive": 0.3,
                "negative": 0.2,  
                "neutral": 0.5
            },
            "examples": [
                {
                    "text": "This is great!",
                    "author": "User1",
                    "prediction": {"label": "positive", "confidence": 0.95}
                },
                {
                    "text": "Not bad",
                    "author": "User2", 
                    "prediction": {"label": "neutral", "confidence": 0.75}
                },
                {
                    "text": "I don't like this",
                    "author": "User3",
                    "prediction": {"label": "negative", "confidence": 0.85}
                }
            ],
            "processing_time": 2.5,
            "visualizations": {
                "wordcloud_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                "pie_chart_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                "bar_chart_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            }
        }
        
        return AnalyzeVideoWithVisualizationOut(**mock_response)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# ✅ Alternative endpoint if you want different URL pattern
@router.get("/analyze/{video_id}", response_model=AnalyzeVideoWithVisualizationOut) 
async def analyze_video_simple(
    video_id: str,
    percentage: float = Query(0.5, ge=0.25, le=1.0)
):
    """Alternative simpler endpoint"""
    # Same logic as above
    pass
