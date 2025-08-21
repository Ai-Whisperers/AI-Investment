"""Enhanced validation schemas with security constraints."""

import re
from datetime import date
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator


class SecureStrategyConfig(BaseModel):
    """Validated strategy configuration with security constraints."""

    momentum_weight: float = Field(
        default=0.4,
        ge=0.0,  # Greater than or equal to 0
        le=1.0,  # Less than or equal to 1
        description="Weight for momentum factor (0-1)",
    )

    market_cap_weight: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Weight for market cap factor (0-1)"
    )

    risk_parity_weight: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Weight for risk parity factor (0-1)"
    )

    rebalance_frequency: str = Field(
        default="monthly", description="Rebalancing frequency"
    )

    min_price_threshold: float = Field(
        default=1.0,
        ge=0.01,
        le=1000000.0,
        description="Minimum price threshold for assets",
    )

    max_daily_return: float = Field(
        default=0.5, ge=0.01, le=10.0, description="Maximum allowed daily return"
    )

    min_daily_return: float = Field(
        default=-0.5, ge=-10.0, le=-0.01, description="Minimum allowed daily return"
    )

    max_forward_fill_days: int = Field(
        default=2, ge=0, le=30, description="Maximum days to forward fill missing data"
    )

    outlier_std_threshold: float = Field(
        default=3.0,
        ge=1.0,
        le=10.0,
        description="Standard deviation threshold for outlier detection",
    )

    daily_drop_threshold: float = Field(
        default=-0.01, ge=-1.0, le=0.0, description="Daily drop threshold for alerts"
    )

    @model_validator(mode="after")
    def validate_weights(self) -> Self:
        """Ensure weights sum to approximately 1.0."""
        momentum = self.momentum_weight
        market_cap = self.market_cap_weight
        risk_parity = self.risk_parity_weight

        total = momentum + market_cap + risk_parity

        if abs(total - 1.0) > 0.001:  # Allow small floating point errors
            raise ValueError(f"Strategy weights must sum to 1.0, got {total}")

        return self

    @field_validator("rebalance_frequency")
    @classmethod
    def validate_frequency(cls, v):
        """Validate rebalancing frequency."""
        allowed = ["daily", "weekly", "monthly", "quarterly", "yearly"]
        if v.lower() not in allowed:
            raise ValueError(f"Rebalance frequency must be one of {allowed}")
        return v.lower()

    @field_validator("max_daily_return", "min_daily_return")
    @classmethod
    def validate_return_bounds(cls, v, info):
        """Ensure return bounds are reasonable."""
        if info.field_name == "max_daily_return" and v <= 0:
            raise ValueError("Max daily return must be positive")
        if info.field_name == "min_daily_return" and v >= 0:
            raise ValueError("Min daily return must be negative")
        return v


class SecureAssetSymbol(BaseModel):
    """Validated asset symbol to prevent injection attacks."""

    symbol: str = Field(
        ..., min_length=1, max_length=10, description="Asset ticker symbol"
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v):
        """Validate symbol format to prevent injection."""
        # Only allow alphanumeric, dots, and hyphens (common in tickers)
        if not re.match(r"^[A-Z0-9\.\-]+$", v.upper()):
            raise ValueError(
                "Symbol must contain only letters, numbers, dots, and hyphens"
            )

        # Prevent path traversal attempts
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Invalid symbol format")

        return v.upper()


class SecureSimulationRequest(BaseModel):
    """Validated simulation request with bounds checking."""

    amount: float = Field(
        ...,
        gt=0,  # Must be positive
        le=1000000000,  # Max 1 billion
        description="Investment amount",
    )

    currency: str = Field(
        default="USD", min_length=3, max_length=3, description="Currency code"
    )

    start_date: date | None = Field(
        default=None, description="Simulation start date"
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        """Validate currency code."""
        # Only allow uppercase letters for currency codes
        if not re.match(r"^[A-Z]{3}$", v.upper()):
            raise ValueError("Currency must be a 3-letter code")
        return v.upper()

    @field_validator("start_date")
    @classmethod
    def validate_date(cls, v):
        """Validate date is reasonable."""
        if v:
            # Don't allow dates too far in the past or future
            min_date = date(2000, 1, 1)
            max_date = date.today()

            if v < min_date:
                raise ValueError(f"Start date cannot be before {min_date}")
            if v > max_date:
                raise ValueError("Start date cannot be in the future")

        return v


class SecureRefreshMode(BaseModel):
    """Validated refresh mode."""

    mode: str = Field(default="smart", description="Refresh mode")

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v):
        """Validate refresh mode."""
        allowed_modes = ["smart", "full", "minimal", "cached", "incremental"]
        if v.lower() not in allowed_modes:
            raise ValueError(f"Mode must be one of {allowed_modes}")
        return v.lower()


class SecureReportRequest(BaseModel):
    """Validated report generation request."""

    report_type: str = Field(
        default="performance", description="Type of report to generate"
    )

    period_days: int = Field(
        default=30,
        ge=1,
        le=3650,  # Max 10 years
        description="Period in days for the report",
    )

    @field_validator("report_type")
    @classmethod
    def validate_report_type(cls, v):
        """Validate report type."""
        allowed_types = ["performance", "allocation", "risk", "summary", "detailed"]
        if v.lower() not in allowed_types:
            raise ValueError(f"Report type must be one of {allowed_types}")
        return v.lower()


def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    Sanitize string input to prevent injection attacks.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not value:
        return ""

    # Remove null bytes
    value = value.replace("\x00", "")

    # Limit length
    value = value[:max_length]

    # Remove control characters except newlines and tabs
    value = "".join(char for char in value if char in "\n\t" or not ord(char) < 32)

    # HTML escape if needed (for display)
    # This should be done at display time, not storage

    return value.strip()
