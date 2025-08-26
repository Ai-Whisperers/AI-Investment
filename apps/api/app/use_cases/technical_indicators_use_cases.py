"""Use cases for technical indicator calculations.

This layer orchestrates technical analysis business logic with infrastructure concerns,
following Clean Architecture principles.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import pandas as pd

from ..repositories import IAssetRepository, IPriceRepository
from ..repositories import SQLAssetRepository, SQLPriceRepository
from ..services.technical_indicators import TechnicalIndicators


class TechnicalIndicatorError(Exception):
    """Base exception for technical indicator errors."""
    pass


class AssetNotFoundError(TechnicalIndicatorError):
    """Raised when asset is not found."""
    pass


class InsufficientDataError(TechnicalIndicatorError):
    """Raised when there's insufficient data for calculation."""
    pass


class GetRSIUseCase:
    """Use case for calculating Relative Strength Index."""
    
    def __init__(self, db: Session):
        """Initialize with database session.
        
        Args:
            db: Database session for repository access
        """
        self.asset_repo: IAssetRepository = SQLAssetRepository(db)
        self.price_repo: IPriceRepository = SQLPriceRepository(db)
    
    def execute(
        self,
        symbol: str,
        period: int = 14,
        days: int = 100
    ) -> Dict[str, Any]:
        """Calculate RSI for an asset.
        
        Args:
            symbol: Asset symbol
            period: RSI period
            days: Number of days of history
            
        Returns:
            RSI calculation results
            
        Raises:
            AssetNotFoundError: If asset not found
            InsufficientDataError: If insufficient price data
        """
        # Get asset from repository
        asset = self.asset_repo.get_by_symbol(symbol)
        if not asset:
            raise AssetNotFoundError(f"Asset {symbol} not found")
        
        # Get price history
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        prices = self.price_repo.get_history(
            asset_id=asset.id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not prices:
            raise InsufficientDataError(f"No price data available for {symbol}")
        
        # Calculate RSI
        price_series = pd.Series([p.close for p in prices])
        rsi_values = TechnicalIndicators.calculate_rsi(price_series, period)
        
        # Determine signal
        latest_rsi = rsi_values.iloc[-1]
        signal = self._determine_rsi_signal(latest_rsi)
        
        return {
            'symbol': symbol.upper(),
            'period': period,
            'current_rsi': float(latest_rsi),
            'signal': signal,
            'rsi_history': rsi_values.tolist(),
            'dates': [p.date.isoformat() for p in prices]
        }
    
    def _determine_rsi_signal(self, rsi: float) -> str:
        """Determine signal based on RSI value."""
        if rsi > 70:
            return 'overbought'
        elif rsi < 30:
            return 'oversold'
        else:
            return 'neutral'


class GetMACDUseCase:
    """Use case for calculating MACD indicator."""
    
    def __init__(self, db: Session):
        """Initialize with database session.
        
        Args:
            db: Database session for repository access
        """
        self.asset_repo: IAssetRepository = SQLAssetRepository(db)
        self.price_repo: IPriceRepository = SQLPriceRepository(db)
    
    def execute(
        self,
        symbol: str,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        days: int = 100
    ) -> Dict[str, Any]:
        """Calculate MACD for an asset.
        
        Args:
            symbol: Asset symbol
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            days: Number of days of history
            
        Returns:
            MACD calculation results
            
        Raises:
            AssetNotFoundError: If asset not found
            InsufficientDataError: If insufficient price data
        """
        # Get asset from repository
        asset = self.asset_repo.get_by_symbol(symbol)
        if not asset:
            raise AssetNotFoundError(f"Asset {symbol} not found")
        
        # Get price history
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        prices = self.price_repo.get_history(
            asset_id=asset.id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not prices:
            raise InsufficientDataError(f"No price data available for {symbol}")
        
        # Calculate MACD
        price_series = pd.Series([p.close for p in prices])
        macd, signal, histogram = TechnicalIndicators.calculate_macd(
            price_series, fast_period, slow_period, signal_period
        )
        
        # Determine signal
        latest_histogram = histogram.iloc[-1]
        signal_type = self._determine_macd_signal(latest_histogram, histogram)
        
        return {
            'symbol': symbol.upper(),
            'fast_period': fast_period,
            'slow_period': slow_period,
            'signal_period': signal_period,
            'current_macd': float(macd.iloc[-1]),
            'current_signal': float(signal.iloc[-1]),
            'current_histogram': float(latest_histogram),
            'signal': signal_type,
            'macd_history': macd.tolist(),
            'signal_history': signal.tolist(),
            'histogram_history': histogram.tolist(),
            'dates': [p.date.isoformat() for p in prices]
        }
    
    def _determine_macd_signal(self, latest: float, histogram: pd.Series) -> str:
        """Determine signal based on MACD histogram."""
        if len(histogram) < 2:
            return 'neutral'
        
        prev = histogram.iloc[-2]
        if latest > 0 and prev <= 0:
            return 'bullish_crossover'
        elif latest < 0 and prev >= 0:
            return 'bearish_crossover'
        elif latest > 0:
            return 'bullish'
        else:
            return 'bearish'


class GetBollingerBandsUseCase:
    """Use case for calculating Bollinger Bands."""
    
    def __init__(self, db: Session):
        """Initialize with database session.
        
        Args:
            db: Database session for repository access
        """
        self.asset_repo: IAssetRepository = SQLAssetRepository(db)
        self.price_repo: IPriceRepository = SQLPriceRepository(db)
    
    def execute(
        self,
        symbol: str,
        period: int = 20,
        std_dev: int = 2,
        days: int = 100
    ) -> Dict[str, Any]:
        """Calculate Bollinger Bands for an asset.
        
        Args:
            symbol: Asset symbol
            period: Moving average period
            std_dev: Standard deviation multiplier
            days: Number of days of history
            
        Returns:
            Bollinger Bands calculation results
            
        Raises:
            AssetNotFoundError: If asset not found
            InsufficientDataError: If insufficient price data
        """
        # Get asset from repository
        asset = self.asset_repo.get_by_symbol(symbol)
        if not asset:
            raise AssetNotFoundError(f"Asset {symbol} not found")
        
        # Get price history
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        prices = self.price_repo.get_history(
            asset_id=asset.id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not prices:
            raise InsufficientDataError(f"No price data available for {symbol}")
        
        # Calculate Bollinger Bands
        price_series = pd.Series([p.close for p in prices])
        upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(
            price_series, period, std_dev
        )
        
        # Determine signal
        current_price = price_series.iloc[-1]
        signal = self._determine_bb_signal(current_price, upper.iloc[-1], lower.iloc[-1])
        
        return {
            'symbol': symbol.upper(),
            'period': period,
            'std_dev': std_dev,
            'current_price': float(current_price),
            'upper_band': float(upper.iloc[-1]),
            'middle_band': float(middle.iloc[-1]),
            'lower_band': float(lower.iloc[-1]),
            'signal': signal,
            'upper_band_history': upper.tolist(),
            'middle_band_history': middle.tolist(),
            'lower_band_history': lower.tolist(),
            'price_history': price_series.tolist(),
            'dates': [p.date.isoformat() for p in prices]
        }
    
    def _determine_bb_signal(self, price: float, upper: float, lower: float) -> str:
        """Determine signal based on Bollinger Bands position."""
        band_width = upper - lower
        position = (price - lower) / band_width if band_width > 0 else 0.5
        
        if position > 0.95:
            return 'strong_overbought'
        elif position > 0.8:
            return 'overbought'
        elif position < 0.05:
            return 'strong_oversold'
        elif position < 0.2:
            return 'oversold'
        else:
            return 'neutral'