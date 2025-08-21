"""
Benchmark comparison schemas.
"""


from pydantic import BaseModel, ConfigDict, Field

from .index import SeriesPoint


class BenchmarkResponse(BaseModel):
    """Benchmark performance data response."""

    series: list[SeriesPoint] = Field(
        ..., description="Benchmark time series (base 100)"
    )
    benchmark_name: str = Field("S&P 500", description="Name of the benchmark")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "series": [
                    {"date": "2024-01-01", "value": 100.0},
                    {"date": "2024-01-02", "value": 101.2},
                ],
                "benchmark_name": "S&P 500",
            }
        }
    )
