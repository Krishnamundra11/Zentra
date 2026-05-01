"""
/recognition — Image upload, task polling, and WebSocket progress stream.
"""
import uuid
import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.place import RecognitionEvent
from app.services.cv_pipeline import run_cv_pipeline, RecognitionResult
from app.tasks.cv_tasks import run_cv_task
from app.utils.cache import get_redis, set_json, get_json
from app.utils.s3 import upload_image

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_BYTES = 10 * 1024 * 1024   # 10 MB


# ── Schemas ────────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    task_id: str
    message: str = "Recognition started. Connect to /ws/{task_id} for live progress."


class RecognitionStatusResponse(BaseModel):
    task_id: str
    status: str
    place: Optional[dict] = None
    confidence: Optional[float] = None
    similar_places: list[dict] = []
    claude_description: str = ""


# ── Active WebSocket connections keyed by task_id ─────────────────────────────
_ws_connections: dict[str, WebSocket] = {}


async def _emit_ws(task_id: str, event: str, data: dict):
    """Send an event to the WebSocket client for this task."""
    ws = _ws_connections.get(task_id)
    if ws:
        try:
            await ws.send_json({"event": event, "data": data})
        except Exception:
            pass


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse)
async def upload_image_for_recognition(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept an image file, store it in S3, queue the CV pipeline as a Celery task.
    Returns a task_id the client uses to track progress.
    """
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_FILE_BYTES:
        raise HTTPException(413, "Image too large (max 10 MB).")

    task_id = str(uuid.uuid4())

    # Upload to S3
    s3_key = await upload_image(image_bytes, task_id, file.content_type)

    # Persist recognition event
    event = RecognitionEvent(task_id=task_id, image_s3_key=s3_key, status="pending")
    db.add(event)
    await db.flush()

    # Enqueue Celery task (passes bytes via Redis, not S3, for simplicity)
    run_cv_task.delay(task_id, image_bytes)

    return UploadResponse(task_id=task_id)


@router.get("/{task_id}", response_model=RecognitionStatusResponse)
async def get_recognition_status(task_id: str):
    """Poll recognition result from Redis cache."""
    cached = await get_json(f"recognition:{task_id}")
    if cached is None:
        return RecognitionStatusResponse(task_id=task_id, status="pending")
    return RecognitionStatusResponse(task_id=task_id, **cached)


@router.websocket("/ws/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint — client connects immediately after upload.
    Events: cv_started, cv_matched, cv_unknown, agent_started, agent_tool_called, itinerary_ready.
    """
    await websocket.accept()
    _ws_connections[task_id] = websocket
    try:
        while True:
            # Keep connection alive; results are pushed from the Celery worker via the cache
            cached = await get_json(f"recognition:{task_id}")
            if cached and cached.get("status") in ("matched", "likely", "unknown"):
                await websocket.send_json({"event": cached["status"], "data": cached})
                break
            await asyncio.sleep(0.5)
            # Also relay agent events stored in Redis list
            events_raw = await get_json(f"events:{task_id}")
            if events_raw:
                for ev in events_raw:
                    await websocket.send_json(ev)
    except WebSocketDisconnect:
        pass
    finally:
        _ws_connections.pop(task_id, None)
