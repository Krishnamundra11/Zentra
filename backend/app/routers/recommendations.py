"""
/recommend — Attractions, hotels, food, and similar places endpoints.
"""
from fastapi import APIRouter, Query
from app.services.agent_service import (
    _exec_search_nearby_attractions,
    _exec_search_hotels,
    _exec_search_homestays,
    _exec_search_restaurants,
)

router = APIRouter()


@router.get("/attractions")
async def get_attractions(
    place_id: str = Query(...),
    lat: float = Query(...),
    lng: float = Query(...),
    category: str = Query("tourist_attraction"),
    radius_km: float = Query(10),
):
    result = await _exec_search_nearby_attractions({
        "place_name": place_id, "lat": lat, "lng": lng,
        "category": category, "radius_km": radius_km,
    })
    return result


@router.get("/hotels")
async def get_hotels(
    place_id: str = Query(...),
    lat: float = Query(...),
    lng: float = Query(...),
    budget: str = Query("mid"),
):
    result = await _exec_search_hotels({
        "place_name": place_id, "lat": lat, "lng": lng, "budget": budget,
    })
    return result


@router.get("/homestays")
async def get_homestays(
    place_id: str = Query(...),
    lat: float = Query(...),
    lng: float = Query(...),
    guests: int = Query(2),
):
    result = await _exec_search_homestays({
        "place_name": place_id, "lat": lat, "lng": lng, "guests": guests,
    })
    return result


@router.get("/food")
async def get_food(
    place_id: str = Query(...),
    lat: float = Query(...),
    lng: float = Query(...),
    diet: str = Query("any"),
    budget: str = Query("mid"),
):
    result = await _exec_search_restaurants({
        "place_name": place_id, "lat": lat, "lng": lng,
        "diet": diet, "budget": budget,
    })
    return result
