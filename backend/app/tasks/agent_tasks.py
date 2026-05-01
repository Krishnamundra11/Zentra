"""Agent Celery task — re-exported from cv_tasks for clarity."""
# The actual task is defined in cv_tasks.py and registered with celery_app.
# This file exists so the celery include path app.tasks.agent_tasks resolves.
from app.tasks.cv_tasks import run_agent_task  # noqa: F401
