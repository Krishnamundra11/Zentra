"""
seed_places.py — Populate the places table with well-known tourist spots
and generate CLIP embeddings from their Wikipedia image URLs.

Usage:
    cd backend
    python seed_places.py
"""
import asyncio
import httpx
from io import BytesIO
from PIL import Image

# Bootstrap path so app imports work
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import init_db, AsyncSessionLocal
from app.models.place import Place, PlaceEmbedding
from app.services.cv_pipeline import compute_clip_embedding, preprocess_image

SEED_PLACES = [
    {
        "name": "Eiffel Tower",
        "country": "France", "city": "Paris",
        "lat": 48.8584, "lng": 2.2945,
        "category": "landmark",
        "description": "Iconic iron lattice tower on the Champ de Mars in Paris.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Smiley.svg/200px-Smiley.svg.png",
        # Real usage: use actual landmark image URLs
    },
    {
        "name": "Taj Mahal",
        "country": "India", "city": "Agra",
        "lat": 27.1751, "lng": 78.0421,
        "category": "heritage",
        "description": "Ivory-white marble mausoleum on the bank of the Yamuna river.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Smiley.svg/200px-Smiley.svg.png",
    },
    {
        "name": "Colosseum",
        "country": "Italy", "city": "Rome",
        "lat": 41.8902, "lng": 12.4922,
        "category": "heritage",
        "description": "Ancient amphitheatre in the centre of Rome.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Smiley.svg/200px-Smiley.svg.png",
    },
    {
        "name": "Machu Picchu",
        "country": "Peru", "city": "Cusco Region",
        "lat": -13.1631, "lng": -72.5450,
        "category": "heritage",
        "description": "15th-century Inca citadel in the Andes Mountains.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Smiley.svg/200px-Smiley.svg.png",
    },
    {
        "name": "Sydney Opera House",
        "country": "Australia", "city": "Sydney",
        "lat": -33.8568, "lng": 151.2153,
        "category": "landmark",
        "description": "Multi-venue performing arts centre on Sydney Harbour.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Smiley.svg/200px-Smiley.svg.png",
    },
]


async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        for p in SEED_PLACES:
            # Check if already seeded
            from sqlalchemy import select
            existing = await db.scalar(select(Place).where(Place.name == p["name"]))
            if existing:
                print(f"  skip (exists): {p['name']}")
                continue

            # Download image
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    r = await client.get(p["image_url"])
                    img_bytes = r.content
            except Exception as exc:
                print(f"  failed to fetch image for {p['name']}: {exc}")
                continue

            # Compute embedding
            img = preprocess_image(img_bytes)
            embedding = compute_clip_embedding(img)

            # Insert place
            place = Place(
                name=p["name"], country=p["country"], city=p["city"],
                lat=p["lat"], lng=p["lng"],
                category=p.get("category"), description=p.get("description"),
            )
            db.add(place)
            await db.flush()

            # Insert embedding
            pe = PlaceEmbedding(place_id=place.id, embedding=embedding, source_image_url=p["image_url"])
            db.add(pe)
            await db.flush()
            print(f"  seeded: {p['name']}")

        await db.commit()
    print("Done seeding places.")


if __name__ == "__main__":
    asyncio.run(seed())
