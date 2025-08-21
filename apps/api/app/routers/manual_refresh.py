import logging
import traceback
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.asset import Price
from ..models.index import IndexValue

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/trigger-refresh")
def trigger_manual_refresh(
    background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """
    Trigger a manual refresh without requiring admin token (for debugging).
    This endpoint should be removed or secured in production.
    """
    try:
        # Check current state
        index_count = db.query(func.count()).select_from(IndexValue).scalar()
        price_count = db.query(func.count()).select_from(Price).scalar()

        # Add refresh to background tasks
        background_tasks.add_task(run_refresh_with_logging, db)

        return {
            "status": "REFRESH_STARTED",
            "message": "Refresh has been triggered in the background",
            "current_state": {"index_values": index_count, "prices": price_count},
            "note": "Check /api/v1/diagnostics/database-status in 30-60 seconds to see results",
        }
    except Exception as e:
        logger.error(f"Failed to trigger refresh: {str(e)}")
        return {"status": "ERROR", "error": str(e), "traceback": traceback.format_exc()}


@router.post("/smart-refresh")
def trigger_smart_refresh(
    background_tasks: BackgroundTasks, mode: str = "auto", db: Session = Depends(get_db)
):
    """
    Trigger smart refresh with rate limiting protection.

    Modes: auto, full, minimal, cached
    """
    valid_modes = ["auto", "full", "minimal", "cached"]
    if mode not in valid_modes:
        return {
            "status": "ERROR",
            "error": f"Invalid mode. Must be one of: {valid_modes}",
        }

    try:
        # Add smart refresh to background tasks
        background_tasks.add_task(run_smart_refresh_with_logging, db, mode)

        return {
            "status": "SMART_REFRESH_STARTED",
            "message": f"Smart refresh has been triggered in {mode} mode",
            "mode": mode,
            "features": [
                "Rate limit protection",
                "Caching support",
                "Fallback to cached data",
                "API tier optimization",
            ],
            "note": "This refresh is optimized for your API plan and will avoid rate limits",
        }
    except Exception as e:
        logger.error(f"Failed to trigger smart refresh: {str(e)}")
        return {"status": "ERROR", "error": str(e), "traceback": traceback.format_exc()}


def run_refresh_with_logging(db: Session):
    """Run refresh with detailed logging."""
    try:
        logger.info("Starting manual refresh process...")
        from ..services.refresh import refresh_all

        refresh_all(db)

        # Verify results
        index_count = db.query(func.count()).select_from(IndexValue).scalar()
        price_count = db.query(func.count()).select_from(Price).scalar()

        logger.info(
            f"Refresh completed. Index values: {index_count}, Prices: {price_count}"
        )

    except Exception as e:
        logger.error(f"Refresh failed: {str(e)}")
        logger.error(traceback.format_exc())


def run_smart_refresh_with_logging(db: Session, mode: str = "auto"):
    """Run smart refresh with detailed logging."""
    try:
        logger.info(f"Starting smart refresh in {mode} mode...")

        try:
            from ..services.refresh_optimized import smart_refresh

            result = smart_refresh(db, mode=mode)
            logger.info(f"Smart refresh completed: {result}")
        except ImportError:
            logger.warning("Smart refresh not available, falling back to standard")
            from ..services.refresh import refresh_all

            refresh_all(db)
            result = {"success": True, "mode": "fallback"}

        # Verify results
        index_count = db.query(func.count()).select_from(IndexValue).scalar()
        price_count = db.query(func.count()).select_from(Price).scalar()

        logger.info(
            f"Smart refresh result - Index values: {index_count}, Prices: {price_count}"
        )

    except Exception as e:
        logger.error(f"Smart refresh failed: {str(e)}")
        logger.error(traceback.format_exc())


@router.post("/minimal-refresh")
def minimal_data_refresh(db: Session = Depends(get_db)):
    """
    Perform a minimal refresh with just a few days of data for testing.
    """
    try:
        from datetime import date, timedelta

        from ..models.asset import Asset, Price
        from ..models.index import IndexValue
        from ..services.refresh import ensure_assets
        from ..services.twelvedata import fetch_prices

        results = {"timestamp": datetime.utcnow().isoformat(), "steps": []}

        # Step 1: Ensure assets exist
        ensure_assets(db)
        assets = (
            db.query(Asset).filter(Asset.symbol.in_(["AAPL", "MSFT", "GOOGL"])).all()
        )
        results["steps"].append(
            {
                "step": "assets",
                "count": len(assets),
                "symbols": [a.symbol for a in assets],
            }
        )

        # Step 2: Fetch minimal price data (last 7 days)
        symbols = [a.symbol for a in assets]
        start_date = date.today() - timedelta(days=7)

        try:
            price_df = fetch_prices(symbols, start=start_date)

            # Clear existing recent prices
            db.query(Price).filter(Price.date >= start_date).delete()
            db.commit()

            # Store new prices
            stored_count = 0
            for sym in symbols:
                asset = next((a for a in assets if a.symbol == sym), None)
                if asset:
                    # Handle both MultiIndex and regular columns
                    if hasattr(price_df.columns, 'levels'):
                        # MultiIndex columns (symbol, metric)
                        if sym in price_df.columns.levels[0]:
                            series = price_df[sym]["close"].dropna()
                            for idx, val in series.items():
                                db.add(
                                    Price(asset_id=asset.id, date=idx.date(), close=float(val))
                                )
                                stored_count += 1
                    else:
                        # Regular columns or single symbol
                        if "close" in price_df.columns:
                            series = price_df["close"].dropna()
                            for idx, val in series.items():
                                db.add(
                                    Price(asset_id=asset.id, date=idx.date(), close=float(val))
                                )
                                stored_count += 1

            db.commit()
            results["steps"].append(
                {"step": "prices", "fetched": len(price_df), "stored": stored_count}
            )

            # Step 3: Create simple index values
            # For testing, just create a simple average
            dates = price_df.index.unique()
            for dt in dates:
                # Simple average of prices as index value
                avg_price = 100.0  # Base value
                try:
                    prices_on_date = []
                    for sym in symbols:
                        if hasattr(price_df.columns, 'levels'):
                            # MultiIndex columns
                            if sym in price_df.columns.levels[0]:
                                if dt in price_df[sym]["close"].index:
                                    prices_on_date.append(price_df[sym]["close"][dt])
                        else:
                            # Regular columns
                            if "close" in price_df.columns:
                                if dt in price_df.index:
                                    prices_on_date.append(price_df.loc[dt, "close"])

                    if prices_on_date:
                        avg_price = sum(prices_on_date) / len(prices_on_date)

                    # Check if index value exists
                    existing = (
                        db.query(IndexValue)
                        .filter(IndexValue.date == dt.date())
                        .first()
                    )
                    if not existing:
                        db.add(IndexValue(date=dt.date(), value=avg_price))
                except Exception as e:
                    logger.debug(f"Skipping date {dt}: {e}")

            db.commit()

            index_count = db.query(func.count()).select_from(IndexValue).scalar()
            results["steps"].append({"step": "index_values", "created": index_count})

            results["status"] = "SUCCESS"
            results["message"] = "Minimal data refresh completed"

        except Exception as e:
            results["status"] = "FAILED"
            results["error"] = str(e)
            results["traceback"] = traceback.format_exc()

        return results

    except Exception as e:
        return {"status": "ERROR", "error": str(e), "traceback": traceback.format_exc()}
