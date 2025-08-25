"""
Local Backtesting System
Uses locally stored market data for backtesting strategies
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from pathlib import Path

from .data_collector import data_collector
from .backtesting import BacktestEngine, BacktestResult, TradingStrategy

logger = logging.getLogger(__name__)


@dataclass
class LocalBacktestConfig:
    """Configuration for local backtesting."""
    symbols: List[str]
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    position_size: float = 0.1  # 10% per position
    max_positions: int = 10
    stop_loss: float = 0.05  # 5% stop loss
    take_profit: float = 0.15  # 15% take profit
    use_synthetic: bool = False
    
    
class LocalBacktester:
    """
    Backtesting system that uses locally stored data.
    Allows testing strategies without API keys.
    """
    
    def __init__(self, config: LocalBacktestConfig = None):
        """Initialize the local backtester."""
        self.config = config or LocalBacktestConfig(
            symbols=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
            start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
            end_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        self.engine = BacktestEngine()
        self.results = {}
        
    def load_local_data(self) -> Dict[str, pd.DataFrame]:
        """Load price data from local storage."""
        data = {}
        missing_symbols = []
        
        for symbol in self.config.symbols:
            df = data_collector.load_price_data(
                symbol,
                self.config.start_date,
                self.config.end_date
            )
            
            if df is not None and not df.empty:
                data[symbol] = df
                logger.info(f"Loaded {len(df)} days of data for {symbol}")
            else:
                missing_symbols.append(symbol)
        
        # Download missing data or generate synthetic
        if missing_symbols:
            logger.info(f"Downloading missing data for {missing_symbols}")
            
            if self.config.use_synthetic:
                new_data = data_collector._generate_synthetic_data(
                    missing_symbols,
                    self.config.start_date,
                    self.config.end_date
                )
            else:
                new_data = data_collector.download_yahoo_data(
                    missing_symbols,
                    self.config.start_date,
                    self.config.end_date
                )
            
            data.update(new_data)
        
        return data
    
    def backtest_strategy(
        self,
        strategy: TradingStrategy,
        data: Dict[str, pd.DataFrame] = None
    ) -> BacktestResult:
        """
        Backtest a trading strategy using local data.
        
        Args:
            strategy: Trading strategy to test
            data: Optional price data (loads from disk if not provided)
            
        Returns:
            Backtest results
        """
        # Load data if not provided
        if data is None:
            data = self.load_local_data()
        
        if not data:
            raise ValueError("No data available for backtesting")
        
        # Merge all symbol data into single DataFrame
        merged_data = self._merge_price_data(data)
        
        # Run backtest
        result = self.engine.run_backtest(
            merged_data,
            strategy,
            initial_capital=self.config.initial_capital
        )
        
        # Store result
        self.results[strategy.name] = result
        
        return result
    
    def _merge_price_data(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Merge multiple symbol DataFrames into one."""
        frames = []
        
        for symbol, df in data.items():
            # Add symbol column
            df_copy = df.copy()
            df_copy['symbol'] = symbol
            
            # Ensure we have required columns
            if 'Close' not in df_copy.columns:
                df_copy['Close'] = df_copy.get('close', df_copy.get('price', 0))
            if 'Volume' not in df_copy.columns:
                df_copy['Volume'] = df_copy.get('volume', 1000000)
            
            frames.append(df_copy)
        
        # Combine all frames
        if frames:
            merged = pd.concat(frames, ignore_index=False)
            merged.sort_index(inplace=True)
            return merged
        
        return pd.DataFrame()
    
    def test_multiple_strategies(
        self,
        strategies: List[TradingStrategy]
    ) -> Dict[str, BacktestResult]:
        """Test multiple strategies and compare results."""
        data = self.load_local_data()
        results = {}
        
        for strategy in strategies:
            logger.info(f"Testing strategy: {strategy.name}")
            try:
                result = self.backtest_strategy(strategy, data)
                results[strategy.name] = result
            except Exception as e:
                logger.error(f"Error testing {strategy.name}: {e}")
        
        return results
    
    def optimize_strategy(
        self,
        base_strategy: TradingStrategy,
        param_ranges: Dict[str, Tuple[float, float, float]]
    ) -> Dict:
        """
        Optimize strategy parameters using grid search.
        
        Args:
            base_strategy: Base strategy to optimize
            param_ranges: Parameter ranges (min, max, step)
            
        Returns:
            Optimization results
        """
        data = self.load_local_data()
        best_result = None
        best_params = {}
        all_results = []
        
        # Generate parameter combinations
        param_grid = self._generate_param_grid(param_ranges)
        
        logger.info(f"Testing {len(param_grid)} parameter combinations")
        
        for params in param_grid:
            # Create strategy with current parameters
            strategy = TradingStrategy(
                name=f"{base_strategy.name}_opt",
                **params
            )
            
            try:
                result = self.backtest_strategy(strategy, data)
                
                # Track results
                all_results.append({
                    "params": params,
                    "sharpe_ratio": result.sharpe_ratio,
                    "total_return": result.total_return,
                    "max_drawdown": result.max_drawdown
                })
                
                # Update best if better Sharpe ratio
                if best_result is None or result.sharpe_ratio > best_result.sharpe_ratio:
                    best_result = result
                    best_params = params
                    
            except Exception as e:
                logger.warning(f"Failed to test params {params}: {e}")
        
        return {
            "best_params": best_params,
            "best_result": best_result,
            "all_results": all_results
        }
    
    def _generate_param_grid(
        self,
        param_ranges: Dict[str, Tuple[float, float, float]]
    ) -> List[Dict]:
        """Generate parameter grid for optimization."""
        import itertools
        
        param_values = {}
        for param, (min_val, max_val, step) in param_ranges.items():
            values = []
            current = min_val
            while current <= max_val:
                values.append(current)
                current += step
            param_values[param] = values
        
        # Generate all combinations
        keys = list(param_values.keys())
        combinations = list(itertools.product(*[param_values[k] for k in keys]))
        
        # Convert to list of dictionaries
        param_grid = []
        for combo in combinations:
            param_grid.append(dict(zip(keys, combo)))
        
        return param_grid
    
    def analyze_performance(
        self,
        result: BacktestResult
    ) -> Dict:
        """
        Analyze backtest performance in detail.
        
        Args:
            result: Backtest result to analyze
            
        Returns:
            Detailed performance analysis
        """
        analysis = {
            "summary": {
                "total_return": f"{result.total_return:.2%}",
                "sharpe_ratio": f"{result.sharpe_ratio:.2f}",
                "max_drawdown": f"{result.max_drawdown:.2%}",
                "win_rate": f"{result.win_rate:.2%}",
                "total_trades": result.total_trades
            },
            "risk_metrics": {
                "volatility": result.volatility,
                "downside_deviation": self._calculate_downside_deviation(result),
                "sortino_ratio": self._calculate_sortino_ratio(result),
                "calmar_ratio": self._calculate_calmar_ratio(result)
            },
            "trade_analysis": {
                "avg_win": result.avg_win,
                "avg_loss": result.avg_loss,
                "profit_factor": result.profit_factor,
                "expectancy": self._calculate_expectancy(result)
            },
            "time_analysis": self._analyze_time_periods(result)
        }
        
        return analysis
    
    def _calculate_downside_deviation(self, result: BacktestResult) -> float:
        """Calculate downside deviation."""
        if result.equity_curve is None or len(result.equity_curve) < 2:
            return 0.0
        
        returns = pd.Series(result.equity_curve).pct_change().dropna()
        negative_returns = returns[returns < 0]
        
        if len(negative_returns) > 0:
            return float(negative_returns.std() * np.sqrt(252))
        return 0.0
    
    def _calculate_sortino_ratio(self, result: BacktestResult) -> float:
        """Calculate Sortino ratio."""
        downside_dev = self._calculate_downside_deviation(result)
        if downside_dev > 0:
            return result.total_return / downside_dev
        return 0.0
    
    def _calculate_calmar_ratio(self, result: BacktestResult) -> float:
        """Calculate Calmar ratio."""
        if result.max_drawdown > 0:
            return result.total_return / abs(result.max_drawdown)
        return 0.0
    
    def _calculate_expectancy(self, result: BacktestResult) -> float:
        """Calculate trade expectancy."""
        if result.total_trades == 0:
            return 0.0
        
        win_expectancy = result.win_rate * result.avg_win
        loss_expectancy = (1 - result.win_rate) * abs(result.avg_loss)
        
        return win_expectancy - loss_expectancy
    
    def _analyze_time_periods(self, result: BacktestResult) -> Dict:
        """Analyze performance across different time periods."""
        if result.equity_curve is None or len(result.equity_curve) < 30:
            return {}
        
        equity_series = pd.Series(result.equity_curve)
        
        # Calculate returns for different periods
        periods = {
            "daily": equity_series.pct_change().mean() * 100,
            "weekly": equity_series.pct_change(5).mean() * 100,
            "monthly": equity_series.pct_change(21).mean() * 100,
            "best_day": equity_series.pct_change().max() * 100,
            "worst_day": equity_series.pct_change().min() * 100
        }
        
        return periods
    
    def generate_report(
        self,
        output_file: str = None
    ) -> str:
        """Generate comprehensive backtest report."""
        if not self.results:
            return "No backtest results available"
        
        report = []
        report.append("=" * 60)
        report.append("LOCAL BACKTEST REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Data Source: Local ({data_collector.data_dir})")
        report.append("")
        
        # Configuration
        report.append("Configuration:")
        report.append(f"  Symbols: {', '.join(self.config.symbols)}")
        report.append(f"  Period: {self.config.start_date} to {self.config.end_date}")
        report.append(f"  Initial Capital: ${self.config.initial_capital:,.0f}")
        report.append("")
        
        # Results for each strategy
        for strategy_name, result in self.results.items():
            report.append("-" * 40)
            report.append(f"Strategy: {strategy_name}")
            report.append("-" * 40)
            
            # Performance summary
            analysis = self.analyze_performance(result)
            
            report.append("Performance Summary:")
            for key, value in analysis["summary"].items():
                report.append(f"  {key}: {value}")
            
            report.append("\nRisk Metrics:")
            for key, value in analysis["risk_metrics"].items():
                if isinstance(value, float):
                    report.append(f"  {key}: {value:.4f}")
                else:
                    report.append(f"  {key}: {value}")
            
            report.append("\nTrade Analysis:")
            for key, value in analysis["trade_analysis"].items():
                if isinstance(value, float):
                    report.append(f"  {key}: {value:.4f}")
                else:
                    report.append(f"  {key}: {value}")
            
            report.append("")
        
        # Best strategy
        if len(self.results) > 1:
            best_strategy = max(
                self.results.items(),
                key=lambda x: x[1].sharpe_ratio
            )
            report.append("=" * 40)
            report.append(f"Best Strategy: {best_strategy[0]}")
            report.append(f"Sharpe Ratio: {best_strategy[1].sharpe_ratio:.2f}")
            report.append("=" * 40)
        
        report_text = "\n".join(report)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            logger.info(f"Report saved to {output_file}")
        
        return report_text


# Create global instance
local_backtester = LocalBacktester()