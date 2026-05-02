import asyncio
from app.utils.cache import get_redis
async def test():
    r = await get_redis()
    keys = await r.keys('itinerary:*')
    print('Itineraries:', keys)
    events = await r.keys('events:*')
    print('Events:', events)
asyncio.run(test())
