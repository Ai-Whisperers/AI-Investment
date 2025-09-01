"""
Repository for system status and database monitoring operations.
Abstracts database access for system health checks and status reporting.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.asset import Asset, Price
from ..models.index import Allocation, IndexValue
from ..models.strategy import RiskMetrics
from ..models.user import User

logger = logging.getLogger(__name__)


class SystemStatusRepository:
    """Repository for system status and monitoring queries."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_database_status(self) -> Dict[str, Any]:
        """Get comprehensive database status information."""
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
                    count = self.db.query(func.count()).select_from(model).scalar()

                    # Get date range for time-series tables
                    date_info = {}
                    if hasattr(model, "date"):
                        min_date = self.db.query(func.min(model.date)).scalar()
                        max_date = self.db.query(func.max(model.date)).scalar()
                        date_info = {
                            "oldest_record": min_date.isoformat() if min_date else None,
                            "newest_record": max_date.isoformat() if max_date else None
                        }

                    status["tables"][table_name] = {
                        "count": count,
                        "status": "healthy" if count > 0 else "empty",
                        **date_info
                    }

                except Exception as e:
                    status["tables"][table_name] = {
                        "count": 0,
                        "status": "error",
                        "error": str(e)
                    }

            return status

        except Exception as e:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "status": "failed"
            }
    
    def get_data_freshness_status(self) -> Dict[str, Any]:
        """Check data freshness across key tables."""
        try:
            status = {}
            
            # Price data freshness
            latest_price = self.db.query(Price).order_by(Price.date.desc()).first()
            status["prices"] = {
                "latest_date": latest_price.date.isoformat() if latest_price else None,
                "count": self.db.query(func.count()).select_from(Price).scalar()
            }
            
            # Index values freshness
            latest_index = self.db.query(IndexValue).order_by(IndexValue.date.desc()).first()
            status["index_values"] = {
                "latest_date": latest_index.date.isoformat() if latest_index else None,
                "count": self.db.query(func.count()).select_from(IndexValue).scalar()
            }
            
            # Allocations freshness
            latest_allocation = self.db.query(Allocation).order_by(Allocation.date.desc()).first()
            status["allocations"] = {
                "latest_date": latest_allocation.date.isoformat() if latest_allocation else None,
                "count": self.db.query(func.count()).select_from(Allocation).scalar()
            }
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "data_freshness": status,
                "status": "healthy"
            }
            
        except Exception as e:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "status": "failed"
            }
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        try:
            # Get basic counts
            user_count = self.db.query(func.count()).select_from(User).scalar()
            asset_count = self.db.query(func.count()).select_from(Asset).scalar()
            price_count = self.db.query(func.count()).select_from(Price).scalar()
            
            # Determine health status
            health_score = 0
            if user_count > 0:
                health_score += 20
            if asset_count > 0:
                health_score += 30
            if price_count > 0:
                health_score += 50
                
            if health_score >= 80:
                status = "healthy"
            elif health_score >= 50:
                status = "degraded"
            else:
                status = "unhealthy"
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "health_score": health_score,
                "status": status,
                "summary": {
                    "users": user_count,
                    "assets": asset_count,
                    "prices": price_count
                }
            }
            
        except Exception as e:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "status": "failed",
                "health_score": 0
            }
    
    def get_table_details(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific table."""
        table_map = {
            "users": User,
            "assets": Asset,
            "prices": Price,
            "index_values": IndexValue,
            "allocations": Allocation,
            "risk_metrics": RiskMetrics,
        }
        
        model = table_map.get(table_name)
        if not model:
            return None
            
        try:
            count = self.db.query(func.count()).select_from(model).scalar()
            
            details = {
                "table_name": table_name,
                "total_records": count,
                "status": "healthy" if count > 0 else "empty"
            }
            
            # Add date range for time-series tables
            if hasattr(model, "date"):
                min_date = self.db.query(func.min(model.date)).scalar()
                max_date = self.db.query(func.max(model.date)).scalar()
                
                details.update({
                    "date_range": {
                        "from": min_date.isoformat() if min_date else None,
                        "to": max_date.isoformat() if max_date else None
                    }
                })
            
            return details
            
        except Exception as e:
            return {
                "table_name": table_name,
                "error": str(e),
                "status": "error"
            }
    
    def get_basic_counts(self) -> Dict[str, int]:
        """Get basic counts for common operations."""
        try:
            return {
                "users": self.db.query(func.count()).select_from(User).scalar(),
                "assets": self.db.query(func.count()).select_from(Asset).scalar(),
                "prices": self.db.query(func.count()).select_from(Price).scalar(),
                "index_values": self.db.query(func.count()).select_from(IndexValue).scalar(),
                "allocations": self.db.query(func.count()).select_from(Allocation).scalar(),
                "risk_metrics": self.db.query(func.count()).select_from(RiskMetrics).scalar(),
            }
        except Exception as e:
            logger.error(f"Error getting basic counts: {e}")
            return {}
    
    def get_refresh_status_counts(self) -> Dict[str, int]:
        """Get counts specifically for refresh status reporting."""
        try:
            return {
                "index_values": self.db.query(func.count()).select_from(IndexValue).scalar(),
                "prices": self.db.query(func.count()).select_from(Price).scalar(),
            }
        except Exception as e:
            logger.error(f"Error getting refresh status counts: {e}")
            return {"index_values": 0, "prices": 0}