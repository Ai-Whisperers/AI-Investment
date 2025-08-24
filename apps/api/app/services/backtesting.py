"""Backtesting framework for validating investment strategies."""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from ..models import Asset, Price
from .investment_engine import (
    InvestmentDecisionEngine,
    InvestmentRecommendation,
    SignalStrength,
    InvestmentHorizon
)

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents a portfolio position."""
    symbol: str
    shares: float
    entry_price: float
    entry_date: datetime
    exit_price: Optional[float] = None
    exit_date: Optional[datetime] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    
    @property
    def is_open(self) -> bool:
        """Check if position is still open."""
        return self.exit_date is None
    
    @property
    def current_value(self, current_price: float) -> float:
        """Calculate current position value."""
        if self.is_open:
            return self.shares * current_price
        return self.shares * (self.exit_price or self.entry_price)
    
    @property
    def profit_loss(self) -> float:
        """Calculate profit/loss."""
        if self.exit_price:
            return self.shares * (self.exit_price - self.entry_price)
        return 0
    
    @property
    def return_pct(self) -> float:
        """Calculate return percentage."""
        if self.exit_price:
            return ((self.exit_price - self.entry_price) / self.entry_price) * 100
        return 0


@dataclass
class BacktestResult:
    """Results from a backtest run."""
    initial_capital: float
    final_value: float
    total_return: float
    total_return_pct: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    avg_win: float
    avg_loss: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    positions: List[Position]
    equity_curve: pd.Series
    benchmark_return: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BacktestEngine:
    """
    Engine for backtesting investment strategies.
    Simulates portfolio performance over historical data.
    """
    
    def __init__(self, db: Session, initial_capital: float = 100000):
        """
        Initialize backtest engine.
        
        Args:
            db: Database session
            initial_capital: Starting capital for simulation
        """
        self.db = db
        self.initial_capital = initial_capital
        self.investment_engine = InvestmentDecisionEngine(db)
        
        # Portfolio state
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        
        # Configuration
        self.max_position_size = 0.10  # Max 10% per position
        self.max_positions = 20  # Maximum number of concurrent positions
        self.transaction_cost = 0.001  # 0.1% transaction cost
        self.slippage = 0.001  # 0.1% slippage
    
    def run_backtest(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        rebalance_frequency: str = 'monthly',
        strategy_params: Optional[Dict] = None
    ) -> BacktestResult:
        """
        Run backtest simulation.
        
        Args:
            symbols: List of symbols to trade
            start_date: Backtest start date
            end_date: Backtest end date
            rebalance_frequency: How often to rebalance ('daily', 'weekly', 'monthly')
            strategy_params: Additional strategy parameters
            
        Returns:
            Backtest results
        """
        try:
            # Reset portfolio state
            self._reset_portfolio()
            
            # Get trading dates
            trading_dates = self._get_trading_dates(start_date, end_date, rebalance_frequency)
            
            # Run simulation
            for current_date in trading_dates:
                # Update existing positions (check stop loss, targets)
                self._update_positions(current_date)
                
                # Get new signals and rebalance
                if self._should_rebalance(current_date, rebalance_frequency):
                    self._rebalance_portfolio(symbols, current_date, strategy_params)
                
                # Record equity curve
                portfolio_value = self._calculate_portfolio_value(current_date)
                self.equity_curve.append((current_date, portfolio_value))
            
            # Close all remaining positions at end
            self._close_all_positions(end_date)
            
            # Calculate performance metrics
            result = self._calculate_performance_metrics(start_date, end_date)
            
            # Add benchmark comparison if available
            benchmark_return = self._calculate_benchmark_return(start_date, end_date)
            if benchmark_return:
                result.benchmark_return = benchmark_return
                result.alpha = result.annualized_return - benchmark_return
            
            return result
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            raise
    
    def _reset_portfolio(self):
        """Reset portfolio to initial state."""
        self.cash = self.initial_capital
        self.positions = {}
        self.closed_positions = []
        self.equity_curve = []
    
    def _get_trading_dates(
        self,
        start_date: datetime,
        end_date: datetime,
        frequency: str
    ) -> List[datetime]:
        """Get list of trading dates based on frequency."""
        dates = []
        current = start_date
        
        while current <= end_date:
            dates.append(current)
            
            if frequency == 'daily':
                current += timedelta(days=1)
            elif frequency == 'weekly':
                current += timedelta(weeks=1)
            elif frequency == 'monthly':
                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
            else:
                current += timedelta(days=30)  # Default monthly
        
        return dates
    
    def _should_rebalance(self, current_date: datetime, frequency: str) -> bool:
        """Check if portfolio should be rebalanced."""
        if frequency == 'daily':
            return True
        elif frequency == 'weekly':
            return current_date.weekday() == 0  # Monday
        elif frequency == 'monthly':
            return current_date.day <= 7  # First week of month
        return False
    
    def _update_positions(self, current_date: datetime):
        """Update existing positions - check stops and targets."""
        for symbol, position in list(self.positions.items()):
            current_price = self._get_price(symbol, current_date)
            if not current_price:
                continue
            
            # Check stop loss
            if position.stop_loss and current_price <= position.stop_loss:
                self._close_position(symbol, current_price, current_date, "Stop loss hit")
            
            # Check target price
            elif position.target_price and current_price >= position.target_price:
                self._close_position(symbol, current_price, current_date, "Target reached")
            
            # Check if position is too old (optional position timeout)
            elif (current_date - position.entry_date).days > 365:
                self._close_position(symbol, current_price, current_date, "Position timeout")
    
    def _rebalance_portfolio(
        self,
        symbols: List[str],
        current_date: datetime,
        strategy_params: Optional[Dict]
    ):
        """Rebalance portfolio based on current signals."""
        recommendations = []
        
        # Get recommendations for each symbol
        for symbol in symbols:
            try:
                # Skip if we already have maximum position
                if symbol in self.positions:
                    continue
                
                # Get investment recommendation
                rec = self.investment_engine.analyze_investment_opportunity(
                    symbol,
                    InvestmentHorizon.LONG
                )
                
                # Only consider buy signals with sufficient confidence
                if rec.action in [SignalStrength.BUY, SignalStrength.STRONG_BUY]:
                    if rec.investment_score > 60:  # Minimum score threshold
                        recommendations.append(rec)
                        
            except Exception as e:
                logger.debug(f"Could not analyze {symbol}: {e}")
                continue
        
        # Sort by investment score
        recommendations.sort(key=lambda x: x.investment_score, reverse=True)
        
        # Execute top recommendations
        for rec in recommendations[:self.max_positions - len(self.positions)]:
            self._execute_recommendation(rec, current_date)
    
    def _execute_recommendation(
        self,
        recommendation: InvestmentRecommendation,
        current_date: datetime
    ):
        """Execute an investment recommendation."""
        symbol = recommendation.symbol
        current_price = self._get_price(symbol, current_date)
        
        if not current_price:
            return
        
        # Calculate position size
        portfolio_value = self._calculate_portfolio_value(current_date)
        position_value = portfolio_value * min(
            recommendation.target_allocation,
            self.max_position_size
        )
        
        # Check if we have enough cash
        if position_value > self.cash:
            position_value = self.cash * 0.95  # Use 95% of available cash
        
        if position_value < 1000:  # Minimum position size
            return
        
        # Apply transaction costs and slippage
        entry_price = current_price * (1 + self.slippage + self.transaction_cost)
        shares = position_value / entry_price
        
        # Create position
        position = Position(
            symbol=symbol,
            shares=shares,
            entry_price=entry_price,
            entry_date=current_date,
            stop_loss=recommendation.stop_loss,
            target_price=recommendation.exit_price_target
        )
        
        # Update portfolio
        self.positions[symbol] = position
        self.cash -= position_value
        
        logger.debug(f"Opened position: {symbol} - {shares:.2f} shares at ${entry_price:.2f}")
    
    def _close_position(
        self,
        symbol: str,
        exit_price: float,
        exit_date: datetime,
        reason: str = ""
    ):
        """Close a position."""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # Apply transaction costs and slippage
        actual_exit_price = exit_price * (1 - self.slippage - self.transaction_cost)
        
        # Update position
        position.exit_price = actual_exit_price
        position.exit_date = exit_date
        
        # Update cash
        self.cash += position.shares * actual_exit_price
        
        # Move to closed positions
        self.closed_positions.append(position)
        del self.positions[symbol]
        
        logger.debug(
            f"Closed position: {symbol} - "
            f"Return: {position.return_pct:.2f}% - "
            f"Reason: {reason}"
        )
    
    def _close_all_positions(self, date: datetime):
        """Close all open positions."""
        for symbol in list(self.positions.keys()):
            current_price = self._get_price(symbol, date)
            if current_price:
                self._close_position(symbol, current_price, date, "Backtest end")
    
    def _get_price(self, symbol: str, date: datetime) -> Optional[float]:
        """Get price for a symbol on a specific date."""
        asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()
        if not asset:
            return None
        
        # Get closest price to date
        price = self.db.query(Price).filter(
            Price.asset_id == asset.id,
            Price.date <= date
        ).order_by(Price.date.desc()).first()
        
        return price.close if price else None
    
    def _calculate_portfolio_value(self, date: datetime) -> float:
        """Calculate total portfolio value."""
        total = self.cash
        
        for symbol, position in self.positions.items():
            current_price = self._get_price(symbol, date)
            if current_price:
                total += position.shares * current_price
        
        return total
    
    def _calculate_performance_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Calculate comprehensive performance metrics."""
        
        # Basic returns
        final_value = self._calculate_portfolio_value(end_date)
        total_return = final_value - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100
        
        # Annualized return
        years = (end_date - start_date).days / 365.25
        annualized_return = ((final_value / self.initial_capital) ** (1/years) - 1) * 100
        
        # Create equity curve series
        if self.equity_curve:
            dates, values = zip(*self.equity_curve)
            equity_series = pd.Series(values, index=dates)
            
            # Calculate returns
            returns = equity_series.pct_change().dropna()
            
            # Max drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min() * 100
            
            # Sharpe ratio (assuming 2% risk-free rate)
            risk_free_rate = 0.02 / 252  # Daily risk-free rate
            excess_returns = returns - risk_free_rate
            sharpe_ratio = np.sqrt(252) * excess_returns.mean() / returns.std() if returns.std() > 0 else 0
        else:
            equity_series = pd.Series([self.initial_capital])
            max_drawdown = 0
            sharpe_ratio = 0
        
        # Trade statistics
        all_positions = self.closed_positions + list(self.positions.values())
        winning_trades = [p for p in self.closed_positions if p.profit_loss > 0]
        losing_trades = [p for p in self.closed_positions if p.profit_loss < 0]
        
        win_rate = len(winning_trades) / len(self.closed_positions) * 100 if self.closed_positions else 0
        avg_win = np.mean([p.return_pct for p in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([p.return_pct for p in losing_trades]) if losing_trades else 0
        
        return BacktestResult(
            initial_capital=self.initial_capital,
            final_value=final_value,
            total_return=total_return,
            total_return_pct=total_return_pct,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            total_trades=len(self.closed_positions),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            positions=all_positions,
            equity_curve=equity_series,
            metadata={
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'trading_days': len(self.equity_curve)
            }
        )
    
    def _calculate_benchmark_return(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[float]:
        """Calculate benchmark (S&P 500) return for comparison."""
        # In production, use actual S&P 500 data
        # For now, return a mock annual return
        years = (end_date - start_date).days / 365.25
        annual_return = 0.10  # Assume 10% annual S&P 500 return
        return annual_return
    
    def optimize_strategy(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        param_grid: Dict[str, List[Any]]
    ) -> Tuple[Dict[str, Any], BacktestResult]:
        """
        Optimize strategy parameters using grid search.
        
        Args:
            symbols: List of symbols to trade
            start_date: Backtest start date
            end_date: Backtest end date
            param_grid: Dictionary of parameters to optimize
            
        Returns:
            Best parameters and results
        """
        best_params = None
        best_result = None
        best_score = float('-inf')
        
        # Generate parameter combinations
        param_combinations = self._generate_param_combinations(param_grid)
        
        for params in param_combinations:
            try:
                # Run backtest with current parameters
                self.max_position_size = params.get('max_position_size', 0.10)
                self.max_positions = params.get('max_positions', 20)
                
                result = self.run_backtest(
                    symbols,
                    start_date,
                    end_date,
                    params.get('rebalance_frequency', 'monthly'),
                    params
                )
                
                # Score based on Sharpe ratio (risk-adjusted returns)
                score = result.sharpe_ratio
                
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_result = result
                    
            except Exception as e:
                logger.error(f"Failed to test parameters {params}: {e}")
                continue
        
        return best_params, best_result
    
    def _generate_param_combinations(self, param_grid: Dict[str, List[Any]]) -> List[Dict]:
        """Generate all parameter combinations from grid."""
        import itertools
        
        keys = param_grid.keys()
        values = param_grid.values()
        
        combinations = []
        for combo in itertools.product(*values):
            combinations.append(dict(zip(keys, combo)))
        
        return combinations