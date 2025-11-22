import fakeredis, json, asyncio
import backend.src.services.index_retry_queue_redis as rq
from backend.src.api import admin_vectorstore as admin_mod

fake = fakeredis.FakeRedis()
rq.redis.Redis.from_url = staticmethod(lambda url, decode_responses=True: fake)
q = rq.RedisIndexJobQueue(url='redis://unused')
# monkeypatch add_texts
rq.add_texts = lambda texts, metadatas=None: False

job = asyncio.get_event_loop().run_until_complete(q.enqueue({'texts':['x'],'metadatas':[{'doc_id':'f1'}],'max_attempts':2}))
asyncio.get_event_loop().run_until_complete(q.process_all())
print('failed list direct:', fake.lrange(q.KEY + ':failed',0,-1))
res = asyncio.get_event_loop().run_until_complete(admin_mod.list_failed_jobs())
print('admin list_failed_jobs ->', res)

# instantiate RedisIndexJobQueue via admin_mod path
from backend.src.services import index_retry_queue_redis as redis_mod
rq2 = redis_mod.RedisIndexJobQueue(url='redis://unused')
print('rq2 failed:', rq2.list_failed())
