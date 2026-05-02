import asyncio
from app.utils.cache import get_redis
async def test():
    r = await get_redis()
    print("Redis success!")
    print(await r.keys('*'))
asyncio.run(test())
