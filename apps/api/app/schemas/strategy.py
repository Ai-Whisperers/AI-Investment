"""
Strategy configuration and risk management schemas.
"""

from datetime import date as DateType
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrategyConfigRequest(BaseModel):
    """Strategy configuration update request."""

    momentum_weight: float | None = Field(None, ge=0, le=1)
    market_cap_weight: float | None = Field(None, ge=0, le=1)
    risk_parity_weight: float | None = Field(None, ge=0, le=1)
    min_price_threshold: float | None = Field(None, gt=0)
    max_daily_return: float | None = Field(None, gt=0)
    min_daily_return: float | None = Field(None, lt=0)
    max_forward_fill_days: int | None = Field(None, ge=0, le=5)
    outlier_std_threshold: float | None = Field(None, gt=0)
    rebalance_frequency: Literal["daily", "weekly", "monthly"] | None = None
    daily_drop_threshold: float | None = Field(None, lt=0)

    @field_validator("momentum_weight", "market_cap_weight", "risk_parity_weight")
    def validate_weights(cls, v, values):
        """Ensure weights are valid when provided together."""
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "momentum_weight": 0.4,
                "market_cap_weight": 0.3,
                "risk_parity_weight": 0.3,
                "rebalance_frequency": "weekly",
            }
        }
    )


class StrategyConfigResponse(BaseModel):
    """Current strategy configuration."""

    momentum_weight: float
    market_cap_weight: float
    risk_parity_weight: float
    min_price_threshold: float
    max_daily_return: float
    min_daily_return: float
    max_forward_fill_days: int
    outlier_std_threshold: float
    rebalance_frequency: str
    daily_drop_threshold: float
    ai_adjusted: bool = False
    ai_adjustment_reason: str | None = None
    ai_confidence_score: float | None = None
    last_rebalance: datetime | None = None
    updated_at: datetime | None = None


class RiskMetric(BaseModel):
    """Individual risk metric data point."""

    date: DateType
    total_return: float
    annualized_return: float | None = None
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    current_drawdown: float
    volatility: float | None = None
    var_95: float | None = Field(None, description="95% Value at Risk")
    var_99: float | None = Field(None, description="99% Value at Risk")
    beta_sp500: float | None = Field(None, description="Beta relative to S&P 500")
    correlation_sp500: float | None = Field(
        None, description="Correlation with S&P 500"
    )


class RiskMetricsResponse(BaseModel):
    """Risk metrics response."""

    metrics: list[RiskMetric]
    message: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metrics": [
                    {
                        "date": "2024-01-15",
                        "total_return": 25.5,
                        "annualized_return": 28.3,
                        "sharpe_ratio": 1.85,
                        "sortino_ratio": 2.15,
                        "max_drawdown": 0.12,
                        "current_drawdown": 0.03,
                        "volatility": 15.2,
                    }
                ]
            }
        }
    )
