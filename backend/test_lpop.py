import asyncio
from app.utils.cache import get_redis, push_event_sync
async def test():
    push_event_sync('test_task', {'event':'abc'})
    r = await get_redis()
    res = await r.lpop('events:test_task')
    print('lpop returned:', res)
asyncio.run(test())
