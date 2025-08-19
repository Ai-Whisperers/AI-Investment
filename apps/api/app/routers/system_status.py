"""
System status endpoints for monitoring database and infrastructure state.
Provides detailed information about database tables, data freshness, and system components.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import traceback

from ..core.database import get_db
from ..models.asset import Asset, Price
from ..models.index import IndexValue, Allocation
from ..models.user import User
from ..models.strategy import RiskMetrics

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/database-status")
def check_database_status(db: Session = Depends(get_db)):
    """Check the current state of the database tables."""
    try:
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "tables": {}
        }

        # Check each table
        tables = [
            ("users", User),
            ("assets", Asset),
            ("prices", Price),
            ("index_values", IndexValue),
            ("allocations", Allocation),
            ("risk_metrics", RiskMetrics),
        ]

        for table_name, model in tables:
            try:
                count = db.query(func.count()).select_from(model).scalar()

                # Get date range for time-series tables
                date_info = {}
                if hasattr(model, "date"):
                    min_date = db.query(func.min(model.date)).scalar()
                    max_date = db.query(func.max(model.date)).scalar()
                    date_info = {
                        "earliest_date": str(min_date) if min_date else None,
                        "latest_date": str(max_date) if max_date else None,
                    }

                status["tables"][table_name] = {
                    "count": count,
                    "status": "OK" if count > 0 else "EMPTY",
                    **date_info,
                }
            except Exception as e:
                status["tables"][table_name] = {
                    "count": 0,
                    "status": "ERROR",
                    "error": str(e),
                }

        # Check if we have enough data for simulation
        index_count = status["tables"]["index_values"]["count"]
        status["simulation_ready"] = index_count > 0
        status["message"] = (
            "Database is ready for simulation"
            if index_count > 0
            else "No index data available - refresh needed"
        )

        return status

    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "ERROR",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


@router.get("/data-freshness")
def check_data_freshness(db: Session = Depends(get_db)):
    """Check the freshness of various data types."""
    try:
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "data_types": {}
        }

        # Check price data
        latest_price = db.query(func.max(Price.date)).scalar()
        if latest_price:
            days_old = (datetime.now().date() - latest_price).days
            results["data_types"]["prices"] = {
                "latest_date": str(latest_price),
                "days_old": days_old,
                "status": "current" if days_old <= 1 else "stale"
            }

        # Check index values
        latest_index = db.query(func.max(IndexValue.date)).scalar()
        if latest_index:
            days_old = (datetime.now().date() - latest_index).days
            results["data_types"]["index_values"] = {
                "latest_date": str(latest_index),
                "days_old": days_old,
                "status": "current" if days_old <= 1 else "stale"
            }

        # Check allocations
        latest_allocation = db.query(func.max(Allocation.date)).scalar()
        if latest_allocation:
            days_old = (datetime.now().date() - latest_allocation).days
            results["data_types"]["allocations"] = {
                "latest_date": str(latest_allocation),
                "days_old": days_old,
                "status": "current" if days_old <= 1 else "stale"
            }

        # Check risk metrics
        latest_risk = db.query(func.max(RiskMetrics.date)).scalar()
        if latest_risk:
            days_old = (datetime.now().date() - latest_risk).days
            results["data_types"]["risk_metrics"] = {
                "latest_date": str(latest_risk),
                "days_old": days_old,
                "status": "current" if days_old <= 1 else "stale"
            }

        # Overall status
        all_current = all(
            dt.get("status") == "current"
            for dt in results["data_types"].values()
        )
        results["overall_status"] = "current" if all_current else "update_needed"

        return results

    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.post("/recalculate-index")
def recalculate_autoindex(db: Session = Depends(get_db)):
    """Recalculate the AutoIndex with proper normalization."""
    try:
        from ..services.strategy import compute_index_and_allocations

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "starting"
        }

        # Get counts before
        before_index_count = db.query(func.count()).select_from(IndexValue).scalar()
        before_allocation_count = db.query(func.count()).select_from(Allocation).scalar()

        # Recalculate
        compute_index_and_allocations(db)

        # Get counts after
        after_index_count = db.query(func.count()).select_from(IndexValue).scalar()
        after_allocation_count = db.query(func.count()).select_from(Allocation).scalar()

        # Get sample values
        sample_values = (
            db.query(IndexValue)
            .order_by(IndexValue.date.desc())
            .limit(5)
            .all()
        )

        result.update({
            "status": "success",
            "before": {
                "index_values": before_index_count,
                "allocations": before_allocation_count,
            },
            "after": {
                "index_values": after_index_count,
                "allocations": after_allocation_count,
            },
            "sample_recent_values": [
                {"date": str(iv.date), "value": iv.value}
                for iv in sample_values
            ],
        })

        return result

    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


@router.get("/summary")
def get_system_summary(db: Session = Depends(get_db)):
    """Get comprehensive system summary."""
    try:
        # Get database status
        db_status = check_database_status(db)
        
        # Get data freshness
        freshness = check_data_freshness(db)
        
        # Get basic counts
        user_count = db.query(func.count()).select_from(User).scalar()
        asset_count = db.query(func.count()).select_from(Asset).scalar()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "operational",
            "summary": {
                "users": user_count,
                "assets": asset_count,
                "simulation_ready": db_status.get("simulation_ready", False),
                "data_freshness": freshness.get("overall_status", "unknown"),
                "database_status": "healthy" if db_status.get("status") != "ERROR" else "error"
            },
            "details": {
                "database": db_status,
                "freshness": freshness
            }
        }
        
    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }