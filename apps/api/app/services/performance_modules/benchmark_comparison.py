"""
Benchmark comparison metrics for portfolio performance analysis.
Includes beta, alpha, information ratio, and correlation calculations.
"""

import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Annual trading days
TRADING_DAYS_PER_YEAR = 252
# Default risk-free rate (annual)
DEFAULT_RISK_FREE_RATE = 0.05


class BenchmarkComparison:
    """Calculate benchmark-relative performance metrics."""

    @staticmethod
    def align_returns(
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Align portfolio and benchmark returns to same length.
        
        Args:
            portfolio_returns: Portfolio return series
            benchmark_returns: Benchmark return series
            
        Returns:
            Tuple of aligned (portfolio_returns, benchmark_returns)
        """
        if len(portfolio_returns) == 0 or len(benchmark_returns) == 0:
            return np.array([]), np.array([])
        
        min_len = min(len(portfolio_returns), len(benchmark_returns))
        return portfolio_returns[:min_len], benchmark_returns[:min_len]

    @staticmethod
    def beta(
        portfolio_returns: np.ndarray,
        market_returns: np.ndarray
    ) -> float:
        """
        Calculate beta (portfolio volatility relative to market).

        Args:
            portfolio_returns: Portfolio daily returns
            market_returns: Market daily returns

        Returns:
            Beta coefficient
        """
        if len(portfolio_returns) < 2 or len(market_returns) < 2:
            return 1.0

        # Align returns
        portfolio_aligned, market_aligned = BenchmarkComparison.align_returns(
            portfolio_returns, market_returns
        )
        
        if len(portfolio_aligned) < 2:
            return 1.0

        # Calculate covariance and market variance
        try:
            covariance = np.cov(portfolio_aligned, market_aligned)[0, 1]
            market_variance = np.var(market_aligned)

            if market_variance == 0:
                return 1.0

            beta = covariance / market_variance
            return float(beta)
        except Exception as e:
            logger.warning(f"Error calculating beta: {e}")
            return 1.0

    @staticmethod
    def alpha(
        portfolio_returns: np.ndarray,
        market_returns: np.ndarray,
        beta: Optional[float] = None,
        risk_free_rate: float = DEFAULT_RISK_FREE_RATE
    ) -> float:
        """
        Calculate Jensen's alpha.

        Args:
            portfolio_returns: Portfolio daily returns
            market_returns: Market daily returns
            beta: Portfolio beta (calculated if not provided)
            risk_free_rate: Annual risk-free rate

        Returns:
            Annualized alpha
        """
        if len(portfolio_returns) == 0 or len(market_returns) == 0:
            return 0.0

        # Align returns
        portfolio_aligned, market_aligned = BenchmarkComparison.align_returns(
            portfolio_returns, market_returns
        )
        
        if len(portfolio_aligned) == 0:
            return 0.0

        # Calculate beta if not provided
        if beta is None:
            beta = BenchmarkComparison.beta(portfolio_aligned, market_aligned)

        # Annualized returns
        portfolio_annual = (1 + portfolio_aligned.mean()) ** TRADING_DAYS_PER_YEAR - 1
        market_annual = (1 + market_aligned.mean()) ** TRADING_DAYS_PER_YEAR - 1

        # Calculate alpha using CAPM
        alpha = portfolio_annual - (
            risk_free_rate + beta * (market_annual - risk_free_rate)
        )
        return float(alpha)

    @staticmethod
    def information_ratio(
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> float:
        """
        Calculate Information Ratio (active return / tracking error).

        Args:
            portfolio_returns: Portfolio daily returns
            benchmark_returns: Benchmark daily returns

        Returns:
            Information ratio
        """
        if len(portfolio_returns) == 0 or len(benchmark_returns) == 0:
            return 0.0

        # Align returns
        portfolio_aligned, benchmark_aligned = BenchmarkComparison.align_returns(
            portfolio_returns, benchmark_returns
        )
        
        if len(portfolio_aligned) == 0:
            return 0.0

        # Calculate active returns
        active_returns = portfolio_aligned - benchmark_aligned

        if active_returns.std() == 0:
            return 0.0

        # Annualized information ratio
        ir = (active_returns.mean() / active_returns.std()) * np.sqrt(
            TRADING_DAYS_PER_YEAR
        )
        return float(ir)

    @staticmethod
    def correlation(
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> float:
        """
        Calculate correlation between portfolio and benchmark.

        Args:
            portfolio_returns: Portfolio daily returns
            benchmark_returns: Benchmark daily returns

        Returns:
            Correlation coefficient
        """
        if len(portfolio_returns) < 2 or len(benchmark_returns) < 2:
            return 0.0

        # Align returns
        portfolio_aligned, benchmark_aligned = BenchmarkComparison.align_returns(
            portfolio_returns, benchmark_returns
        )
        
        if len(portfolio_aligned) < 2:
            return 0.0

        try:
            correlation_matrix = np.corrcoef(portfolio_aligned, benchmark_aligned)
            correlation = float(correlation_matrix[0, 1])
            
            if np.isnan(correlation):
                return 0.0
            
            return correlation
        except Exception as e:
            logger.warning(f"Error calculating correlation: {e}")
            return 0.0

    @staticmethod
    def tracking_error(
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> float:
        """
        Calculate tracking error (standard deviation of active returns).

        Args:
            portfolio_returns: Portfolio daily returns
            benchmark_returns: Benchmark daily returns

        Returns:
            Annualized tracking error
        """
        if len(portfolio_returns) == 0 or len(benchmark_returns) == 0:
            return 0.0

        # Align returns
        portfolio_aligned, benchmark_aligned = BenchmarkComparison.align_returns(
            portfolio_returns, benchmark_returns
        )
        
        if len(portfolio_aligned) == 0:
            return 0.0

        # Calculate active returns
        active_returns = portfolio_aligned - benchmark_aligned

        # Annualized tracking error
        te = active_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        return float(te)

    @staticmethod
    def treynor_ratio(
        portfolio_returns: np.ndarray,
        market_returns: np.ndarray,
        beta: Optional[float] = None,
        risk_free_rate: float = DEFAULT_RISK_FREE_RATE
    ) -> float:
        """
        Calculate Treynor ratio (excess return per unit of systematic risk).

        Args:
            portfolio_returns: Portfolio daily returns
            market_returns: Market daily returns
            beta: Portfolio beta (calculated if not provided)
            risk_free_rate: Annual risk-free rate

        Returns:
            Treynor ratio
        """
        if len(portfolio_returns) == 0:
            return 0.0

        # Calculate beta if not provided
        if beta is None:
            beta = BenchmarkComparison.beta(portfolio_returns, market_returns)

        if beta == 0:
            return 0.0

        # Annualized portfolio return
        portfolio_annual = (1 + portfolio_returns.mean()) ** TRADING_DAYS_PER_YEAR - 1

        # Treynor ratio
        treynor = (portfolio_annual - risk_free_rate) / beta
        return float(treynor)

    @staticmethod
    def capture_ratio(
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray,
        upside: bool = True
    ) -> float:
        """
        Calculate upside or downside capture ratio.

        Args:
            portfolio_returns: Portfolio daily returns
            benchmark_returns: Benchmark daily returns
            upside: If True, calculate upside capture; if False, downside capture

        Returns:
            Capture ratio
        """
        if len(portfolio_returns) == 0 or len(benchmark_returns) == 0:
            return 0.0

        # Align returns
        portfolio_aligned, benchmark_aligned = BenchmarkComparison.align_returns(
            portfolio_returns, benchmark_returns
        )
        
        if len(portfolio_aligned) == 0:
            return 0.0

        # Filter for up or down markets
        if upside:
            mask = benchmark_aligned > 0
        else:
            mask = benchmark_aligned < 0

        if not mask.any():
            return 0.0

        # Calculate capture ratio
        portfolio_filtered = portfolio_aligned[mask]
        benchmark_filtered = benchmark_aligned[mask]

        if len(benchmark_filtered) == 0 or benchmark_filtered.sum() == 0:
            return 0.0

        capture = portfolio_filtered.sum() / benchmark_filtered.sum()
        return float(capture * 100)