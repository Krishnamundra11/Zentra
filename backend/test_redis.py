import asyncio
import ssl
import redis.asyncio as aioredis
from dotenv import load_dotenv
import os

load_dotenv('.env')
url = os.environ.get('REDIS_URL')
kwargs = {}
if 'rediss://' in url:
    kwargs['ssl_cert_reqs'] = ssl.CERT_NONE
clean_url = url.split('?')[0]

async def test():
    print('Testing redis:', clean_url)
    r = aioredis.from_url(clean_url, decode_responses=True, **kwargs)
    await r.ping()
    print('Redis ping OK')
    print(await r.keys('events:*'))

asyncio.run(test())
