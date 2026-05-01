"""Agent router — trigger planning and fetch itinerary."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.cache import get_json, set_json
from app.tasks.cv_tasks import run_agent_task  # reuse celery_app

router = APIRouter()


class AgentStartRequest(BaseModel):
    place_id: str
    place_name: str
    country: str = ""
    city: str = ""
    lat: float = 0.0
    lng: float = 0.0
    budget: str = "mid"
    travel_style: str = "couple"
    duration_days: int = 3
    diet: str = "any"
    accessibility: bool = False


class AgentStartResponse(BaseModel):
    task_id: str
    message: str = "Agent planning started. Poll /agent/{task_id}/status or watch WebSocket."


@router.post("/start", response_model=AgentStartResponse)
async def start_agent(body: AgentStartRequest):
    task_id = str(uuid.uuid4())
    prefs = {
        "budget": body.budget,
        "travel_style": body.travel_style,
        "duration_days": body.duration_days,
        "diet": body.diet,
        "accessibility": body.accessibility,
    }
    # Import here to avoid circular at module load
    from app.tasks.celery_app import celery_app
    celery_app.send_task(
        "agent_tasks.run_agent_task",
        args=[task_id, body.place_name, body.country, body.city, body.lat, body.lng, prefs],
    )
    return AgentStartResponse(task_id=task_id)


@router.get("/{task_id}/status")
async def agent_status(task_id: str):
    result = await get_json(f"itinerary:{task_id}")
    if result is None:
        return {"task_id": task_id, "status": "running"}
    return {"task_id": task_id, "status": "completed", "result": result}


@router.get("/itinerary/{task_id}")
async def get_itinerary(task_id: str):
    result = await get_json(f"itinerary:{task_id}")
    if result is None:
        raise HTTPException(404, "Itinerary not ready or not found")
    return result
