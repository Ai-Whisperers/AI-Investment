"""
System status endpoints for monitoring database and infrastructure state.
Refactored to use repository pattern - no direct database access.
"""

import traceback
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..repositories.system_status_repository import SystemStatusRepository

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/database-status")
def check_database_status(db: Session = Depends(get_db)):
    """Check the current state of the database tables."""
    try:
        # Use repository instead of direct DB access
        repo = SystemStatusRepository(db)
        status = repo.get_database_status()
        
        # Add simulation readiness check
        index_count = status["tables"].get("index_values", {}).get("count", 0)
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
        # Use repository instead of direct DB access
        repo = SystemStatusRepository(db)
        results = repo.get_data_freshness_status()
        
        # Calculate overall status
        if results.get("status") == "healthy":
            data_types = results.get("data_freshness", {})
            
            # Add staleness analysis
            for data_type, info in data_types.items():
                if info.get("latest_date"):
                    try:
                        latest_date = datetime.fromisoformat(info["latest_date"]).date()
                        days_old = (datetime.now().date() - latest_date).days
                        info["days_old"] = days_old
                        info["status"] = "current" if days_old <= 1 else "stale"
                    except Exception:
                        info["status"] = "unknown"
            
            # Overall status
            all_current = all(
                dt.get("status") == "current"
                for dt in data_types.values()
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
        
        repo = SystemStatusRepository(db)
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "starting"
        }

        # Get counts before
        before_status = repo.get_database_status()
        before_index_count = before_status["tables"].get("index_values", {}).get("count", 0)
        before_allocation_count = before_status["tables"].get("allocations", {}).get("count", 0)

        # Recalculate
        compute_index_and_allocations(db)

        # Get counts after
        after_status = repo.get_database_status()
        after_index_count = after_status["tables"].get("index_values", {}).get("count", 0)
        after_allocation_count = after_status["tables"].get("allocations", {}).get("count", 0)

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
            "note": "Use /system/database-status for detailed sample values"
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
        # Use repository instead of direct DB access
        repo = SystemStatusRepository(db)
        
        # Get system health summary
        health_summary = repo.get_system_health_summary()
        
        # Get database status
        db_status = repo.get_database_status()
        
        # Get data freshness
        freshness = repo.get_data_freshness_status()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "operational",
            "health_score": health_summary.get("health_score", 0),
            "summary": health_summary.get("summary", {}),
            "simulation_ready": db_status["tables"].get("index_values", {}).get("count", 0) > 0,
            "data_freshness": freshness.get("status", "unknown"),
            "database_status": health_summary.get("status", "unknown"),
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


@router.get("/table/{table_name}")
def get_table_details(table_name: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific table."""
    try:
        repo = SystemStatusRepository(db)
        details = repo.get_table_details(table_name)
        
        if not details:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        return details

    except HTTPException:
        raise
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }