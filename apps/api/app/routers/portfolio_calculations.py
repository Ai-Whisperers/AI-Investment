"""
Portfolio calculation endpoints.
Provides backend calculation services to replace frontend calculations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel
import numpy as np

from ..core.database import get_db
from ..models.user import User
from ..utils.token_dep import get_current_user
from ..services.performance_modules.return_calculator import ReturnCalculator
from ..services.performance_modules.risk_metrics import RiskMetricsCalculator

router = APIRouter(prefix="/calculations", tags=["calculations"])


class CalculateReturnsRequest(BaseModel):
    values: List[float]


class CalculateReturnsResponse(BaseModel):
    returns: List[float]


class CalculateTotalReturnRequest(BaseModel):
    start_value: float
    end_value: float


class CalculateTotalReturnResponse(BaseModel):
    total_return: float


class CalculateAnnualizedReturnRequest(BaseModel):
    total_return: float
    period_in_days: int


class CalculateAnnualizedReturnResponse(BaseModel):
    annualized_return: float


class CalculateVolatilityRequest(BaseModel):
    returns: List[float]


class CalculateVolatilityResponse(BaseModel):
    volatility: float


class CalculateSharpeRatioRequest(BaseModel):
    annualized_return: float
    volatility: float
    risk_free_rate: Optional[float] = 2.0


class CalculateSharpeRatioResponse(BaseModel):
    sharpe_ratio: float


class CalculateMaxDrawdownRequest(BaseModel):
    values: List[float]


class CalculateMaxDrawdownResponse(BaseModel):
    max_drawdown: float
    current_drawdown: float


class CalculatePortfolioMetricsRequest(BaseModel):
    values: List[float]
    period_in_days: int


class PerformanceMetrics(BaseModel):
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    current_drawdown: float


class CalculatePortfolioMetricsResponse(BaseModel):
    metrics: PerformanceMetrics


@router.post("/returns", response_model=CalculateReturnsResponse)
def calculate_returns(
    request: CalculateReturnsRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Calculate daily returns from price series."""
    try:
        if len(request.values) < 2:
            return CalculateReturnsResponse(returns=[])
        
        returns = ReturnCalculator.calculate_returns(request.values)
        return CalculateReturnsResponse(returns=returns.tolist())
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")


@router.post("/total-return", response_model=CalculateTotalReturnResponse)
def calculate_total_return(
    request: CalculateTotalReturnRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Calculate total return between two values."""
    try:
        if request.start_value == 0:
            raise HTTPException(status_code=400, detail="Start value cannot be zero")
        
        total_return = ((request.end_value - request.start_value) / request.start_value) * 100
        return CalculateTotalReturnResponse(total_return=total_return)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")


@router.post("/annualized-return", response_model=CalculateAnnualizedReturnResponse)
def calculate_annualized_return(
    request: CalculateAnnualizedReturnRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Calculate annualized return from total return and period."""
    try:
        if request.period_in_days <= 0:
            raise HTTPException(status_code=400, detail="Period must be positive")
        
        years_elapsed = request.period_in_days / 365
        annualized_return = (((1 + request.total_return / 100) ** (1 / years_elapsed)) - 1) * 100
        return CalculateAnnualizedReturnResponse(annualized_return=annualized_return)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")


@router.post("/volatility", response_model=CalculateVolatilityResponse)
def calculate_volatility(
    request: CalculateVolatilityRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Calculate annualized volatility from returns."""
    try:
        if len(request.returns) == 0:
            return CalculateVolatilityResponse(volatility=0.0)
        
        returns_array = np.array(request.returns)
        volatility = RiskMetricsCalculator.volatility(returns_array, annualized=True)
        return CalculateVolatilityResponse(volatility=volatility * 100)  # Convert to percentage
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")


@router.post("/sharpe-ratio", response_model=CalculateSharpeRatioResponse)
def calculate_sharpe_ratio(
    request: CalculateSharpeRatioRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Calculate Sharpe ratio."""
    try:
        if request.volatility == 0:
            return CalculateSharpeRatioResponse(sharpe_ratio=0.0)
        
        # Convert percentages to decimals for calculation
        annual_return_decimal = request.annualized_return / 100
        volatility_decimal = request.volatility / 100
        risk_free_decimal = request.risk_free_rate / 100
        
        sharpe_ratio = (annual_return_decimal - risk_free_decimal) / volatility_decimal
        return CalculateSharpeRatioResponse(sharpe_ratio=sharpe_ratio)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")


@router.post("/max-drawdown", response_model=CalculateMaxDrawdownResponse)
def calculate_max_drawdown(
    request: CalculateMaxDrawdownRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Calculate maximum and current drawdown."""
    try:
        if len(request.values) == 0:
            return CalculateMaxDrawdownResponse(max_drawdown=0.0, current_drawdown=0.0)
        
        max_dd, _, _ = RiskMetricsCalculator.max_drawdown(request.values)
        current_dd = RiskMetricsCalculator.current_drawdown(request.values)
        
        return CalculateMaxDrawdownResponse(
            max_drawdown=max_dd,
            current_drawdown=current_dd
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")


@router.post("/portfolio-metrics", response_model=CalculatePortfolioMetricsResponse)
def calculate_portfolio_metrics(
    request: CalculatePortfolioMetricsRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Calculate comprehensive portfolio performance metrics."""
    try:
        if len(request.values) < 2:
            return CalculatePortfolioMetricsResponse(
                metrics=PerformanceMetrics(
                    total_return=0.0,
                    annualized_return=0.0,
                    volatility=0.0,
                    sharpe_ratio=0.0,
                    max_drawdown=0.0,
                    current_drawdown=0.0
                )
            )
        
        # Calculate returns
        returns = ReturnCalculator.calculate_returns(request.values)
        
        # Calculate total return
        total_return = ((request.values[-1] - request.values[0]) / request.values[0]) * 100
        
        # Calculate annualized return
        years_elapsed = request.period_in_days / 365
        annualized_return = (((1 + total_return / 100) ** (1 / years_elapsed)) - 1) * 100 if years_elapsed > 0 else 0
        
        # Calculate volatility
        volatility = RiskMetricsCalculator.volatility(returns, annualized=True) * 100
        
        # Calculate Sharpe ratio
        if volatility == 0:
            sharpe_ratio = 0.0
        else:
            sharpe_ratio = (annualized_return - 2.0) / volatility  # Default 2% risk-free rate
        
        # Calculate drawdowns
        max_dd, _, _ = RiskMetricsCalculator.max_drawdown(request.values)
        current_dd = RiskMetricsCalculator.current_drawdown(request.values)
        
        metrics = PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_dd,
            current_drawdown=current_dd
        )
        
        return CalculatePortfolioMetricsResponse(metrics=metrics)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")