"""
API endpoints for managing strategy configuration.
Refactored to use repository pattern - no direct database access.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..models.user import User
from ..repositories.strategy_repository import StrategyRepository
from ..schemas.validation import SecureStrategyConfig
from ..services.refresh import refresh_all
from ..utils.token_dep import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/config")
def get_strategy_config(
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    """Get current strategy configuration."""
    # Use repository instead of direct DB access
    repo = StrategyRepository(db)
    config = repo.get_config()
    
    if not config:
        raise HTTPException(status_code=404, detail="Strategy configuration not found")

    return {
        "momentum_weight": config.momentum_weight,
        "market_cap_weight": config.market_cap_weight,
        "risk_parity_weight": config.risk_parity_weight,
        "min_price_threshold": config.min_price_threshold,
        "max_daily_return": config.max_daily_return,
        "min_daily_return": config.min_daily_return,
        "max_forward_fill_days": config.max_forward_fill_days,
        "outlier_std_threshold": config.outlier_std_threshold,
        "rebalance_frequency": config.rebalance_frequency,
        "daily_drop_threshold": config.daily_drop_threshold,
        "ai_adjusted": config.ai_adjusted,
        "ai_adjustment_reason": config.ai_adjustment_reason,
        "ai_confidence_score": config.ai_confidence_score,
        "last_rebalance": config.last_rebalance,
        "updated_at": config.updated_at,
    }


@router.put("/config")
def update_strategy_config(
    updates: SecureStrategyConfig,  # Use validated schema
    recompute: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Update strategy configuration with validated input.

    Args:
        updates: Validated strategy configuration
        recompute: Whether to recompute the index after updating
    """
    # Use repository for data access
    repo = StrategyRepository(db)
    
    # Update configuration through repository
    update_dict = updates.dict(exclude_unset=True)  # Only include provided fields
    config = repo.update_config(update_dict, user_id=user.id)

    # Recompute index if requested
    if recompute:
        try:
            logger.info("Recomputing index with new configuration...")
            refresh_all(db, smart_mode=True)
        except Exception as e:
            logger.error(f"Error recomputing index: {e}")
            raise HTTPException(
                status_code=500, detail=f"Configuration updated but recompute failed: {str(e)}"
            )

    return {
        "message": "Strategy configuration updated successfully",
        "config": {
            "momentum_weight": config.momentum_weight,
            "market_cap_weight": config.market_cap_weight,
            "risk_parity_weight": config.risk_parity_weight,
            "min_price_threshold": config.min_price_threshold,
            "max_daily_return": config.max_daily_return,
            "min_daily_return": config.min_daily_return,
            "max_forward_fill_days": config.max_forward_fill_days,
            "outlier_std_threshold": config.outlier_std_threshold,
            "rebalance_frequency": config.rebalance_frequency,
            "daily_drop_threshold": config.daily_drop_threshold,
            "ai_adjusted": config.ai_adjusted,
            "ai_adjustment_reason": config.ai_adjustment_reason,
            "ai_confidence_score": config.ai_confidence_score,
            "last_rebalance": config.last_rebalance,
            "updated_at": config.updated_at,
        },
    }


@router.get("/risk-metrics")
def get_risk_metrics(
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    """Get current risk metrics for the strategy."""
    # Use repository for data access
    repo = StrategyRepository(db)
    metrics = repo.get_risk_metrics()
    
    if not metrics:
        raise HTTPException(status_code=404, detail="Risk metrics not available")
    
    return {
        "sharpe_ratio": metrics.sharpe_ratio,
        "max_drawdown": metrics.max_drawdown,
        "volatility": metrics.volatility,
        "beta": metrics.beta,
        "calculated_at": metrics.calculated_at,
        "win_rate": metrics.win_rate,
        "profit_factor": metrics.profit_factor,
        "calmar_ratio": metrics.calmar_ratio,
        "omega_ratio": metrics.omega_ratio,
        "sortino_ratio": metrics.sortino_ratio,
    }


@router.post("/rebalance")
def trigger_rebalance(
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    """Manually trigger a portfolio rebalance."""
    # Use repository for data access
    repo = StrategyRepository(db)
    config = repo.get_or_create_config()
    
    try:
        logger.info(f"Manual rebalance triggered by user {user.id}")
        
        # Update last rebalance time
        config.last_rebalance = datetime.utcnow()
        repo.save_config(config)
        
        # Trigger the refresh
        refresh_all(db, smart_mode=True)
        
        return {
            "message": "Rebalance triggered successfully",
            "last_rebalance": config.last_rebalance,
        }
    except Exception as e:
        logger.error(f"Error during rebalance: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Rebalance failed: {str(e)}"
        )


@router.get("/history")
def get_adjustment_history(
    limit: int = 10,
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    """Get history of strategy configuration adjustments."""
    # Use repository for data access
    repo = StrategyRepository(db)
    config = repo.get_config()
    
    if not config or not config.adjustment_history:
        return {"history": []}
    
    # Return most recent adjustments
    history = config.adjustment_history[-limit:] if limit else config.adjustment_history
    return {"history": list(reversed(history))}