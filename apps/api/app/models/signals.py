"""Enhanced signal model for extreme alpha generation."""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Signal(Base):
    """Enhanced signal model for extreme alpha >30% returns."""
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    signal_type = Column(String, nullable=False)  # 'extreme', 'swing', 'long_term', 'meme', 'divergence'
    pattern_type = Column(String)  # 'volume_spike', 'influencer_shift', 'momentum_surge'
    
    confidence = Column(Float, nullable=False)
    expected_return = Column(Float, nullable=False)
    timeframe = Column(String, nullable=False)  # '48_hours', '1_week', '1_month'
    sources = Column(JSON, nullable=False)  # Which platforms detected
    pattern_stack = Column(JSON, nullable=False)  # Multiple patterns detected
    detection_metadata = Column(JSON)  # Additional context
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Execution tracking
    executed = Column(Boolean, default=False)
    execution_price = Column(Float, nullable=True)
    execution_time = Column(DateTime(timezone=True), nullable=True)
    result = Column(Float, nullable=True)  # Actual return achieved
    exit_price = Column(Float, nullable=True)
    exit_time = Column(DateTime(timezone=True), nullable=True)
    
    # Trading fields
    action = Column(String, nullable=False)  # 'BUY', 'SELL', 'HOLD'
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    allocation_percent = Column(Float, nullable=True)
    
    # Pattern detection metadata
    volume_spike = Column(Float, nullable=True)
    momentum_score = Column(Float, nullable=True)
    sentiment_divergence = Column(Float, nullable=True)
    meme_velocity = Column(Float, nullable=True)
    
    # User relationship (optional)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        return f"<Signal {self.ticker}: {self.action} @ {self.confidence:.2f} confidence>"
    
    def to_dict(self):
        """Convert signal to dictionary."""
        return {
            "id": self.id,
            "ticker": self.ticker,
            "signal_type": self.signal_type,
            "pattern_type": self.pattern_type,
            "confidence": self.confidence,
            "expected_return": self.expected_return,
            "timeframe": self.timeframe,
            "sources": self.sources,
            "pattern_stack": self.pattern_stack,
            "action": self.action,
            "executed": self.executed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "allocation_percent": self.allocation_percent
        }


class ExtremeEvent(Base):
    """Track extreme market events for pattern learning."""
    __tablename__ = "extreme_events"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    event_type = Column(String)  # 'short_squeeze', 'sector_rotation', 'viral_adoption'
    
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    start_price = Column(Float, nullable=False)
    peak_price = Column(Float, nullable=True)
    total_return = Column(Float, nullable=True)
    
    precursor_patterns = Column(JSON)  # Patterns that preceded event
    catalyst = Column(String)  # What triggered the move
    
    reddit_mentions = Column(Integer)
    twitter_mentions = Column(Integer)
    tiktok_videos = Column(Integer)
    youtube_videos = Column(Integer)
    
    mention_velocity = Column(Float)  # Rate of change
    sentiment_velocity = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MemeVelocity(Base):
    """Track meme stock velocity across platforms."""
    __tablename__ = "meme_velocity"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    reddit_score = Column(Float, default=0)
    twitter_score = Column(Float, default=0)
    tiktok_score = Column(Float, default=0)
    discord_score = Column(Float, default=0)
    youtube_score = Column(Float, default=0)
    
    total_score = Column(Float, nullable=False)
    velocity = Column(Float)  # Change from previous
    acceleration = Column(Float)  # Change in velocity
    
    average_sentiment = Column(Float)
    sentiment_divergence = Column(Float)
    
    top_influencers = Column(JSON)
    influencer_reach = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PatternDetection(Base):
    """Store detected patterns for analysis."""
    __tablename__ = "pattern_detections"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_name = Column(String, index=True)
    ticker = Column(String, index=True)
    
    confidence = Column(Float)
    indicators_met = Column(JSON)
    strength = Column(Float)
    
    market_context = Column(JSON)
    cross_validation = Column(JSON)
    
    signal_generated = Column(Boolean, default=False)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    outcome_return = Column(Float, nullable=True)
    outcome_timeframe = Column(String, nullable=True)
    
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class InformationAsymmetry(Base):
    """Track information asymmetry opportunities."""
    __tablename__ = "information_asymmetry"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    
    retail_sentiment = Column(Float)
    institutional_sentiment = Column(Float)
    divergence_score = Column(Float)
    
    early_source = Column(String)  # First platform to detect
    mainstream_lag = Column(Integer)  # Hours until mainstream
    
    information_path = Column(JSON)  # How info spread
    propagation_speed = Column(Float)
    
    entry_window = Column(String)  # Time window for entry
    expected_convergence = Column(String)  # When asymmetry closes
    
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)