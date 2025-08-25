"""
API endpoints for system monitoring and health checks
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from app.core.dependencies import get_db
from app.services.monitoring_service import (
    get_monitoring_service,
    SystemMetrics,
    SignalMetrics,
    Alert
)
from app.services.discord_notifier import get_discord_notifier

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"],
    responses={404: {"description": "Not found"}},
)


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "waardhaven-autoindex",
        "version": "1.0.0"
    }


@router.get("/system/status")
async def get_system_status():
    """Get comprehensive system health status."""
    
    monitoring = get_monitoring_service()
    status = await monitoring.get_health_status()
    
    return status


@router.get("/system/metrics")
async def get_system_metrics():
    """Get current system metrics."""
    
    monitoring = get_monitoring_service()
    metrics = await monitoring.collect_system_metrics()
    
    return {
        "timestamp": metrics.timestamp.isoformat(),
        "database_connected": metrics.database_connected,
        "cache_connected": metrics.cache_connected,
        "api_latency": metrics.api_latency,
        "memory_usage": metrics.memory_usage,
        "cpu_usage": metrics.cpu_usage,
        "active_connections": metrics.active_connections,
        "error_rate": metrics.error_rate,
        "signal_processing_rate": metrics.signal_processing_rate
    }


@router.get("/system/metrics/history")
async def get_metrics_history(hours: int = 24):
    """Get historical system metrics."""
    
    monitoring = get_monitoring_service()
    
    # Filter metrics by time range
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    history = [
        {
            "timestamp": m.timestamp.isoformat(),
            "api_latency": m.api_latency,
            "memory_usage": m.memory_usage,
            "cpu_usage": m.cpu_usage,
            "error_rate": m.error_rate,
            "signal_processing_rate": m.signal_processing_rate
        }
        for m in monitoring.metrics_history
        if m.timestamp > cutoff
    ]
    
    return {
        "hours": hours,
        "data_points": len(history),
        "metrics": history
    }


@router.get("/signals/metrics")
async def get_signal_metrics(db: Session = Depends(get_db)):
    """Get signal performance metrics."""
    
    monitoring = get_monitoring_service()
    metrics = await monitoring.collect_signal_metrics(db)
    
    return {
        "total_signals": metrics.total_signals,
        "signals_today": metrics.signals_today,
        "high_confidence_signals": metrics.high_confidence_signals,
        "executed_signals": metrics.executed_signals,
        "win_rate": metrics.win_rate,
        "average_return": metrics.average_return,
        "best_performer": metrics.best_performer,
        "worst_performer": metrics.worst_performer,
        "pending_signals": metrics.pending_signals
    }


@router.get("/alerts")
async def get_alerts(hours: int = 24):
    """Get recent system alerts."""
    
    monitoring = get_monitoring_service()
    
    # Filter alerts by time range
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    alerts = [
        {
            "level": a.level,
            "category": a.category,
            "title": a.title,
            "message": a.message,
            "timestamp": a.timestamp.isoformat(),
            "metadata": a.metadata
        }
        for a in monitoring.alert_history
        if a.timestamp > cutoff
    ]
    
    return {
        "hours": hours,
        "total_alerts": len(alerts),
        "alerts": alerts
    }


@router.post("/alerts/test")
async def test_alert(
    level: str = "info",
    title: str = "Test Alert",
    message: str = "This is a test alert from the monitoring system"
):
    """Send a test alert to verify notification system."""
    
    monitoring = get_monitoring_service()
    
    alert = await monitoring.create_alert(
        level=level,
        category="test",
        title=title,
        message=message,
        metadata={"test": True, "timestamp": datetime.utcnow().isoformat()}
    )
    
    return {
        "success": True,
        "alert": {
            "level": alert.level,
            "title": alert.title,
            "message": alert.message
        }
    }


@router.post("/discord/test")
async def test_discord():
    """Test Discord webhook notification."""
    
    notifier = get_discord_notifier()
    
    if not notifier.enabled:
        raise HTTPException(
            status_code=503,
            detail="Discord webhook not configured"
        )
    
    success = await notifier.send_system_alert(
        level="info",
        title="Test Notification",
        message="Discord webhook is working correctly!",
        details={
            "timestamp": datetime.utcnow().isoformat(),
            "source": "monitoring API"
        }
    )
    
    return {
        "success": success,
        "message": "Discord notification sent" if success else "Failed to send notification"
    }


@router.get("/performance/summary")
async def get_performance_summary(db: Session = Depends(get_db)):
    """Get overall performance summary."""
    
    monitoring = get_monitoring_service()
    signal_metrics = await monitoring.collect_signal_metrics(db)
    system_metrics = await monitoring.collect_system_metrics()
    
    # Calculate uptime
    uptime_hours = 24  # Would normally calculate from start time
    
    # Calculate success rate
    success_rate = (signal_metrics.win_rate if signal_metrics.executed_signals > 0 else 0)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "status": "healthy" if system_metrics.database_connected else "degraded",
            "uptime_hours": uptime_hours,
            "api_latency": system_metrics.api_latency,
            "error_rate": system_metrics.error_rate
        },
        "signals": {
            "total": signal_metrics.total_signals,
            "today": signal_metrics.signals_today,
            "pending": len(signal_metrics.pending_signals),
            "success_rate": success_rate
        },
        "performance": {
            "win_rate": signal_metrics.win_rate,
            "average_return": signal_metrics.average_return,
            "best_performer": signal_metrics.best_performer,
            "worst_performer": signal_metrics.worst_performer
        }
    }


@router.post("/monitoring/start")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start the monitoring service in the background."""
    
    monitoring = get_monitoring_service()
    
    # Add monitoring loop to background tasks
    background_tasks.add_task(monitoring.run_monitoring_loop)
    
    return {
        "success": True,
        "message": "Monitoring service started"
    }


