"""
Report generation background tasks.
Handles creating various reports and analytics asynchronously.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any

from ..core.celery_app import celery_app
from ..models.index import Allocation, IndexValue
from ..models.strategy import RiskMetrics
from ..services.performance import calculate_portfolio_metrics
from .base import DatabaseTask, create_error_response, create_success_response

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=DatabaseTask, name="generate_report")
def generate_report(
    self,
    report_type: str = "performance",
    period_days: int = 30,
    db=None
) -> dict[str, Any]:
    """
    Generate various reports in the background.

    Args:
        report_type: Type of report (performance, allocation, risk)
        period_days: Period to analyze
        db: Database session (injected by DatabaseTask)

    Returns:
        Report data
    """
    try:
        start_time = datetime.utcnow()
        logger.info(f"Generating {report_type} report for {period_days} days")

        self.update_state(
            state="PROGRESS",
            meta={"status": f"Generating {report_type} report..."}
        )

        # Generate report based on type
        if report_type == "performance":
            report_data = _generate_performance_report(db, period_days)
        elif report_type == "allocation":
            report_data = _generate_allocation_report(db)
        elif report_type == "risk":
            report_data = _generate_risk_report(db)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        result = create_success_response(
            duration=duration,
            start_time=start_time,
            end_time=end_time,
            report=report_data
        )

        logger.info(f"Report generation completed in {duration:.2f} seconds")
        return result

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return create_error_response(e)


def _generate_performance_report(db, period_days: int) -> dict[str, Any]:
    """Generate performance report."""
    end_date = date.today()
    start_date = end_date - timedelta(days=period_days)

    report_data = {
        "type": "performance",
        "period_days": period_days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }

    # Get performance metrics
    metrics = calculate_portfolio_metrics(db)

    # Get index values for period
    index_values = (
        db.query(IndexValue)
        .filter(IndexValue.date >= start_date, IndexValue.date <= end_date)
        .order_by(IndexValue.date)
        .all()
    )

    if index_values:
        start_value = index_values[0].value
        end_value = index_values[-1].value
        period_return = ((end_value / start_value) - 1) * 100

        report_data.update({
            "period_return": period_return,
            "start_value": start_value,
            "end_value": end_value,
            "data_points": len(index_values),
            "metrics": metrics,
        })

    return report_data


def _generate_allocation_report(db) -> dict[str, Any]:
    """Generate allocation report."""
    report_data = {
        "type": "allocation"
    }

    # Get latest allocations
    latest_date = (
        db.query(Allocation.date)
        .order_by(Allocation.date.desc())
        .first()
    )

    if latest_date:
        allocations = (
            db.query(Allocation)
            .filter(Allocation.date == latest_date[0])
            .all()
        )

        # Get asset details
        from ..models.asset import Asset

        allocation_details = []
        for alloc in allocations:
            asset = db.query(Asset).filter(Asset.id == alloc.asset_id).first()
            if asset:
                allocation_details.append({
                    "asset_id": alloc.asset_id,
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "weight": alloc.weight,
                    "asset_type": asset.asset_type
                })

        report_data.update({
            "date": latest_date[0].isoformat(),
            "allocations": allocation_details,
            "total_assets": len(allocation_details)
        })

    return report_data


def _generate_risk_report(db) -> dict[str, Any]:
    """Generate risk report."""
    report_data = {
        "type": "risk"
    }

    # Get latest risk metrics
    latest_risk = (
        db.query(RiskMetrics)
        .order_by(RiskMetrics.date.desc())
        .first()
    )

    if latest_risk:
        report_data.update({
            "date": latest_risk.date.isoformat(),
            "risk_metrics": {
                "sharpe_ratio": latest_risk.sharpe_ratio,
                "sortino_ratio": latest_risk.sortino_ratio,
                "max_drawdown": latest_risk.max_drawdown,
                "current_drawdown": latest_risk.current_drawdown,
                "volatility": latest_risk.volatility,
                "beta_sp500": latest_risk.beta_sp500,
                "correlation_sp500": latest_risk.correlation_sp500,
                "total_return": latest_risk.total_return,
                "annualized_return": latest_risk.annualized_return
            }
        })

        # Add risk assessment
        risk_level = "Low"
        if latest_risk.volatility > 0.25:
            risk_level = "High"
        elif latest_risk.volatility > 0.15:
            risk_level = "Medium"

        report_data["risk_assessment"] = {
            "level": risk_level,
            "volatility_percentile": latest_risk.volatility * 100,
            "max_loss_observed": latest_risk.max_drawdown * 100
        }

    return report_data


@celery_app.task(bind=True, base=DatabaseTask, name="generate_comprehensive_report")
def generate_comprehensive_report(
    self,
    period_days: int = 30,
    db=None
) -> dict[str, Any]:
    """
    Generate a comprehensive report combining all report types.

    Args:
        period_days: Period to analyze
        db: Database session (injected by DatabaseTask)

    Returns:
        Comprehensive report data
    """
    try:
        start_time = datetime.utcnow()
        logger.info(f"Generating comprehensive report for {period_days} days")

        self.update_state(
            state="PROGRESS",
            meta={"status": "Generating comprehensive report..."}
        )

        # Generate all report types
        performance = _generate_performance_report(db, period_days)
        allocation = _generate_allocation_report(db)
        risk = _generate_risk_report(db)

        # Combine reports
        report_data = {
            "type": "comprehensive",
            "period_days": period_days,
            "performance": performance,
            "allocation": allocation,
            "risk": risk
        }

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        result = create_success_response(
            duration=duration,
            start_time=start_time,
            end_time=end_time,
            report=report_data
        )

        logger.info(f"Comprehensive report generation completed in {duration:.2f} seconds")
        return result

    except Exception as e:
        logger.error(f"Comprehensive report generation failed: {e}")
        return create_error_response(e)
