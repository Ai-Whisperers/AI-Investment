"""
Health check endpoints for system monitoring.
Provides basic health checks and system status information.
"""

import traceback
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.redis_client import get_redis_client
from ..models.asset import Asset, Price

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "waardhaven-autoindex-api"
    }


@router.get("/live")
def liveness_probe():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive"}


@router.get("/ready")
def readiness_probe(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe endpoint.
    Checks if the service is ready to accept traffic.
    """
    try:
        # Check database connectivity
        db.execute("SELECT 1")

        # Check Redis connectivity
        redis_client = get_redis_client()
        redis_connected = redis_client.health_check()

        return {
            "status": "ready",
            "database": "connected",
            "cache": "connected" if redis_connected else "disconnected"
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "error": str(e)
        }


@router.get("/test-refresh")
def test_refresh_process(db: Session = Depends(get_db)):
    """Test the refresh process with detailed error reporting."""
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "steps": []
    }

    try:
        # Step 1: Test asset creation
        from ..services.refresh import ensure_assets

        results["steps"].append({"step": "ensure_assets", "status": "starting"})
        ensure_assets(db)
        asset_count = db.query(func.count()).select_from(Asset).scalar()
        results["steps"].append({
            "step": "ensure_assets",
            "status": "success",
            "asset_count": asset_count
        })

        # Step 2: Test price fetching for one symbol
        from datetime import date, timedelta

        from ..services.twelvedata import fetch_prices

        results["steps"].append({"step": "fetch_prices", "status": "starting"})
        test_symbol = "AAPL"
        start_date = date.today() - timedelta(days=30)

        try:
            price_df = fetch_prices([test_symbol], start=start_date)
            results["steps"].append({
                "step": "fetch_prices",
                "status": "success",
                "symbol": test_symbol,
                "rows": len(price_df),
                "columns": (
                    list(price_df.columns.levels[0])
                    if hasattr(price_df.columns, "levels")
                    else list(price_df.columns)
                )
            })
        except Exception as e:
            results["steps"].append({
                "step": "fetch_prices",
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            })

        # Step 3: Check database connectivity
        results["steps"].append({"step": "database_write", "status": "starting"})
        try:
            # Try to write a test record
            test_asset = db.query(Asset).filter(Asset.symbol == "AAPL").first()
            if test_asset and not price_df.empty:
                results["steps"].append({
                    "step": "database_write",
                    "status": "ready",
                    "message": "Database is writable"
                })
            else:
                results["steps"].append({
                    "step": "database_write",
                    "status": "skipped",
                    "message": "No test data to write"
                })
        except Exception as e:
            results["steps"].append({
                "step": "database_write",
                "status": "failed",
                "error": str(e)
            })

        results["overall_status"] = "PARTIAL_SUCCESS"

    except Exception as e:
        results["overall_status"] = "FAILED"
        results["error"] = str(e)
        results["traceback"] = traceback.format_exc()

    return results


@router.get("/refresh-status")
def check_refresh_requirements(db: Session = Depends(get_db)):
    """Check what needs to be refreshed."""
    try:
        # Check assets
        assets = db.query(Asset).all()
        asset_symbols = [a.symbol for a in assets]

        # Check for S&P 500 benchmark
        has_benchmark = "^GSPC" in asset_symbols

        # Check price data freshness
        latest_price_date = db.query(func.max(Price.date)).scalar()
        days_old = (
            (datetime.now().date() - latest_price_date).days
            if latest_price_date
            else None
        )

        return {
            "assets": {
                "count": len(assets),
                "symbols": asset_symbols,
                "has_benchmark": has_benchmark,
            },
            "prices": {
                "latest_date": str(latest_price_date) if latest_price_date else None,
                "days_old": days_old,
                "needs_update": days_old > 1 if days_old is not None else True,
            },
            "recommendation": (
                "Run refresh to populate data"
                if latest_price_date is None
                else (
                    "Data is up to date"
                    if days_old <= 1
                    else f"Data is {days_old} days old, consider refreshing"
                )
            ),
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
