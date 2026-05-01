"""Celery application factory."""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "travellens",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.cv_tasks", "app.tasks.agent_tasks"],
)

celery_app.conf.update(
    task_serializer="pickle",
    result_serializer="pickle",
    accept_content=["pickle", "json"],
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
