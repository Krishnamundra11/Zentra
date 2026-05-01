"""
Agentic Travel Planner — Claude tool-use loop.

The agent receives a recognised place + user preferences and autonomously:
  1. Fetches nearby attractions
  2. Searches hotels and homestays
  3. Finds restaurant recommendations
  4. Retrieves travel info (best season, how to reach)
  5. Synthesises a day-by-day itinerary with booking links
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

import anthropic
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

AnthropicClient = anthropic.Anthropic(api_key=settings.anthropic_api_key)


# ── Tool Definitions (Claude tool_use format) ─────────────────────────────────

TRAVEL_TOOLS = [
    {
        "name": "search_nearby_attractions",
        "description": "Search for tourist attractions, museums, parks, and points of interest near a location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "place_name": {"type": "string", "description": "Name of the place"},
                "lat": {"type": "number"},
                "lng": {"type": "number"},
                "radius_km": {"type": "number", "default": 10},
                "category": {"type": "string", "description": "e.g. museum, park, temple, beach"}
            },
            "required": ["place_name", "lat", "lng"]
        }
    },
    {
        "name": "search_hotels",
        "description": "Search for hotels and resorts near a location with price and rating filters.",
        "input_schema": {
            "type": "object",
            "properties": {
                "place_name": {"type": "string"},
                "lat": {"type": "number"},
                "lng": {"type": "number"},
                "budget": {"type": "string", "enum": ["budget", "mid", "luxury"]},
                "checkin": {"type": "string"},
                "checkout": {"type": "string"}
            },
            "required": ["place_name", "lat", "lng"]
        }
    },
    {
        "name": "search_homestays",
        "description": "Search for homestays and vacation rentals near a location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "place_name": {"type": "string"},
                "lat": {"type": "number"},
                "lng": {"type": "number"},
                "guests": {"type": "integer", "default": 2}
            },
            "required": ["place_name", "lat", "lng"]
        }
    },
    {
        "name": "search_restaurants",
        "description": "Find restaurants and food places near a location matching dietary preferences.",
        "input_schema": {
            "type": "object",
            "properties": {
                "place_name": {"type": "string"},
                "lat": {"type": "number"},
                "lng": {"type": "number"},
                "cuisine": {"type": "string"},
                "diet": {"type": "string", "enum": ["any", "vegetarian", "vegan"]},
                "budget": {"type": "string", "enum": ["budget", "mid", "luxury"]}
            },
            "required": ["place_name", "lat", "lng"]
        }
    },
    {
        "name": "get_travel_info",
        "description": "Get general travel information for a destination: best season, how to reach, safety, local tips.",
        "input_schema": {
            "type": "object",
            "properties": {
                "place_name": {"type": "string"},
                "country": {"type": "string"}
            },
            "required": ["place_name"]
        }
    },
    {
        "name": "get_booking_links",
        "description": "Generate booking links for hotels, tours, and tickets for a place.",
        "input_schema": {
            "type": "object",
            "properties": {
                "place_name": {"type": "string"},
                "hotel_name": {"type": "string"},
                "checkin": {"type": "string"},
                "checkout": {"type": "string"}
            },
            "required": ["place_name"]
        }
    }
]


# ── Tool Executors ─────────────────────────────────────────────────────────────

async def _exec_search_nearby_attractions(inp: dict) -> dict:
    """Call Google Places Nearby Search."""
    params = {
        "location": f"{inp['lat']},{inp['lng']}",
        "radius": int(inp.get("radius_km", 10) * 1000),
        "type": inp.get("category", "tourist_attraction"),
        "key": settings.google_places_api_key,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json", params=params)
        data = r.json()
    results = []
    for p in data.get("results", [])[:8]:
        results.append({
            "name": p.get("name"),
            "rating": p.get("rating"),
            "vicinity": p.get("vicinity"),
            "types": p.get("types", [])[:3],
            "place_id": p.get("place_id"),
        })
    return {"attractions": results}


async def _exec_search_hotels(inp: dict) -> dict:
    """Stub — in production call Booking.com or similar API."""
    return {
        "hotels": [
            {"name": f"Hotel near {inp['place_name']}", "price_per_night": 120,
             "rating": 4.3, "booking_url": "https://booking.com/placeholder"},
        ],
        "note": "Connect Booking.com API for live data."
    }


async def _exec_search_homestays(inp: dict) -> dict:
    """Stub — in production call Airbnb API."""
    return {
        "homestays": [
            {"name": f"Cozy stay near {inp['place_name']}", "price_per_night": 65,
             "host_rating": 4.8, "url": "https://airbnb.com/placeholder"},
        ]
    }


async def _exec_search_restaurants(inp: dict) -> dict:
    """Call Google Places for restaurants."""
    params = {
        "location": f"{inp['lat']},{inp['lng']}",
        "radius": 3000,
        "type": "restaurant",
        "key": settings.google_places_api_key,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json", params=params)
        data = r.json()
    results = [
        {"name": p.get("name"), "rating": p.get("rating"), "vicinity": p.get("vicinity")}
        for p in data.get("results", [])[:6]
    ]
    return {"restaurants": results}


async def _exec_get_travel_info(inp: dict) -> dict:
    """Return structured travel info (stub — could call a travel DB or Wikipedia)."""
    return {
        "place": inp["place_name"],
        "best_season": "October – March (cooler and dry)",
        "how_to_reach": "Nearest international airport; local buses and taxis available.",
        "safety": "Generally safe for tourists; standard precautions apply.",
        "local_tips": ["Carry cash for local markets", "Respect local customs at religious sites"],
    }


async def _exec_get_booking_links(inp: dict) -> dict:
    """Generate affiliate booking URLs."""
    import urllib.parse
    base = "https://www.booking.com/searchresults.html"
    q = urllib.parse.urlencode({"ss": inp["place_name"], "checkin": inp.get("checkin", ""), "checkout": inp.get("checkout", "")})
    return {
        "hotels_link": f"{base}?{q}",
        "tours_link": f"https://www.viator.com/searchResults/all?text={urllib.parse.quote(inp['place_name'])}",
    }


TOOL_EXECUTORS: dict[str, Callable[[dict], Awaitable[dict]]] = {
    "search_nearby_attractions": _exec_search_nearby_attractions,
    "search_hotels": _exec_search_hotels,
    "search_homestays": _exec_search_homestays,
    "search_restaurants": _exec_search_restaurants,
    "get_travel_info": _exec_get_travel_info,
    "get_booking_links": _exec_get_booking_links,
}


async def execute_tool(name: str, inp: dict) -> str:
    """Dispatch tool by name and return JSON string result."""
    executor = TOOL_EXECUTORS.get(name)
    if not executor:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = await executor(inp)
        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        logger.exception("Tool %s failed", name)
        return json.dumps({"error": str(exc)})


# ── Agent Loop ─────────────────────────────────────────────────────────────────

@dataclass
class UserPrefs:
    budget: str = "mid"               # budget | mid | luxury
    travel_style: str = "couple"      # solo | couple | family | group
    duration_days: int = 3
    diet: str = "any"                 # any | vegetarian | vegan
    accessibility: bool = False


@dataclass
class TravelPlan:
    place_name: str
    itinerary: dict = field(default_factory=dict)
    attractions: list = field(default_factory=list)
    hotels: list = field(default_factory=list)
    homestays: list = field(default_factory=list)
    restaurants: list = field(default_factory=list)
    travel_info: dict = field(default_factory=dict)
    booking_links: dict = field(default_factory=dict)
    raw_agent_output: str = ""


def _build_system_prompt(place_name: str, country: str, city: str, prefs: UserPrefs) -> str:
    return f"""You are TravelLens, an expert AI travel planner.

