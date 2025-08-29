"""
Repository for strategy configuration data access.
Implements repository pattern to abstract database operations.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.strategy import StrategyConfig, RiskMetrics


class StrategyRepository:
    """Repository for strategy configuration operations."""
    
    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db
    
    def get_config(self) -> Optional[StrategyConfig]:
        """
        Get the current strategy configuration.
        
        Returns:
            StrategyConfig or None if not found
        """
        return self.db.query(StrategyConfig).first()
    
    def create_config(self) -> StrategyConfig:
        """
        Create a new strategy configuration with defaults.
        
        Returns:
            Newly created StrategyConfig
        """
        config = StrategyConfig()
        self.db.add(config)
        return config
    
    def get_or_create_config(self) -> StrategyConfig:
        """
        Get existing config or create new one if doesn't exist.
        
        Returns:
            StrategyConfig instance
        """
        config = self.get_config()
        if not config:
            config = self.create_config()
        return config
    
    def update_config(
        self, 
        updates: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> StrategyConfig:
        """
        Update strategy configuration.
        
        Args:
            updates: Dictionary of fields to update
            user_id: ID of user making the update
            
        Returns:
            Updated StrategyConfig
        """
        config = self.get_or_create_config()
        
        # Update fields
        for field, value in updates.items():
            if hasattr(config, field):
                setattr(config, field, value)
        
        config.updated_at = datetime.utcnow()
        
        # Store in adjustment history
        if config.adjustment_history is None:
            config.adjustment_history = []
        
        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "updates": updates
        }
        
        if user_id:
            history_entry["user_id"] = user_id
            
        config.adjustment_history.append(history_entry)
        
        self.db.commit()
        return config
    
    def get_risk_metrics(self) -> Optional[RiskMetrics]:
        """
        Get current risk metrics.
        
        Returns:
            RiskMetrics or None if not found
        """
        return self.db.query(RiskMetrics).order_by(RiskMetrics.calculated_at.desc()).first()
    
    def save_config(self, config: StrategyConfig) -> None:
        """
        Save strategy configuration changes.
        """
        self.db.commit()
    
    def refresh(self) -> None:
        """
        Refresh the session to get latest data.
        """
        self.db.refresh(self.get_config())