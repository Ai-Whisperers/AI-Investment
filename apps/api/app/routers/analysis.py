"""API endpoints for technical and fundamental analysis."""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
import pandas as pd
from datetime import datetime, timedelta

from ..core.database import get_db
from ..models import Asset, Price, User
from ..repositories.asset_repository import SQLAssetRepository
from ..repositories.price_repository import SQLPriceRepository
from ..utils.token_dep import get_current_user
from ..services.technical_indicators import TechnicalIndicators
from ..services.fundamental_analysis import FundamentalAnalysis

router = APIRouter()


@router.get("/technical/{symbol}")
def get_technical_analysis(
    symbol: str,
    period: int = Query(100, description="Number of days of price history to analyze"),
    limit: Optional[int] = Query(None, description="Maximum number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive technical analysis for an asset.
    
    This endpoint is now a pure presentation layer following Clean Architecture.
    All business logic has been moved to domain services and use cases.
    """
    # Import use case
    from ..use_cases import (
        GetTechnicalAnalysisUseCase,
        AssetNotFoundError,
        InsufficientPriceDataError
    )
    
    # Create and execute use case
    use_case = GetTechnicalAnalysisUseCase(db)
    
    try:
        # Execute use case - all business logic is encapsulated
        result = use_case.execute(
            symbol=symbol, 
            period=period,
            limit=limit,
            offset=offset
        )
        
        # Convert domain result to API response
        return {
            'symbol': result.symbol,
            'period_days': result.period_days,
            'latest_price': result.latest_price,
            'indicators': result.indicators,
            'signals': result.signals,
            'dates': result.dates,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': len(result.dates) if hasattr(result, 'dates') else 0
            }
        }
        
    except AssetNotFoundError as e:
        # Handle domain-specific exceptions
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InsufficientPriceDataError as e:
        # Handle insufficient data error
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        # Handle validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during technical analysis"
        )


@router.get("/technical/{symbol}/rsi")
def get_rsi(
    symbol: str,
    period: int = Query(14, description="RSI period"),
    days: int = Query(100, description="Number of days of history"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get Relative Strength Index for an asset.
    
    This endpoint is now a pure presentation layer following Clean Architecture.
    All business logic has been moved to domain services and use cases.
    """
    from ..use_cases.technical_indicators_use_cases import (
        GetRSIUseCase,
        AssetNotFoundError as RSIAssetNotFoundError,
        InsufficientDataError
    )
    
    # Create and execute use case
    use_case = GetRSIUseCase(db)
    
    try:
        # Execute use case - all business logic is encapsulated
        result = use_case.execute(symbol=symbol, period=period, days=days)
        return result
        
    except RSIAssetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InsufficientDataError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating RSI: {str(e)}"
        )


@router.get("/technical/{symbol}/macd")
def get_macd(
    symbol: str,
    fast: int = Query(12, description="Fast EMA period"),
    slow: int = Query(26, description="Slow EMA period"),
    signal: int = Query(9, description="Signal EMA period"),
    days: int = Query(100, description="Number of days of history"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get MACD indicator for an asset."""
    # Initialize repositories
    asset_repo = SQLAssetRepository(db)
    price_repo = SQLPriceRepository(db)
    
    # Get asset using repository
    asset = asset_repo.get_by_symbol(symbol)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {symbol} not found"
        )
    
    # Get price history using repository
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    prices = price_repo.get_history(
        asset_id=asset.id,
        start_date=start_date,
        end_date=end_date
    )
    
    if not prices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data available for {symbol}"
        )
    
    # Calculate MACD
    price_series = pd.Series([p.close for p in prices])
    macd_data = TechnicalIndicators.calculate_macd(price_series, fast, slow, signal)
    
    # Determine signal
    histogram = macd_data['histogram'].iloc[-1]
    prev_histogram = macd_data['histogram'].iloc[-2] if len(macd_data['histogram']) > 1 else 0
    
    if histogram > 0 and prev_histogram <= 0:
        macd_signal = 'bullish_crossover'
    elif histogram < 0 and prev_histogram >= 0:
        macd_signal = 'bearish_crossover'
    elif histogram > 0:
        macd_signal = 'bullish'
    else:
        macd_signal = 'bearish'
    
    return {
        'symbol': symbol.upper(),
        'parameters': {'fast': fast, 'slow': slow, 'signal': signal},
        'current_signal': macd_signal,
        'macd_line': macd_data['macd'].to_list(),
        'signal_line': macd_data['signal'].to_list(),
        'histogram': macd_data['histogram'].to_list(),
        'dates': [p.date.strftime('%Y-%m-%d') for p in prices]
    }


@router.get("/technical/{symbol}/bollinger")
def get_bollinger_bands(
    symbol: str,
    period: int = Query(20, description="SMA period"),
    std_dev: float = Query(2.0, description="Number of standard deviations"),
    days: int = Query(100, description="Number of days of history"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get Bollinger Bands for an asset."""
    # Initialize repositories
    asset_repo = SQLAssetRepository(db)
    price_repo = SQLPriceRepository(db)
    
    # Get asset using repository
    asset = asset_repo.get_by_symbol(symbol)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {symbol} not found"
        )
    
    # Get price history
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    prices = price_repo.get_history(
        asset_id=asset.id,
        start_date=start_date,
        end_date=end_date
    )
    
    if not prices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data available for {symbol}"
        )
    
    # Calculate Bollinger Bands
    price_series = pd.Series([p.close for p in prices])
    bb_data = TechnicalIndicators.calculate_bollinger_bands(price_series, period, std_dev)
    
    # Determine signal
    latest_price = price_series.iloc[-1]
    upper_band = bb_data['upper'].iloc[-1]
    lower_band = bb_data['lower'].iloc[-1]
    
    if latest_price > upper_band:
        bb_signal = 'overbought'
    elif latest_price < lower_band:
        bb_signal = 'oversold'
    else:
        bb_signal = 'neutral'
    
    return {
        'symbol': symbol.upper(),
        'parameters': {'period': period, 'std_dev': std_dev},
        'current_price': float(latest_price),
        'current_signal': bb_signal,
        'upper_band': bb_data['upper'].to_list(),
        'middle_band': bb_data['middle'].to_list(),
        'lower_band': bb_data['lower'].to_list(),
        'bandwidth': bb_data['bandwidth'].to_list(),
        'dates': [p.date.strftime('%Y-%m-%d') for p in prices]
    }


@router.get("/technical/{symbol}/support-resistance")
def get_support_resistance(
    symbol: str,
    window: int = Query(20, description="Window size for finding levels"),
    min_touches: int = Query(2, description="Minimum touches to confirm level"),
    days: int = Query(200, description="Number of days of history"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Identify support and resistance levels for an asset."""
    # Initialize repositories
    asset_repo = SQLAssetRepository(db)
    price_repo = SQLPriceRepository(db)
    
    # Get asset using repository
    asset = asset_repo.get_by_symbol(symbol)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {symbol} not found"
        )
    
    # Get price history
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    prices = price_repo.get_history(
        asset_id=asset.id,
        start_date=start_date,
        end_date=end_date
    )
    
    if not prices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data available for {symbol}"
        )
    
    # Calculate support and resistance
    price_series = pd.Series([p.close for p in prices])
    levels = TechnicalIndicators.identify_support_resistance(price_series, window, min_touches)
    
    current_price = float(price_series.iloc[-1])
    
    # Find nearest levels
    nearest_support = None
    nearest_resistance = None
    
    for support in sorted(levels['support'], reverse=True):
        if support < current_price:
            nearest_support = support
            break
    
    for resistance in sorted(levels['resistance']):
        if resistance > current_price:
            nearest_resistance = resistance
            break
    
    return {
        'symbol': symbol.upper(),
        'current_price': current_price,
        'support_levels': levels['support'],
        'resistance_levels': levels['resistance'],
        'nearest_support': nearest_support,
        'nearest_resistance': nearest_resistance,
        'analysis_period_days': days
    }


@router.get("/fundamental/{symbol}")
def get_fundamental_analysis(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get fundamental analysis for an asset."""
    fundamental_service = FundamentalAnalysis(db)
    return fundamental_service.get_asset_fundamentals(symbol)


@router.get("/fundamental/{symbol}/valuation")
def get_valuation_metrics(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get valuation metrics for an asset."""
    # Initialize repositories
    asset_repo = SQLAssetRepository(db)
    price_repo = SQLPriceRepository(db)
    
    # Get asset using repository
    asset = asset_repo.get_by_symbol(symbol)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {symbol} not found"
        )
    
    # Get latest price using repository
    latest_price = price_repo.get_latest(asset_id=asset.id)
    
    if not latest_price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data available for {symbol}"
        )
    
    # Mock financial data (in production, fetch from financial APIs)
    eps = 5.25  # Earnings per share
    book_value = 35.50  # Book value per share
    revenue = asset.market_cap * 0.8 if asset.market_cap else 1000000000  # Mock revenue
    
    # Calculate valuation metrics
    valuation = {
        'symbol': symbol.upper(),
        'current_price': float(latest_price.close),
        'market_cap': asset.market_cap,
        'pe_ratio': FundamentalAnalysis.calculate_pe_ratio(latest_price.close, eps),
        'price_to_book': FundamentalAnalysis.calculate_price_to_book(latest_price.close, book_value),
        'price_to_sales': FundamentalAnalysis.calculate_price_to_sales(asset.market_cap, revenue) if asset.market_cap else None,
        'dividend_yield': asset.dividend_yield,
        'sector_average_pe': 22.5,  # Mock sector average
        'valuation_assessment': 'fair' if asset.pe_ratio and 15 < asset.pe_ratio < 25 else 'review_needed'
    }
    
    return valuation


@router.get("/fundamental/{symbol}/growth")
def get_growth_metrics(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get growth metrics for an asset."""
    # Initialize repositories
    asset_repo = SQLAssetRepository(db)
    price_repo = SQLPriceRepository(db)
    
    # Get asset using repository
    asset = asset_repo.get_by_symbol(symbol)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {symbol} not found"
        )
    
    # Mock growth data (in production, fetch from financial APIs)
    current_revenue = 5000000000
    previous_revenue = 4200000000
    current_earnings = 800000000
    previous_earnings = 650000000
    
    # Calculate growth metrics
    growth = {
        'symbol': symbol.upper(),
        'revenue_growth_yoy': FundamentalAnalysis.calculate_revenue_growth(current_revenue, previous_revenue),
        'earnings_growth_yoy': FundamentalAnalysis.calculate_earnings_growth(current_earnings, previous_earnings),
        'peg_ratio': FundamentalAnalysis.calculate_peg_ratio(
            asset.pe_ratio, 
            FundamentalAnalysis.calculate_earnings_growth(current_earnings, previous_earnings)
        ) if asset.pe_ratio else None,
        'growth_assessment': 'high_growth' if FundamentalAnalysis.calculate_revenue_growth(current_revenue, previous_revenue) > 15 else 'moderate_growth'
    }
    
    return growth


@router.get("/fundamental/{symbol}/financial-health")
def get_financial_health(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get financial health assessment for an asset."""
    # Initialize repositories
    asset_repo = SQLAssetRepository(db)
    price_repo = SQLPriceRepository(db)
    
    # Get asset using repository
    asset = asset_repo.get_by_symbol(symbol)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {symbol} not found"
        )
    
    # Mock financial data (in production, fetch from financial APIs)
    metrics = {
        'pe_ratio': asset.pe_ratio or 18.5,
        'current_ratio': 1.8,
        'debt_to_equity': 0.6,
        'roe': 15.5,
        'revenue_growth': 12.3,
        'operating_margin': 22.1,
        'free_cash_flow': 1200000000
    }
    
    # Evaluate financial health
    health_assessment = FundamentalAnalysis.evaluate_financial_health(metrics)
    
    return {
        'symbol': symbol.upper(),
        'metrics': metrics,
        'health_assessment': health_assessment,
        'investment_grade': health_assessment['overall'] in ['excellent', 'good']
    }


@router.get("/screener/technical")
def screen_technical(
    rsi_oversold: Optional[float] = Query(30, description="RSI oversold threshold"),
    rsi_overbought: Optional[float] = Query(70, description="RSI overbought threshold"),
    above_sma_200: Optional[bool] = Query(None, description="Price above 200-day SMA"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Screen assets based on technical indicators."""
    # Initialize repositories
    asset_repo = SQLAssetRepository(db)
    price_repo = SQLPriceRepository(db)
    
    # Get all assets with recent price data
    assets = asset_repo.get_all(limit=limit)
    
    results = []
    for asset in assets:
        if not asset.symbol:  # Skip assets without symbols
            continue
        # Get recent prices using repository
        prices = price_repo.get_history(
            asset_id=asset.id,
            limit=200
        )
        prices = list(reversed(prices))  # Repository returns in ascending order
        
        if len(prices) < 14:  # Need at least 14 days for RSI
            continue
        
        price_series = pd.Series([p.close for p in reversed(prices)])
        
        # Calculate indicators
        rsi = TechnicalIndicators.calculate_rsi(price_series)
        current_rsi = float(rsi.iloc[-1])
        
        # Check conditions
        if rsi_oversold and current_rsi < rsi_oversold:
            signal = 'oversold'
        elif rsi_overbought and current_rsi > rsi_overbought:
            signal = 'overbought'
        else:
            signal = 'neutral'
        
        if above_sma_200 is not None:
            sma_200 = TechnicalIndicators.calculate_sma(price_series, 200)
            if above_sma_200 and price_series.iloc[-1] <= sma_200.iloc[-1]:
                continue
            elif not above_sma_200 and price_series.iloc[-1] >= sma_200.iloc[-1]:
                continue
        
        results.append({
            'symbol': asset.symbol,
            'name': asset.name,
            'current_price': float(price_series.iloc[-1]),
            'rsi': current_rsi,
            'signal': signal,
            'sector': asset.sector
        })
    
    return results


@router.get("/screener/value")
def screen_value_stocks(
    max_pe: Optional[float] = Query(20, description="Maximum P/E ratio"),
    min_dividend_yield: Optional[float] = Query(None, description="Minimum dividend yield"),
    min_roe: Optional[float] = Query(10, description="Minimum ROE"),
    sectors: Optional[List[str]] = Query(None, description="Sectors to include"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Screen for value stocks based on fundamental metrics."""
    # Initialize repository
    asset_repo = SQLAssetRepository(db)
    
    # Note: For complex filtering, we'll get all assets and filter in memory
    # In production, this should be moved to a dedicated screening repository method
    all_assets = asset_repo.get_all()
    
    # Apply filters in memory
    filtered_assets = all_assets
    
    if max_pe:
        filtered_assets = [a for a in filtered_assets if a.pe_ratio and a.pe_ratio <= max_pe]
    
    if min_dividend_yield:
        filtered_assets = [a for a in filtered_assets if a.dividend_yield and a.dividend_yield >= min_dividend_yield]
    
    if sectors:
        filtered_assets = [a for a in filtered_assets if a.sector in sectors]
    
    # Limit results
    assets = filtered_assets[:limit]
    
    results = []
    for asset in assets:
        # Mock ROE calculation (in production, fetch from financial data)
        mock_roe = 15 if asset.sector == "Technology" else 12
        
        if min_roe and mock_roe < min_roe:
            continue
        
        results.append({
            'symbol': asset.symbol,
            'name': asset.name,
            'pe_ratio': asset.pe_ratio,
            'dividend_yield': asset.dividend_yield,
            'market_cap': asset.market_cap,
            'sector': asset.sector,
            'roe_estimate': mock_roe,
            'value_score': 100 - (asset.pe_ratio * 2 if asset.pe_ratio else 50)  # Simple value score
        })
    
    # Sort by value score
    results.sort(key=lambda x: x['value_score'], reverse=True)
    
    return results