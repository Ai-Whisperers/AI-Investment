"""Enhanced signal model for extreme alpha generation."""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from ..core.database import Base


class Signal(Base):
    """Enhanced signal model for extreme alpha >30% returns."""
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    signal_type = Column(String, nullable=False)  # 'extreme', 'swing', 'long_term'
    confidence = Column(Float, nullable=False)
    expected_return = Column(Float, nullable=False)
    timeframe = Column(String, nullable=False)  # '48_hours', '1_week', '1_month'
    sources = Column(JSON, nullable=False)  # Which platforms detected
    pattern_stack = Column(JSON, nullable=False)  # Multiple patterns detected
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    executed = Column(Boolean, default=False)
    result = Column(Float, nullable=True)  # Actual return achieved
    
    # Additional fields for tracking
    action = Column(String, nullable=False)  # 'BUY', 'SELL', 'HOLD'
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    allocation_percent = Column(Float, nullable=True)
    
    # Pattern detection metadata
    volume_spike = Column(Float, nullable=True)
    momentum_score = Column(Float, nullable=True)
    sentiment_divergence = Column(Float, nullable=True)
    meme_velocity = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<Signal {self.ticker}: {self.action} @ {self.confidence:.2f} confidence>"