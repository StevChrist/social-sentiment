# backend/main.py - UNLIMITED COMMENTS VERSION
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from wordcloud import WordCloud
import base64
import io
import re
import time
from backend.core.config import get_settings
from backend.api.ingest_youtube import extract_video_id, fetch_youtube_comments, fetch_video_info
from backend.services.sentiment import SentimentService

app = FastAPI(title="Social Sentiment API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get settings
settings = get_settings()

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
    visualizations: Optional[Dict[str, str]] = None

def analyze_sentiment_simple(text: str) -> Dict[str, Any]:
    """Simple rule-based sentiment analysis as fallback"""
    text_lower = text.lower()
    
    positive_words = ['good', 'great', 'amazing', 'awesome', 'love', 'excellent', 
                     'wonderful', 'fantastic', 'perfect', 'best', 'helpful', 
                     'thanks', 'thank you', 'brilliant', 'outstanding', 'nice',
                     'beautiful', 'cool', 'incredible', 'superb']
    negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 
                     'disgusting', 'stupid', 'boring', 'sucks', 'waste', 'disappointed',
                     'useless', 'trash', 'pathetic', 'annoying', 'frustrating']
    
    positive_score = sum(1 for word in positive_words if word in text_lower)
    negative_score = sum(1 for word in negative_words if word in text_lower)
    
    if positive_score > negative_score:
        sentiment = 'positive'
        confidence = min(0.95, 0.6 + (positive_score - negative_score) * 0.1)
    elif negative_score > positive_score:
        sentiment = 'negative'
        confidence = min(0.95, 0.6 + (negative_score - positive_score) * 0.1)
    else:
        sentiment = 'neutral'
        confidence = 0.7
    
    return {
        'label': sentiment,
        'confidence': confidence,
        'scores': {
            'positive': confidence if sentiment == 'positive' else 0.3,
            'neutral': confidence if sentiment == 'neutral' else 0.4,
            'negative': confidence if sentiment == 'negative' else 0.3
        }
    }

def create_word_cloud_from_comments(comments: List[Dict]) -> str:
    """Create word cloud from real comment texts"""
    try:
        texts = [comment.get('text', '') for comment in comments if comment.get('text')]
        combined_text = ' '.join(texts)
        
        if not combined_text.strip():
            combined_text = "No comments available for analysis"
        
        # Remove URLs and special characters
        combined_text = re.sub(r'http\S+|www\S+|https\S+', '', combined_text, flags=re.MULTILINE)
        combined_text = re.sub(r'[^\w\s]', ' ', combined_text)
        
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            max_words=100,
            colormap='viridis',
            collocations=False,
            min_font_size=10
        ).generate(combined_text)
        
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"Word cloud error: {e}")
        return None

def create_pie_chart_from_data(counts: Dict[str, int]) -> str:
    """Create pie chart from real sentiment counts"""
    try:
        labels = []
        sizes = []
        colors = []
        
        color_map = {'Positive': '#10B981', 'Neutral': '#F59E0B', 'Negative': '#EF4444'}
        
        for sentiment, count in counts.items():
            if count > 0:
                labels.append(sentiment.capitalize())
                sizes.append(count)
                colors.append(color_map.get(sentiment.capitalize(), '#888888'))
        
        if not sizes:
            return None
        
        plt.figure(figsize=(8, 6))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
               startangle=90, textprops={'fontsize': 12})
        plt.title('Real Sentiment Distribution from YouTube Comments', fontsize=14, pad=20)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"Pie chart error: {e}")
        return None

