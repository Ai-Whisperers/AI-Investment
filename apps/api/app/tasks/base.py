"""
Base task classes and utilities for Celery tasks.
Provides database session management and common task functionality.
"""

import logging
from typing import Any

from celery import Task
from celery.result import AsyncResult

from ..core.celery_app import celery_app
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """
    Base task with automatic database session management.
    Ensures proper session lifecycle and error handling.
    """

    def __call__(self, *args, **kwargs):
        """
        Execute task with database session.
        Automatically injects db session and handles commit/rollback.
        """
        db = SessionLocal()
        try:
            # Add db to kwargs for task execution
            kwargs["db"] = db
            result = self.run(*args, **kwargs)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"Task {self.name} failed: {e}")
            raise
        finally:
            db.close()


def get_task_status(task_id: str) -> dict[str, Any]:
    """
    Get the status of a background task.

    Args:
        task_id: Celery task ID

    Returns:
        Task status and result
    """
    try:
        result = AsyncResult(task_id, app=celery_app)

        response = {
            "task_id": task_id,
            "state": result.state,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
        }

        if result.state == "PENDING":
            response["status"] = "Task not found or not started"
        elif result.state == "PROGRESS":
            response["info"] = result.info
        elif result.state == "SUCCESS":
            response["result"] = result.result
        elif result.state == "FAILURE":
            response["error"] = str(result.info)

        return response

    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        return {
            "task_id": task_id,
            "state": "ERROR",
            "error": str(e)
        }


def create_error_response(error: Exception) -> dict[str, Any]:
    """
    Create standardized error response for failed tasks.

    Args:
        error: Exception that occurred

    Returns:
        Error response dictionary
    """
    from datetime import datetime

    return {
        "status": "failed",
        "error": str(error),
        "timestamp": datetime.utcnow().isoformat(),
    }


def create_success_response(
    duration: float,
    start_time,
    end_time,
    **kwargs
) -> dict[str, Any]:
    """
    Create standardized success response for completed tasks.

    Args:
        duration: Task duration in seconds
        start_time: Task start time
        end_time: Task end time
        **kwargs: Additional response fields

    Returns:
        Success response dictionary
    """
    response = {
        "status": "success",
        "duration_seconds": duration,
        "started_at": start_time.isoformat(),
        "completed_at": end_time.isoformat(),
    }
    response.update(kwargs)
    return response