@router.get("/dashboard/data")
async def get_dashboard_data(db: Session = Depends(get_db)):
    """Get all data needed for monitoring dashboard."""
    
    monitoring = get_monitoring_service()
    
    # Collect all metrics
    system_metrics = await monitoring.collect_system_metrics()
    signal_metrics = await monitoring.collect_signal_metrics(db)
    
    # Get recent alerts
    cutoff = datetime.utcnow() - timedelta(hours=1)
    recent_alerts = [
        a for a in monitoring.alert_history
        if a.timestamp > cutoff
    ]
    
    # Get metrics history (last 6 hours)
    history_cutoff = datetime.utcnow() - timedelta(hours=6)
    metrics_history = [
        m for m in monitoring.metrics_history
        if m.timestamp > history_cutoff
    ]
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "database_connected": system_metrics.database_connected,
            "cache_connected": system_metrics.cache_connected,
            "api_latency": system_metrics.api_latency,
            "memory_usage": system_metrics.memory_usage,
            "cpu_usage": system_metrics.cpu_usage,
            "error_rate": system_metrics.error_rate
        },
        "signals": {
            "total": signal_metrics.total_signals,
            "today": signal_metrics.signals_today,
            "high_confidence": signal_metrics.high_confidence_signals,
            "pending": signal_metrics.pending_signals[:5],  # Top 5 pending
            "win_rate": signal_metrics.win_rate
        },
        "alerts": {
            "count": len(recent_alerts),
            "critical": len([a for a in recent_alerts if a.level == 'critical']),
            "warning": len([a for a in recent_alerts if a.level == 'warning']),
            "info": len([a for a in recent_alerts if a.level == 'info'])
        },
        "history": {
            "timestamps": [m.timestamp.isoformat() for m in metrics_history],
            "api_latency": [m.api_latency for m in metrics_history],
            "memory_usage": [m.memory_usage for m in metrics_history],
            "cpu_usage": [m.cpu_usage for m in metrics_history],
            "signal_rate": [m.signal_processing_rate for m in metrics_history]
        }
    }