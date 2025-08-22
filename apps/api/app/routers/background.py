"""Background tasks API router."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..models.user import User
from ..tasks.background_tasks import (
    cleanup_old_data,
    compute_index,
    generate_report,
    get_task_status,
    refresh_market_data,
)
from ..utils.token_dep import get_current_user

router = APIRouter()


class TaskResponse(BaseModel):
    """Response model for task creation."""

    task_id: str
    status: str
    message: str


class RefreshRequest(BaseModel):
    """Request model for refresh task."""

    mode: str = "smart"  # smart, full, minimal


class ComputeRequest(BaseModel):
    """Request model for compute task."""

    momentum_weight: float | None = None
    market_cap_weight: float | None = None
    risk_parity_weight: float | None = None


class ReportRequest(BaseModel):
    """Request model for report generation."""

    report_type: str = "performance"  # performance, allocation, risk
    period_days: int = 30


class CleanupRequest(BaseModel):
    """Request model for cleanup task."""

    days_to_keep: int = 365


@router.post("/refresh", response_model=TaskResponse)
def trigger_refresh_task(
    request: RefreshRequest, user: User = Depends(get_current_user)
) -> TaskResponse:
    """Trigger market data refresh in the background."""
    try:
        # Start the task
        task = refresh_market_data.delay(mode=request.mode)

        return TaskResponse(
            task_id=task.id,
            status="started",
            message=f"Market data refresh started in {request.mode} mode",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}") from e


@router.post("/compute", response_model=TaskResponse)
def trigger_compute_task(
    request: ComputeRequest, user: User = Depends(get_current_user)
) -> TaskResponse:
    """Trigger index computation in the background."""
    try:
        # Prepare strategy config if provided
        strategy_config = None
        if any(
            [
                request.momentum_weight,
                request.market_cap_weight,
                request.risk_parity_weight,
            ]
        ):
            strategy_config = {}
            if request.momentum_weight is not None:
                strategy_config["momentum_weight"] = request.momentum_weight
            if request.market_cap_weight is not None:
                strategy_config["market_cap_weight"] = request.market_cap_weight
            if request.risk_parity_weight is not None:
                strategy_config["risk_parity_weight"] = request.risk_parity_weight

        # Start the task
        task = compute_index.delay(strategy_config=strategy_config)

        return TaskResponse(
            task_id=task.id, status="started", message="Index computation started"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}") from e


@router.post("/report", response_model=TaskResponse)
def trigger_report_task(
    request: ReportRequest, user: User = Depends(get_current_user)
) -> TaskResponse:
    """Generate a report in the background."""
    try:
        # Start the task
        task = generate_report.delay(
            report_type=request.report_type, period_days=request.period_days
        )

        return TaskResponse(
            task_id=task.id,
            status="started",
            message=f"Report generation started for {request.report_type}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}") from e


@router.post("/cleanup", response_model=TaskResponse)
def trigger_cleanup_task(
    request: CleanupRequest, user: User = Depends(get_current_user)
) -> TaskResponse:
    """Clean up old data in the background."""
    try:
        # Start the task
        task = cleanup_old_data.delay(days_to_keep=request.days_to_keep)

        return TaskResponse(
            task_id=task.id,
            status="started",
            message=f"Data cleanup started, keeping {request.days_to_keep} days",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}") from e


@router.get("/status/{task_id}")
def get_task_result(
    task_id: str, user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Get the status and result of a background task."""
    return get_task_status(task_id)


@router.get("/active")
def get_active_tasks(user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Get list of active tasks."""
    try:
        from ..core.celery_app import celery_app

        # Get active tasks
        inspect = celery_app.control.inspect()
        active = inspect.active()
        scheduled = inspect.scheduled()
        reserved = inspect.reserved()

        return {
            "active": active or {},
            "scheduled": scheduled or {},
            "reserved": reserved or {},
            "stats": {
                "total_active": sum(len(tasks) for tasks in (active or {}).values()),
                "total_scheduled": sum(
                    len(tasks) for tasks in (scheduled or {}).values()
                ),
                "total_reserved": sum(
                    len(tasks) for tasks in (reserved or {}).values()
                ),
            },
        }
    except Exception as e:
        return {"error": str(e), "message": "Celery worker may not be running"}
