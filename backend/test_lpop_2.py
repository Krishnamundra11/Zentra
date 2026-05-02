import asyncio
import ssl
import redis.asyncio as aioredis
from app.config import settings
async def test():
    url = settings.redis_url.split('?')[0]
    r = aioredis.from_url(url, ssl_cert_reqs=ssl.CERT_NONE)
    print(await r.ping())
asyncio.run(test())
