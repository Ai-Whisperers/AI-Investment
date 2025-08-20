"""
Performance tracking and database operations.
Orchestrates performance calculations and persists metrics to database.
"""

from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
from sqlalchemy.orm import Session
import logging

from ...models.index import IndexValue
from ...models.asset import Asset, Price
from ...models.strategy import RiskMetrics
from ...core.config import settings
from .return_calculator import ReturnCalculator
from .risk_metrics import RiskMetricsCalculator
from .benchmark_comparison import BenchmarkComparison

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """Track and persist portfolio performance metrics."""
    
    def __init__(self, db: Session):
        """
        Initialize performance tracker.
        
        Args:
            db: Database session
        """
        self.db = db
        self.return_calc = ReturnCalculator()
        self.risk_calc = RiskMetricsCalculator()
        self.benchmark_comp = BenchmarkComparison()

    def get_portfolio_values(
        self,
        lookback_days: Optional[int] = None
    ) -> Tuple[List[float], List[date]]:
        """
        Get portfolio values and dates from database.
        
        Args:
            lookback_days: Number of days to look back (None for all history)
            
        Returns:
            Tuple of (values, dates)
        """
        query = self.db.query(IndexValue).order_by(IndexValue.date.asc())
        
        if lookback_days:
            start_date = date.today() - timedelta(days=lookback_days)
            query = query.filter(IndexValue.date >= start_date)
        
        index_values = query.all()
        
        if not index_values:
            return [], []
        
        values = [iv.value for iv in index_values]
        dates = [iv.date for iv in index_values]
        
        return values, dates

    def get_benchmark_values(
        self,
        start_date: date,
        end_date: date,
        ticker: str = None
    ) -> List[float]:
        """
        Get benchmark values from database.
        
        Args:
            start_date: Start date for benchmark data
            end_date: End date for benchmark data
            ticker: Benchmark ticker (defaults to S&P 500)
            
        Returns:
            List of benchmark values
        """
        if ticker is None:
            ticker = settings.SP500_TICKER
        
        benchmark_asset = (
            self.db.query(Asset)
            .filter(Asset.symbol == ticker)
            .first()
        )
        
        if not benchmark_asset:
            logger.warning(f"Benchmark asset {ticker} not found")
            return []
        
        benchmark_prices = (
            self.db.query(Price)
            .filter(
                Price.asset_id == benchmark_asset.id,
                Price.date >= start_date,
                Price.date <= end_date
            )
            .order_by(Price.date.asc())
            .all()
        )
        
        if not benchmark_prices:
            return []
        
        # Normalize to base 100
        base = benchmark_prices[0].close
        return [(p.close / base) * 100 for p in benchmark_prices]

    def calculate_comprehensive_metrics(
        self,
        lookback_days: Optional[int] = None
    ) -> Dict:
        """
        Calculate comprehensive portfolio performance metrics.
        
        Args:
            lookback_days: Number of days to look back (None for all history)
            
        Returns:
            Dictionary of performance metrics
        """
        try:
            # Get portfolio data
            values, dates = self.get_portfolio_values(lookback_days)
            
            if len(values) < 2:
                logger.warning("Insufficient data for metrics calculation")
                return {}
            
            # Calculate returns
            portfolio_returns = self.return_calc.calculate_returns(values)
            
            # Basic return metrics
            metrics = {
                "total_return": self.return_calc.total_return(values),
                "annualized_return": self.return_calc.annualized_return(values),
                "start_date": dates[0].isoformat(),
                "end_date": dates[-1].isoformat(),
                "days": len(values)
            }
            
            # Risk metrics
            metrics.update({
                "sharpe_ratio": self.risk_calc.sharpe_ratio(portfolio_returns),
                "sortino_ratio": self.risk_calc.sortino_ratio(portfolio_returns),
                "volatility": self.risk_calc.volatility(portfolio_returns),
                "downside_deviation": self.risk_calc.downside_deviation(portfolio_returns),
                "value_at_risk": self.risk_calc.value_at_risk(portfolio_returns),
                "conditional_value_at_risk": self.risk_calc.conditional_value_at_risk(portfolio_returns)
            })
            
            # Drawdown metrics
            max_dd, peak_idx, trough_idx = self.risk_calc.max_drawdown(values)
            metrics.update({
                "max_drawdown": max_dd,
                "max_drawdown_peak_date": dates[peak_idx].isoformat() if peak_idx < len(dates) else None,
                "max_drawdown_trough_date": dates[trough_idx].isoformat() if trough_idx < len(dates) else None,
                "current_drawdown": self.risk_calc.current_drawdown(values),
                "calmar_ratio": self.risk_calc.calmar_ratio(portfolio_returns, max_dd / 100)
            })
            
            # Get benchmark data and calculate relative metrics
            benchmark_values = self.get_benchmark_values(dates[0], dates[-1])
            
            if benchmark_values and len(benchmark_values) >= 2:
                benchmark_returns = self.return_calc.calculate_returns(benchmark_values)
                
                # Benchmark comparison metrics
                beta = self.benchmark_comp.beta(portfolio_returns, benchmark_returns)
                metrics.update({
                    "beta": beta,
                    "alpha": self.benchmark_comp.alpha(portfolio_returns, benchmark_returns, beta),
                    "information_ratio": self.benchmark_comp.information_ratio(
                        portfolio_returns, benchmark_returns
                    ),
                    "correlation_sp500": self.benchmark_comp.correlation(
                        portfolio_returns, benchmark_returns
                    ),
                    "tracking_error": self.benchmark_comp.tracking_error(
                        portfolio_returns, benchmark_returns
                    ),
                    "treynor_ratio": self.benchmark_comp.treynor_ratio(
                        portfolio_returns, benchmark_returns, beta
                    ),
                    "upside_capture": self.benchmark_comp.capture_ratio(
                        portfolio_returns, benchmark_returns, upside=True
                    ),
                    "downside_capture": self.benchmark_comp.capture_ratio(
                        portfolio_returns, benchmark_returns, upside=False
                    ),
                    "benchmark_total_return": self.return_calc.total_return(benchmark_values),
                    "excess_return": metrics["total_return"] - self.return_calc.total_return(benchmark_values)
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate portfolio metrics: {e}")
            return {}

    def save_metrics_to_database(self, metrics: Dict) -> bool:
        """
        Save calculated metrics to database.
        
        Args:
            metrics: Dictionary of metrics to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create or update today's risk metrics
            risk_metrics = RiskMetrics(
                date=date.today(),
                sharpe_ratio=metrics.get("sharpe_ratio", 0.0),
                sortino_ratio=metrics.get("sortino_ratio", 0.0),
                max_drawdown=metrics.get("max_drawdown", 0.0) / 100,  # Store as decimal
                current_drawdown=metrics.get("current_drawdown", 0.0) / 100,  # Store as decimal
                volatility=metrics.get("volatility", 0.0),
                beta_sp500=metrics.get("beta", 1.0),
                correlation_sp500=metrics.get("correlation_sp500", 0.0),
                total_return=metrics.get("total_return", 0.0),
                annualized_return=metrics.get("annualized_return", 0.0)
            )
            
            # Check if metrics for today already exist
            existing = (
                self.db.query(RiskMetrics)
                .filter(RiskMetrics.date == date.today())
                .first()
            )
            
            if existing:
                # Update existing record
                for key, value in metrics.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                # Add new record
                self.db.add(risk_metrics)
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save metrics to database: {e}")
            self.db.rollback()
            return False

    def get_rolling_metrics(self, window: int = 30) -> List[Dict]:
        """
        Calculate rolling performance metrics.
        
        Args:
            window: Rolling window size in days
            
        Returns:
            List of metrics for each window
        """
        try:
            values, dates = self.get_portfolio_values()
            
            if len(values) < window:
                return []
            
            rolling_metrics = []
            
            for i in range(window, len(values)):
                window_values = values[i - window:i]
                window_returns = self.return_calc.calculate_returns(window_values)
                
                if len(window_returns) > 0:
                    rolling_metrics.append({
                        "date": dates[i].isoformat(),
                        "sharpe_ratio": self.risk_calc.sharpe_ratio(window_returns),
                        "sortino_ratio": self.risk_calc.sortino_ratio(window_returns),
                        "volatility": self.risk_calc.volatility(window_returns, annualized=False),
                        "return": self.return_calc.total_return(window_values)
                    })
            
            return rolling_metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate rolling metrics: {e}")
            return []


# Import for backward compatibility
from typing import Tuple