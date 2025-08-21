"""Celery application configuration."""

from celery import Celery

from .config import settings

# Create Celery app
celery_app = Celery(
    "waardhaven_tasks",
    broker=settings.REDIS_URL or "redis://localhost:6379/1",
    backend=settings.REDIS_URL or "redis://localhost:6379/1",
    include=["app.tasks.background_tasks"],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,  # Results expire after 1 hour
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes hard limit
    task_soft_time_limit=1500,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,  # Disable prefetching for long tasks
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks to prevent memory leaks
)

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.background_tasks.refresh_market_data": {"queue": "high_priority"},
    "app.tasks.background_tasks.compute_index": {"queue": "high_priority"},
    "app.tasks.background_tasks.generate_report": {"queue": "low_priority"},
    "app.tasks.background_tasks.cleanup_old_data": {"queue": "low_priority"},
}

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "daily-refresh": {
        "task": "app.tasks.background_tasks.refresh_market_data",
        "schedule": 86400.0,  # Daily (24 hours)
        "options": {"queue": "high_priority"},
    },
    "hourly-index-computation": {
        "task": "app.tasks.background_tasks.compute_index",
        "schedule": 3600.0,  # Hourly
        "options": {"queue": "high_priority"},
    },
    "weekly-cleanup": {
        "task": "app.tasks.background_tasks.cleanup_old_data",
        "schedule": 604800.0,  # Weekly
        "options": {"queue": "low_priority"},
    },
}
