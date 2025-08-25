"""
Performance Metrics Tracking Service
Tracks actual vs expected returns, validates strategy effectiveness
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from app.models.signals import Signal
from app.models.portfolio import Portfolio
from app.models.asset import Price
from app.core.cache import get_cache

logger = logging.getLogger(__name__)


@dataclass
class SignalPerformance:
    """Performance metrics for a single signal."""
    ticker: str
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    expected_return: float
    actual_return: Optional[float]
    holding_period: Optional[int]  # days
    status: str  # 'active', 'closed', 'stopped_out'
    signal_type: str
    confidence: float


@dataclass
class StrategyPerformance:
    """Performance metrics for a strategy."""
    strategy_name: str
    total_signals: int
    winning_signals: int
    losing_signals: int
    win_rate: float
    average_win: float
    average_loss: float
    profit_factor: float  # Total wins / Total losses
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    annualized_return: float


@dataclass
class PortfolioPerformance:
    """Overall portfolio performance metrics."""
    total_value: float
    daily_return: float
    weekly_return: float
    monthly_return: float
    ytd_return: float
    all_time_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    current_drawdown: float
    beta: float  # vs S&P 500
    alpha: float  # Excess return vs benchmark
    win_rate: float
    active_positions: int


class PerformanceTracker:
    """Tracks and analyzes performance metrics."""
    
    def __init__(self):
        self.cache = get_cache()
        self.benchmark_ticker = "SPY"  # S&P 500 ETF
        
    async def track_signal_performance(
        self,
        signal: Signal,
        db: Session
    ) -> SignalPerformance:
        """Track performance of a single signal."""
        
        # Get entry price (when signal was created)
        entry_date = signal.created_at.date()
        entry_price_obj = db.query(Price).filter(
            and_(
                Price.asset_id == signal.asset_id,
                Price.date >= entry_date
            )
        ).order_by(Price.date.asc()).first()
        
        if not entry_price_obj:
            logger.warning(f"No price data for signal {signal.ticker} on {entry_date}")
            return None
            
        entry_price = float(entry_price_obj.close)
        
        # Get current/exit price
        if signal.executed and signal.exit_date:
            # Signal has been closed
            exit_price_obj = db.query(Price).filter(
                and_(
                    Price.asset_id == signal.asset_id,
                    Price.date >= signal.exit_date
                )
            ).order_by(Price.date.asc()).first()
            
            if exit_price_obj:
                exit_price = float(exit_price_obj.close)
                exit_date = signal.exit_date
                status = 'closed'
            else:
                exit_price = None
                exit_date = None
                status = 'active'
        else:
            # Signal is still active - get latest price
            latest_price = db.query(Price).filter(
                Price.asset_id == signal.asset_id
            ).order_by(Price.date.desc()).first()
            
            if latest_price:
                exit_price = float(latest_price.close)
                exit_date = latest_price.date
                status = 'active'
            else:
                exit_price = None
                exit_date = None
                status = 'pending'
                
        # Calculate returns
        if exit_price and entry_price:
            actual_return = (exit_price - entry_price) / entry_price
            holding_period = (exit_date - entry_date).days if exit_date else 0
        else:
            actual_return = None
            holding_period = None
            
        # Check if stopped out
        if signal.stop_loss and exit_price:
            stop_price = entry_price * (1 + signal.stop_loss)
            if exit_price <= stop_price:
                status = 'stopped_out'
                
        performance = SignalPerformance(
            ticker=signal.ticker,
            entry_date=signal.created_at,
            exit_date=exit_date,
            entry_price=entry_price,
            exit_price=exit_price,
            expected_return=signal.expected_return,
            actual_return=actual_return,
            holding_period=holding_period,
            status=status,
            signal_type=signal.signal_type,
            confidence=signal.confidence
        )
        
        # Update signal record with actual performance
        if actual_return is not None and signal.result is None:
            signal.result = actual_return
            db.commit()
            
        # Cache performance data
        await self._cache_performance(signal.ticker, performance)
        
        return performance
        
    async def analyze_strategy_performance(
        self,
        strategy_name: str,
        db: Session,
        days: int = 90
    ) -> StrategyPerformance:
        """Analyze performance of a specific strategy."""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all signals for this strategy
        signals = db.query(Signal).filter(
            and_(
                Signal.signal_type == strategy_name,
                Signal.created_at >= cutoff_date
            )
        ).all()
        
        if not signals:
            return None
            
        # Track individual performances
        performances = []
        for signal in signals:
            perf = await self.track_signal_performance(signal, db)
            if perf and perf.actual_return is not None:
                performances.append(perf)
                
        if not performances:
            return None
            
        # Calculate metrics
        returns = [p.actual_return for p in performances]
        winning = [r for r in returns if r > 0]
        losing = [r for r in returns if r <= 0]
        
        win_rate = len(winning) / len(returns) * 100 if returns else 0
        avg_win = np.mean(winning) if winning else 0
        avg_loss = np.mean(losing) if losing else 0
        
        # Profit factor
        total_wins = sum(winning) if winning else 0
        total_losses = abs(sum(losing)) if losing else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Sharpe ratio (simplified - assuming risk-free rate of 2%)
        if len(returns) > 1:
            excess_returns = [r - 0.02/365 for r in returns]  # Daily risk-free rate
            sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252) if np.std(excess_returns) > 0 else 0
        else:
            sharpe = 0
            
        # Maximum drawdown
        cumulative_returns = np.cumprod([1 + r for r in returns])
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
        
        # Total and annualized returns
        total_return = np.prod([1 + r for r in returns]) - 1
        years = days / 365
        annualized_return = (1 + total_return) ** (1/years) - 1 if years > 0 else total_return
        
        return StrategyPerformance(
            strategy_name=strategy_name,
            total_signals=len(signals),
            winning_signals=len(winning),
            losing_signals=len(losing),
            win_rate=win_rate,
            average_win=avg_win,
            average_loss=avg_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe,
            max_drawdown=max_drawdown,
            total_return=total_return,
            annualized_return=annualized_return
        )
        
    async def calculate_portfolio_performance(
        self,
        portfolio_id: int,
        db: Session
    ) -> PortfolioPerformance:
        """Calculate comprehensive portfolio performance metrics."""
        
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            return None
            
        # Get portfolio value history
        values = await self._get_portfolio_values(portfolio_id, db)
        if not values:
            return None
            
        current_value = values[-1]
        
        # Calculate returns for different periods
        daily_return = self._calculate_period_return(values, 1)
        weekly_return = self._calculate_period_return(values, 7)
        monthly_return = self._calculate_period_return(values, 30)
        ytd_return = self._calculate_ytd_return(values)
        all_time_return = (current_value - values[0]) / values[0] if values[0] > 0 else 0
        
        # Calculate risk metrics
        daily_returns = self._calculate_daily_returns(values)
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        sortino_ratio = self._calculate_sortino_ratio(daily_returns)
        max_dd, current_dd = self._calculate_drawdowns(values)
        
        # Calculate beta and alpha vs benchmark
        beta, alpha = await self._calculate_beta_alpha(daily_returns, db)
        
        # Get win rate from signals
        signals = db.query(Signal).filter(
            Signal.portfolio_id == portfolio_id
        ).all()
        
        winning = len([s for s in signals if s.result and s.result > 0])
        total = len([s for s in signals if s.result is not None])
        win_rate = winning / total * 100 if total > 0 else 0
        
        # Count active positions
        active_positions = len([s for s in signals if not s.executed])
        
        return PortfolioPerformance(
            total_value=current_value,
            daily_return=daily_return,
            weekly_return=weekly_return,
            monthly_return=monthly_return,
            ytd_return=ytd_return,
            all_time_return=all_time_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_dd,
            current_drawdown=current_dd,
            beta=beta,
            alpha=alpha,
            win_rate=win_rate,
            active_positions=active_positions
        )
        
    async def validate_extreme_signals(self, db: Session) -> Dict:
        """Validate if extreme signals are meeting >30% return targets."""
        
        # Get extreme signals from last 90 days
        cutoff = datetime.utcnow() - timedelta(days=90)
        
        extreme_signals = db.query(Signal).filter(
            and_(
                Signal.expected_return >= 0.3,  # 30%+ expected
                Signal.created_at >= cutoff
            )
        ).all()
        
        if not extreme_signals:
            return {
                'total_extreme_signals': 0,
                'meeting_target': 0,
                'success_rate': 0,
                'average_actual_return': 0,
                'average_expected_return': 0
            }
            
        # Track performance
        meeting_target = 0
        actual_returns = []
        expected_returns = []
        
        for signal in extreme_signals:
            perf = await self.track_signal_performance(signal, db)
            
            if perf and perf.actual_return is not None:
                actual_returns.append(perf.actual_return)
                expected_returns.append(perf.expected_return)
                
                if perf.actual_return >= 0.3:
                    meeting_target += 1
                    
        success_rate = meeting_target / len(extreme_signals) * 100 if extreme_signals else 0
        
        return {
            'total_extreme_signals': len(extreme_signals),
            'meeting_target': meeting_target,
            'success_rate': success_rate,
            'average_actual_return': np.mean(actual_returns) if actual_returns else 0,
            'average_expected_return': np.mean(expected_returns) if expected_returns else 0,
            'performance_ratio': np.mean(actual_returns) / np.mean(expected_returns) if expected_returns and np.mean(expected_returns) > 0 else 0
        }
        
    async def generate_performance_report(self, db: Session) -> Dict:
        """Generate comprehensive performance report."""
        
        # Validate extreme signals
        extreme_validation = await self.validate_extreme_signals(db)
        
        # Analyze each strategy
        strategies = ['forty_eight_hour', 'meme_velocity', 'smart_divergence', 'extreme_event']
        strategy_performances = {}
        
        for strategy in strategies:
            perf = await self.analyze_strategy_performance(strategy, db)
            if perf:
                strategy_performances[strategy] = asdict(perf)
                
        # Get overall metrics
        all_signals = db.query(Signal).filter(
            Signal.result.isnot(None)
        ).all()
        
        overall_returns = [s.result for s in all_signals if s.result is not None]
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'extreme_signal_validation': extreme_validation,
            'strategy_performances': strategy_performances,
            'overall_metrics': {
                'total_signals': len(all_signals),
                'average_return': np.mean(overall_returns) if overall_returns else 0,
                'median_return': np.median(overall_returns) if overall_returns else 0,
                'best_return': max(overall_returns) if overall_returns else 0,
                'worst_return': min(overall_returns) if overall_returns else 0,
                'win_rate': len([r for r in overall_returns if r > 0]) / len(overall_returns) * 100 if overall_returns else 0
            },
            'target_achievement': {
                'annual_target': 35,  # 35% target
                'projected_annual': np.mean(overall_returns) * 50 * 100 if overall_returns else 0,  # Assuming 50 trades/year
                'on_track': np.mean(overall_returns) * 50 >= 0.35 if overall_returns else False
            }
        }
        
    # Helper methods
    
    async def _cache_performance(self, ticker: str, performance: SignalPerformance):
        """Cache performance data for quick access."""
        
        key = f"performance:{ticker}:{datetime.utcnow().date()}"
        await self.cache.set(key, asdict(performance), ttl=3600)  # 1 hour TTL
        
    async def _get_portfolio_values(self, portfolio_id: int, db: Session) -> List[float]:
        """Get historical portfolio values."""
        
        # This would normally query a portfolio_values table
        # For now, return simulated data
        return [100000 * (1 + 0.001 * i) for i in range(90)]  # 90 days of 0.1% daily growth
        
    def _calculate_period_return(self, values: List[float], days: int) -> float:
        """Calculate return over specified period."""
        
        if len(values) < days + 1:
            return 0
            
        return (values[-1] - values[-days-1]) / values[-days-1]
        
    def _calculate_ytd_return(self, values: List[float]) -> float:
        """Calculate year-to-date return."""
        
        days_since_year_start = datetime.utcnow().timetuple().tm_yday
        
        if len(values) < days_since_year_start:
            return (values[-1] - values[0]) / values[0]
            
        return (values[-1] - values[-days_since_year_start]) / values[-days_since_year_start]
        
    def _calculate_daily_returns(self, values: List[float]) -> List[float]:
        """Calculate daily returns from portfolio values."""
        
        returns = []
        for i in range(1, len(values)):
            returns.append((values[i] - values[i-1]) / values[i-1])
        return returns
        
    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio."""
        
        if not returns or len(returns) < 2:
            return 0
            
        excess_returns = [r - risk_free_rate/252 for r in returns]  # Daily risk-free rate
        
        if np.std(excess_returns) == 0:
            return 0
            
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        
    def _calculate_sortino_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (only considers downside volatility)."""
        
        if not returns or len(returns) < 2:
            return 0
            
        excess_returns = [r - risk_free_rate/252 for r in returns]
        downside_returns = [r for r in excess_returns if r < 0]
        
        if not downside_returns or np.std(downside_returns) == 0:
            return 0
            
        return np.mean(excess_returns) / np.std(downside_returns) * np.sqrt(252)
        
    def _calculate_drawdowns(self, values: List[float]) -> Tuple[float, float]:
        """Calculate maximum and current drawdown."""
        
        if not values:
            return 0, 0
            
        peak = values[0]
        max_dd = 0
        
        for value in values:
            if value > peak:
                peak = value
                
            dd = (peak - value) / peak
            max_dd = max(max_dd, dd)
            
        current_dd = (peak - values[-1]) / peak if peak > 0 else 0
        
        return max_dd, current_dd
        
    async def _calculate_beta_alpha(
        self,
        portfolio_returns: List[float],
        db: Session
    ) -> Tuple[float, float]:
        """Calculate beta and alpha vs S&P 500."""
        
        # This would normally fetch actual S&P 500 returns
        # For now, use simulated benchmark returns
        benchmark_returns = [0.0007 + np.random.normal(0, 0.01) for _ in portfolio_returns]
        
        if len(portfolio_returns) < 2 or len(benchmark_returns) < 2:
            return 0, 0
            
        # Calculate beta (covariance / variance)
        covariance = np.cov(portfolio_returns, benchmark_returns)[0, 1]
        benchmark_variance = np.var(benchmark_returns)
        
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
        
        # Calculate alpha (excess return above expected given beta)
        portfolio_return = np.mean(portfolio_returns) * 252  # Annualized
        benchmark_return = np.mean(benchmark_returns) * 252  # Annualized
        risk_free_rate = 0.02  # 2% annual
        
        expected_return = risk_free_rate + beta * (benchmark_return - risk_free_rate)
        alpha = portfolio_return - expected_return
        
        return beta, alpha


# Global tracker instance
_performance_tracker = None


def get_performance_tracker() -> PerformanceTracker:
    """Get or create performance tracker instance."""
    
    global _performance_tracker
    if not _performance_tracker:
        _performance_tracker = PerformanceTracker()
    return _performance_tracker