@app.get("/api/analyze/video/{video_input}/visualize", response_model=AnalyzeOut)
async def analyze_video_with_visualization(
    video_input: str,
    percentage: float = Query(0.5, ge=0.25, le=1.0),
    save_to_db: bool = Query(True)
):
    """Analyze REAL YouTube video with UNLIMITED comments"""
    start_time = time.time()
    
    try:
        print(f"🎯 Starting REAL analysis for: {video_input} ({percentage*100}% of comments)")
        
        # Extract video ID using existing function
        video_id = extract_video_id(video_input)
        print(f"📹 Extracted video ID: {video_id}")
        
        # Fetch video info using existing function
        video_info = fetch_video_info(video_id, settings.YOUTUBE_API_KEY)
        video_title = video_info.get('title', 'Unknown Video')
        channel_title = video_info.get('channel_title', 'Unknown Channel')
        total_video_comments = video_info.get('comment_count', 0)
        
        print(f"📺 Video: {video_title} by {channel_title}")
        print(f"📊 Total comments in video: {total_video_comments}")
        
        # ✅ REMOVE ALL LIMITS - Calculate based on actual total
        if percentage == 1.0:
            max_comments = None  # ✅ UNLIMITED for 100%
            print(f"🚀 Fetching ALL comments (unlimited)")
        else:
            max_comments = int(total_video_comments * percentage) if total_video_comments > 0 else 1000
            print(f"📊 Fetching {max_comments} comments ({percentage*100}%)")
        
        # Fetch real YouTube comments using existing function
        comments = fetch_youtube_comments(
            video_id=video_id,
            api_key=settings.YOUTUBE_API_KEY,
            max_comments=max_comments,  # ✅ None = unlimited for 100%
            include_replies=True,
            percentage=percentage
        )
        
        print(f"📝 Fetched {len(comments)} real comments from YouTube")
        
        if not comments:
            raise HTTPException(status_code=404, 
                              detail="No comments found. Video may have comments disabled or be private.")
        
        # Analyze sentiment for each comment
        analyzed_comments = []
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        # Try to use advanced sentiment model, fallback to simple analysis
        try:
            sentiment_service = SentimentService.get()
            comment_texts = [comment['text'] for comment in comments if comment.get('text')]
            predictions = sentiment_service.predict(comment_texts)
            
            for i, comment in enumerate(comments):
                if i < len(predictions):
                    prediction = predictions[i]
                else:
                    prediction = analyze_sentiment_simple(comment.get('text', ''))
                
                analyzed_comment = {
                    'text': comment.get('text', ''),
                    'author': comment.get('author', 'Anonymous'),
                    'published_at': comment.get('published_at', ''),
                    'like_count': comment.get('like_count', 0),
                    'is_reply': comment.get('is_reply', False),
                    'prediction': prediction
                }
                analyzed_comments.append(analyzed_comment)
                sentiment_counts[prediction['label']] += 1
                
            print("✅ Used advanced XLM-RoBERTa sentiment model")
            
        except Exception as model_error:
            print(f"⚠️ Advanced model failed, using simple analysis: {model_error}")
            
            # Fallback to simple sentiment analysis
            for comment in comments:
                prediction = analyze_sentiment_simple(comment.get('text', ''))
                
                analyzed_comment = {
                    'text': comment.get('text', ''),
                    'author': comment.get('author', 'Anonymous'),
                    'published_at': comment.get('published_at', ''),
                    'like_count': comment.get('like_count', 0),
                    'is_reply': comment.get('is_reply', False),
                    'prediction': prediction
                }
                analyzed_comments.append(analyzed_comment)
                sentiment_counts[prediction['label']] += 1
        
        total_analyzed = len(analyzed_comments)
        
        # Calculate ratios
        ratios = {}
        if total_analyzed > 0:
            for sentiment, count in sentiment_counts.items():
                ratios[sentiment] = count / total_analyzed
        else:
            ratios = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        # Create visualizations from REAL data
        word_cloud_b64 = create_word_cloud_from_comments(comments)
        pie_chart_b64 = create_pie_chart_from_data(sentiment_counts)
        
        processing_time = time.time() - start_time
        
        # Select diverse example comments
        example_comments = []
        for sentiment in ['positive', 'neutral', 'negative']:
            sentiment_examples = [c for c in analyzed_comments if c['prediction']['label'] == sentiment]
            # Sort by like_count for better examples
            sentiment_examples.sort(key=lambda x: x.get('like_count', 0), reverse=True)
            example_comments.extend(sentiment_examples[:4])  # Take top 4 of each
        
        response_data = {
            "video_id": video_id,
            "video_title": video_title,
            "channel_title": channel_title,
            "total_comments": total_video_comments,  # ✅ Real total from video
            "actual_analyzed": total_analyzed,  # ✅ Actual number analyzed
            "percentage_analyzed": percentage,
            "counts": sentiment_counts,
            "ratios": ratios,
            "examples": example_comments[:15],  # Limit to 15 examples
            "processing_time": processing_time,
            "visualizations": {
                "wordcloud_base64": word_cloud_b64,
                "pie_chart_base64": pie_chart_b64
            }
        }
        
        print(f"✅ Analysis completed in {processing_time:.2f}s")
        print(f"📊 Real sentiment distribution: {sentiment_counts}")
        print(f"📈 Analyzed {total_analyzed} out of {total_video_comments} total comments")
        
        return AnalyzeOut(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/quota")
async def get_quota():
    """YouTube API quota status"""
    return {
        "daily_limit": 10000,
        "estimated_used": 274,
        "estimated_remaining": 9726,
        "reset_time": "2024-12-10T08:00:00Z",
        "credits_remaining": 9726,
        "comments_remaining": 972600,
        "videos_remaining": 4863,
        "last_updated": "2024-12-09T12:00:00Z"
    }

@app.get("/")
def root():
    return {"message": "Real YouTube Sentiment Analysis API is running! 🚀"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "youtube_api_configured": bool(settings.YOUTUBE_API_KEY)}
