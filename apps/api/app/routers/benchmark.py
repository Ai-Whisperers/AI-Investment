from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.asset import Asset, Price
from ..models.index import IndexValue
from ..models.user import User
from ..schemas.benchmark import BenchmarkResponse
from ..schemas.index import SeriesPoint
from ..utils.token_dep import get_current_user

router = APIRouter()


@router.get("/sp500", response_model=BenchmarkResponse)
def sp500(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # S&P 500 is stored as an asset with symbol '^GSPC' in prices table for history
    # Try multiple possible S&P 500 symbols (different data providers use different symbols)
    sp500_symbols = ["^GSPC", "SPY", "SPX", ".SPX", "^SPX"]

    sp500_asset = None
    for symbol in sp500_symbols:
        sp500_asset = db.query(Asset).filter(Asset.symbol == symbol).first()
        if sp500_asset:
            break

    if not sp500_asset:
        # Return empty series instead of raising error to prevent frontend crashes
        import logging

        logging.getLogger(__name__).warning(
            "S&P 500 benchmark asset not found. Returning empty series."
        )
        return BenchmarkResponse(series=[])

    rows = (
        db.query(Price)
        .filter(Price.asset_id == sp500_asset.id)
        .order_by(Price.date.asc())
        .all()
    )
    if not rows:
        # Return empty series instead of raising error
        import logging

        logging.getLogger(__name__).warning(
            f"No price data for S&P 500 ({sp500_asset.symbol}). Returning empty series."
        )
        return BenchmarkResponse(series=[])

    # Normalize to base 100
    base = rows[0].close
    series = [SeriesPoint(date=r.date, value=(r.close / base) * 100.0) for r in rows]
    return BenchmarkResponse(series=series)


@router.get("/compare")
def compare_performance(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Compare Autoindex performance against S&P 500 benchmark."""
    import numpy as np

    # Get index values
    query = db.query(IndexValue).order_by(IndexValue.date.asc())

    # Apply date filters if provided
    if start_date:
        query = query.filter(IndexValue.date >= start_date)
    if end_date:
        query = query.filter(IndexValue.date <= end_date)

    index_values = query.all()

    if not index_values:
        raise HTTPException(
            status_code=404, detail="No index data available for comparison"
        )

    # Get S&P 500 data for the same period
    sp500_symbols = ["^GSPC", "SPY", "SPX", ".SPX", "^SPX"]
    sp500_asset = None
    for symbol in sp500_symbols:
        sp500_asset = db.query(Asset).filter(Asset.symbol == symbol).first()
        if sp500_asset:
            break

    if not sp500_asset:
        raise HTTPException(status_code=404, detail="S&P 500 benchmark not available")

    # Get S&P 500 prices for the same date range
    sp500_query = (
        db.query(Price)
        .filter(
            Price.asset_id == sp500_asset.id,
            Price.date >= index_values[0].date,
            Price.date <= index_values[-1].date,
        )
        .order_by(Price.date.asc())
    )

    sp500_prices = sp500_query.all()

    if not sp500_prices:
        raise HTTPException(
            status_code=404, detail="No S&P 500 data for comparison period"
        )

    # Calculate performance metrics
    def calculate_metrics(values, name):
        if len(values) < 2:
            return None

        returns = np.diff(values) / values[:-1]

        # Calculate annualized metrics
        days = len(values)
        years = days / 252  # Trading days per year

        total_return = (values[-1] / values[0] - 1) * 100
        annualized_return = (
            ((values[-1] / values[0]) ** (1 / years) - 1) * 100 if years > 0 else 0
        )

        # Volatility (annualized)
        volatility = np.std(returns) * np.sqrt(252) * 100 if len(returns) > 0 else 0

        # Sharpe ratio (assuming 2% risk-free rate)
        risk_free = 0.02
        sharpe = (
            (annualized_return / 100 - risk_free) / (volatility / 100)
            if volatility > 0
            else 0
        )

        return {
            "start_value": float(values[0]),
            "end_value": float(values[-1]),
            "total_return": float(total_return),
            "annualized_return": float(annualized_return),
            "volatility": float(volatility),
            "sharpe_ratio": float(sharpe),
        }

    # Extract values
    autoindex_values = np.array([v.value for v in index_values])
    sp500_values = np.array([p.close for p in sp500_prices])

    # Normalize both to start at 100
    if len(autoindex_values) > 0:
        autoindex_values = (autoindex_values / autoindex_values[0]) * 100
    if len(sp500_values) > 0:
        sp500_values = (sp500_values / sp500_values[0]) * 100

    autoindex_metrics = calculate_metrics(autoindex_values, "autoindex")
    sp500_metrics = calculate_metrics(sp500_values, "sp500")

    if not autoindex_metrics or not sp500_metrics:
        raise HTTPException(status_code=400, detail="Insufficient data for comparison")

    # Calculate outperformance
    outperformance = {
        "total": autoindex_metrics["total_return"] - sp500_metrics["total_return"],
        "annualized": autoindex_metrics["annualized_return"]
        - sp500_metrics["annualized_return"],
        "information_ratio": (
            (
                (
                    autoindex_metrics["annualized_return"]
                    - sp500_metrics["annualized_return"]
                )
                / max(
                    autoindex_metrics["volatility"] - sp500_metrics["volatility"], 0.01
                )
            )
            if autoindex_metrics["volatility"] > sp500_metrics["volatility"]
            else 0
        ),
    }

    return {
        "autoindex": autoindex_metrics,
        "sp500": sp500_metrics,
        "outperformance": outperformance,
    }
