"""
Pydantic schemas for API request/response validation.
Organized by domain for better modularity.
"""

from .auth import LoginRequest, RegisterRequest, TokenResponse
from .benchmark import BenchmarkResponse
from .index import (
    AllocationItem,
    IndexCurrentResponse,
    IndexHistoryResponse,
    SeriesPoint,
    SimulationRequest,
    SimulationResponse,
)
from .strategy import (
    RiskMetric,
    RiskMetricsResponse,
    StrategyConfigRequest,
    StrategyConfigResponse,
)

__all__ = [
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    # Index
    "AllocationItem",
    "IndexCurrentResponse",
    "SeriesPoint",
    "IndexHistoryResponse",
    "SimulationRequest",
    "SimulationResponse",
    # Benchmark
    "BenchmarkResponse",
    # Strategy
    "StrategyConfigRequest",
    "StrategyConfigResponse",
    "RiskMetric",
    "RiskMetricsResponse",
]
