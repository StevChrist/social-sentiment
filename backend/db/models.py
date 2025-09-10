# backend/db/models.py - FIXED VERSION (Compatible with All Python Versions)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, JSON, Float, Date
from datetime import datetime, date
from typing import Optional, List

class Base(DeclarativeBase): 
    pass

class Video(Base):
    __tablename__ = "videos"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32), default="youtube")
    video_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(512))              # ✅ Fix: Use Optional[str]
    channel_title: Mapped[Optional[str]] = mapped_column(String(256))      # ✅ Fix: Use Optional[str]
    published_at: Mapped[Optional[str]] = mapped_column(String(64))        # ✅ Fix: Use Optional[str]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)  # ✅ Fix: Use Optional[datetime]
    
    # Relationships
    comments: Mapped[List["Comment"]] = relationship(back_populates="video", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = "comments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    video_pk: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    comment_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    author: Mapped[Optional[str]] = mapped_column(String(256))             # ✅ Fix: Use Optional[str]
    text: Mapped[str] = mapped_column(Text)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_count: Mapped[int] = mapped_column(Integer, default=0)
    commented_at: Mapped[Optional[str]] = mapped_column(String(64))        # ✅ Fix: Use Optional[str]
    is_reply: Mapped[bool] = mapped_column(default=False)
    raw_json: Mapped[Optional[dict]] = mapped_column(JSON)                 # ✅ Fix: Use Optional[dict]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    video: Mapped["Video"] = relationship(back_populates="comments")
    predictions: Mapped[List["Prediction"]] = relationship(back_populates="comment", cascade="all, delete-orphan")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    comment_pk: Mapped[int] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), index=True)
    model_name: Mapped[str] = mapped_column(String(64), default="xlmr-sentiment")
    label: Mapped[str] = mapped_column(String(16))  # 'negative' | 'neutral' | 'positive'
    confidence: Mapped[float] = mapped_column(Float)
    negative_score: Mapped[float] = mapped_column(Float)
    neutral_score: Mapped[float] = mapped_column(Float)
    positive_score: Mapped[float] = mapped_column(Float)
    predicted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    comment: Mapped["Comment"] = relationship(back_populates="predictions")

class QuotaUsage(Base):
    __tablename__ = "quota_usage"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    operation_type: Mapped[Optional[str]] = mapped_column(String(50))       # ✅ Fix: Use Optional[str]
    units_used: Mapped[int] = mapped_column(Integer, default=0)
    video_id: Mapped[Optional[str]] = mapped_column(String(32))             # ✅ Fix: Use Optional[str]
    user_ip: Mapped[Optional[str]] = mapped_column(String(45))              # ✅ Fix: Use Optional[str]
    session_id: Mapped[Optional[str]] = mapped_column(String(64))           # ✅ Fix: Use Optional[str]
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON)                 # ✅ Fix: Use Optional[dict]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
