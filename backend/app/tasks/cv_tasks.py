"""Celery tasks — heavy background processing for CV pipeline and agent."""
import asyncio
import json
import logging
from celery import shared_task

from app.tasks.celery_app import celery_app
from app.utils.cache import set_json_sync, push_event_sync

logger = logging.getLogger(__name__)


@celery_app.task(name="cv_tasks.run_cv_task", bind=True, max_retries=2)
def run_cv_task(self, task_id: str, image_bytes: bytes):
    """Run the full CV pipeline synchronously inside the Celery worker."""
    from app.database import AsyncSessionLocal
    from app.services.cv_pipeline import run_cv_pipeline

    async def _run():
        push_event_sync(task_id, {"event": "cv_started", "data": {"task_id": task_id}})
        async with AsyncSessionLocal() as db:
            result = await run_cv_pipeline(image_bytes, db)

        payload = {
            "status": result.status,
            "confidence": result.confidence,
            "claude_description": result.claude_description,
            "place": None,
            "similar_places": [],
        }
        if result.place:
            payload["place"] = {
                "id": result.place.place_id,
                "name": result.place.name,
                "country": result.place.country,
                "city": result.place.city,
                "lat": result.place.lat,
                "lng": result.place.lng,
                "description": result.place.description,
                "similarity": result.place.similarity,
            }
        payload["similar_places"] = [
            {
                "id": p.place_id,
                "name": p.name,
                "country": p.country,
                "city": p.city,
                "similarity": p.similarity,
            }
            for p in result.similar_places
        ]
        set_json_sync(f"recognition:{task_id}", payload, ttl=86400)
        push_event_sync(task_id, {"event": result.status, "data": payload})

    asyncio.run(_run())


@celery_app.task(name="agent_tasks.run_agent_task", bind=True, max_retries=1)
def run_agent_task(self, task_id: str, place_name: str, country: str, city: str,
                   lat: float, lng: float, prefs_dict: dict):
    """Run the agentic travel planner synchronously inside the Celery worker."""
    from app.services.agent_service import run_travel_agent, UserPrefs

    prefs = UserPrefs(**prefs_dict)

    async def _progress(event: str, data):
        push_event_sync(task_id, {"event": event, "data": data})

    async def _run():
        plan = await run_travel_agent(
            place_name, country, city, lat, lng, prefs,
            progress_callback=_progress,
        )
        payload = {
            "place_name": plan.place_name,
            "itinerary": plan.itinerary,
            "attractions": plan.attractions,
            "hotels": plan.hotels,
            "homestays": plan.homestays,
            "restaurants": plan.restaurants,
            "travel_info": plan.travel_info,
            "booking_links": plan.booking_links,
        }
        set_json_sync(f"itinerary:{task_id}", payload, ttl=604800)   # 7 days

    asyncio.run(_run())
