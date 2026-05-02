"""
Computer Vision Pipeline
  Stage 1: Preprocess image
  Stage 2: CLIP embedding
  Stage 3: pgvector similarity search
    Stage 4: Gemini Vision verification
  Stage 5: Fallback — visually similar places
"""
from __future__ import annotations

import hashlib
import io
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import torch
from PIL import Image
import google.generativeai as genai
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from transformers import CLIPModel, CLIPProcessor

from app.config import settings
from app.models.place import Place, PlaceEmbedding

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.gemini_api_key)

# ── CLIP Model (loaded once at worker startup) ─────────────────────────────────
_clip_model: Optional[CLIPModel] = None
_clip_processor: Optional[CLIPProcessor] = None


def get_clip():
    global _clip_model, _clip_processor
    if _clip_model is None:
        logger.info("Loading CLIP model: %s", settings.clip_model)
        _clip_model = CLIPModel.from_pretrained(settings.clip_model)
        _clip_processor = CLIPProcessor.from_pretrained(settings.clip_model)
        _clip_model.eval()
    return _clip_model, _clip_processor


# ── Data classes ───────────────────────────────────────────────────────────────

@dataclass
class CandidatePlace:
    place_id: str
    name: str
    country: str
    city: str
    lat: float
    lng: float
    description: str
    distance: float          # cosine distance (lower = more similar)
    similarity: float        # 1 - distance


@dataclass
class RecognitionResult:
    status: str              # "matched" | "likely" | "unknown"
    place: Optional[CandidatePlace] = None
    confidence: float = 0.0
    claude_description: str = ""
    similar_places: list[CandidatePlace] = field(default_factory=list)
    image_sha: str = ""


# ── Pipeline ───────────────────────────────────────────────────────────────────

def preprocess_image(image_bytes: bytes) -> torch.Tensor:
    """Load, validate, and return image as PIL Image."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return img


def compute_clip_embedding(img: Image.Image) -> list[float]:
    """Return 512-d CLIP embedding as plain Python list."""
    model, processor = get_clip()
    inputs = processor(images=img, return_tensors="pt")
    with torch.no_grad():
        features = model.get_image_features(**inputs)
        features = features / features.norm(dim=-1, keepdim=True)   # L2-normalise
    return features[0].tolist()


async def vector_search(
    db: AsyncSession,
    embedding: list[float],
    top_k: int = 5,
    exclude_ids: list[str] | None = None,
) -> list[CandidatePlace]:
    """Cosine similarity search against place_embeddings via pgvector."""
    embedding_str = f"[{','.join(str(v) for v in embedding)}]"
    exclude_clause = ""
    if exclude_ids:
        ids = ", ".join(f"'{x}'" for x in exclude_ids)
        exclude_clause = f"AND p.id NOT IN ({ids})"

    sql = text(f"""
        SELECT
            p.id, p.name, p.country, p.city, p.lat, p.lng, p.description,
            pe.embedding <=> CAST(:emb AS vector) AS distance
        FROM place_embeddings pe
        JOIN places p ON p.id = pe.place_id
        WHERE 1=1 {exclude_clause}
        ORDER BY pe.embedding <=> CAST(:emb AS vector)
        LIMIT :k
    """)
    rows = (await db.execute(sql, {"emb": embedding_str, "k": top_k})).mappings().all()
    return [
        CandidatePlace(
            place_id=r["id"],
            name=r["name"],
            country=r["country"] or "",
            city=r["city"] or "",
            lat=r["lat"] or 0.0,
            lng=r["lng"] or 0.0,
            description=r["description"] or "",
            distance=float(r["distance"]),
            similarity=round(1.0 - float(r["distance"]), 4),
        )
        for r in rows
    ]


def _extract_json_block(text: str) -> dict | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


async def gemini_verify(
    image_bytes: bytes,
    candidate: CandidatePlace,
) -> tuple[float, str]:
    """
    Ask Gemini Vision to verify whether the image matches the candidate place.
    Returns (confidence: 0-1, description: str).
    """
    model = genai.GenerativeModel(settings.gemini_vision_model)
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    prompt = f"""You are a travel expert and landmark identifier.

I have an image that my embedding model thinks might be "{candidate.name}" in {candidate.city}, {candidate.country}.

Please analyse the image carefully and:
1. State whether you believe this IS that place (confidence 0.0–1.0).
2. List the visible landmarks or features that support your conclusion.
3. If it is NOT that place, describe what place it actually appears to be.

Respond ONLY as valid JSON in this exact format:
{{
  "is_match": true,
  "confidence": 0.92,
  "visible_features": ["Eiffel Tower", "Seine River"],
  "actual_place": "Eiffel Tower, Paris, France",
  "description": "A daytime shot of the Eiffel Tower seen from Trocadéro gardens."
}}"""

    response = model.generate_content([prompt, img])
    data = _extract_json_block(response.text or "")
    if not data:
        return 0.0, ""
    confidence = float(data.get("confidence", 0.0)) if data.get("is_match") else 0.0
    description = data.get("description", "")
    return confidence, description


async def run_cv_pipeline(
    image_bytes: bytes,
    db: AsyncSession,
) -> RecognitionResult:
    """Full CV pipeline — returns a RecognitionResult."""
    image_sha = hashlib.sha256(image_bytes).hexdigest()

    # Stage 1: Preprocess
    img = preprocess_image(image_bytes)

    # Stage 2: CLIP embedding
    embedding = compute_clip_embedding(img)

    # Stage 3: Vector search
    candidates = await vector_search(db, embedding, top_k=5)

    if not candidates:
        return RecognitionResult(status="unknown", image_sha=image_sha)

    best = candidates[0]
    logger.info("Best candidate: %s (distance=%.4f)", best.name, best.distance)

    # Stage 4: Gemini Vision verification (only for plausible matches)
    if best.distance < settings.cv_likely_match_threshold:
        confidence, description = await gemini_verify(image_bytes, best)
        logger.info("LLM confidence: %.2f", confidence)

        if confidence >= settings.llm_confidence_threshold:
            return RecognitionResult(
                status="matched",
                place=best,
                confidence=confidence,
                claude_description=description,
                image_sha=image_sha,
            )
        elif confidence >= 0.4:
            return RecognitionResult(
                status="likely",
                place=best,
                confidence=confidence,
                claude_description=description,
                similar_places=candidates[1:4],
                image_sha=image_sha,
            )

    # Stage 5: Fallback — similar places
    similar = await vector_search(db, embedding, top_k=3, exclude_ids=[c.place_id for c in candidates])
    return RecognitionResult(
        status="unknown",
        similar_places=similar or candidates[:3],
        image_sha=image_sha,
    )
