from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.asset import Asset, Price
from ..models.index import Allocation, IndexValue
from ..models.user import User
from ..schemas.index import (
    AllocationItem,
    IndexCurrentResponse,
    IndexHistoryResponse,
    SeriesPoint,
    SimulationRequest,
    SimulationResponse,
)
from ..services.currency import convert_amount, get_supported_currencies
from ..utils.cache_utils import CacheManager, cache_for_1hour, cache_for_5min
from ..utils.token_dep import get_current_user

router = APIRouter()


@router.get("/current", response_model=IndexCurrentResponse)
@cache_for_5min(CacheManager.CACHE_PREFIXES["index_current"])
def get_current_index(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    # Latest allocation date
    latest_date = db.query(func.max(Allocation.date)).scalar()
    if latest_date is None:
        raise HTTPException(
            status_code=404, detail="No allocations computed yet. Run tasks/refresh."
        )
    allocations = (
        db.query(Allocation, Asset)
        .join(Asset, Allocation.asset_id == Asset.id)
        .filter(Allocation.date == latest_date)
        .all()
    )
    items = []
    for alloc, asset in allocations:
        items.append(
            AllocationItem(
                symbol=asset.symbol,
                name=asset.name,
                sector=asset.sector,
                weight=alloc.weight,
            )
        )

    return IndexCurrentResponse(date=latest_date, allocations=items)


@router.get("/history", response_model=IndexHistoryResponse)
@cache_for_1hour(CacheManager.CACHE_PREFIXES["index_history"])
def get_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(IndexValue).order_by(IndexValue.date.asc()).all()
    if not rows:
        raise HTTPException(
            status_code=404, detail="No index history. Run tasks/refresh."
        )
    return IndexHistoryResponse(
        series=[SeriesPoint(date=r.date, value=r.value) for r in rows]
    )


@router.post("/simulate", response_model=SimulationResponse)
def simulate(
    req: SimulationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Get index series
    q = db.query(IndexValue).order_by(IndexValue.date.asc())
    series = q.all()
    if not series:
        raise HTTPException(
            status_code=404, detail="No index history. Run tasks/refresh."
        )

    # Find start and end
    start = next((r for r in series if r.date >= req.start_date), None)
    if start is None:
        raise HTTPException(status_code=400, detail="Start date out of range")
    end = series[-1]

    # Convert input amount to USD if necessary
    amount_usd = req.amount
    if req.currency != "USD":
        amount_usd = convert_amount(req.amount, req.currency, "USD")
        if amount_usd is None:
            raise HTTPException(
                status_code=400, detail=f"Cannot convert from {req.currency} to USD"
            )

    # Calculate in USD
    amount_final_usd = amount_usd * (end.value / start.value)

    # Convert back to requested currency if necessary
    amount_final = amount_final_usd
    if req.currency != "USD":
        amount_final = convert_amount(amount_final_usd, "USD", req.currency)
        if amount_final is None:
            # Fallback to USD if conversion fails
            amount_final = amount_final_usd
            req.currency = "USD"

    roi_pct = (amount_final / req.amount - 1.0) * 100.0

    resp_series = [
        SeriesPoint(date=r.date, value=r.value)
        for r in series
        if r.date >= req.start_date
    ]
    return SimulationResponse(
        start_date=start.date,
        end_date=end.date,
        start_value=start.value,
        end_value=end.value,
        amount_initial=req.amount,
        amount_final=amount_final,
        roi_pct=roi_pct,
        series=resp_series,
        currency=req.currency,
    )


@router.get("/currencies")
def get_currencies(user: User = Depends(get_current_user)):
    """Get list of supported currencies for simulation."""
    return get_supported_currencies()


@router.get("/assets/{symbol}/history", response_model=IndexHistoryResponse)
def get_asset_history(
    symbol: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Get price history for a specific asset, normalized to base 100."""
    asset = db.query(Asset).filter(Asset.symbol == symbol).first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

    rows = (
        db.query(Price)
        .filter(Price.asset_id == asset.id)
        .order_by(Price.date.asc())
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No price history for {symbol}")

    # Normalize to base 100 (same approach as AutoIndex and S&P 500)
    base = rows[0].close
    series = [SeriesPoint(date=r.date, value=(r.close / base) * 100.0) for r in rows]
    return IndexHistoryResponse(series=series)