The user has identified the tourist destination: **{place_name}** in {city}, {country}.

User preferences:
- Budget: {prefs.budget}
- Travel style: {prefs.travel_style}
- Duration: {prefs.duration_days} days
- Diet: {prefs.diet}
- Accessibility needs: {"Yes" if prefs.accessibility else "No"}

Your task:
1. Use the available tools to gather: nearby attractions, hotel options, homestay options, restaurants, travel info, and booking links.
2. After gathering data, synthesise a structured day-by-day itinerary.
3. Return your final answer as valid JSON matching this schema:
{{
  "itinerary": {{"day_1": [{{"time": "09:00", "activity": "...", "duration_hrs": 2}}]}},
  "summary": "...",
  "tips": ["..."]
}}

Be thorough — use multiple tool calls to gather comprehensive information before building the itinerary."""


async def run_travel_agent(
    place_name: str,
    country: str,
    city: str,
    lat: float,
    lng: float,
    prefs: UserPrefs,
    progress_callback: Callable[[str, Any], Awaitable[None]] | None = None,
) -> TravelPlan:
    """
    Main agentic loop. progress_callback(event_type, data) is called at each step
    so the WebSocket layer can stream progress to the frontend.
    """
    plan = TravelPlan(place_name=place_name)
    messages: list[dict] = [
        {"role": "user", "content": _build_system_prompt(place_name, country, city, prefs)}
    ]

    if progress_callback:
        await progress_callback("agent_started", {"place": place_name})

    max_iterations = 12   # safety cap

    for iteration in range(max_iterations):
        response = AnthropicClient.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            tools=TRAVEL_TOOLS,
            messages=messages,
        )

        # Collect assistant message
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Extract final JSON plan from last text block
            for block in response.content:
                if hasattr(block, "text"):
                    plan.raw_agent_output = block.text
                    try:
                        idx = block.text.find("{")
                        end = block.text.rfind("}") + 1
                        plan.itinerary = json.loads(block.text[idx:end])
                    except (ValueError, json.JSONDecodeError):
                        plan.itinerary = {"raw": block.text}
            break

        # Execute all tool calls
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            tool_name = block.name
            tool_input = block.input

            if progress_callback:
                await progress_callback("agent_tool_called", {"tool": tool_name, "input": tool_input})

            result_str = await execute_tool(tool_name, tool_input)
            result_data = json.loads(result_str)

            # Store results in plan
            if tool_name == "search_nearby_attractions":
                plan.attractions = result_data.get("attractions", [])
            elif tool_name == "search_hotels":
                plan.hotels = result_data.get("hotels", [])
            elif tool_name == "search_homestays":
                plan.homestays = result_data.get("homestays", [])
            elif tool_name == "search_restaurants":
                plan.restaurants = result_data.get("restaurants", [])
            elif tool_name == "get_travel_info":
                plan.travel_info = result_data
            elif tool_name == "get_booking_links":
                plan.booking_links = result_data

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_str,
            })

        messages.append({"role": "user", "content": tool_results})

    if progress_callback:
        await progress_callback("itinerary_ready", {"plan": plan.itinerary})

    return plan
