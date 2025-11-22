import asyncio
import json
import fakeredis

from backend.src.services import index_retry_queue_redis as rq
from backend.src.api import admin_vectorstore as admin_mod

fake = fakeredis.FakeRedis()
# Monkeypatch the module's redis class method
rq.redis.Redis.from_url = staticmethod(lambda url, decode_responses=True: fake)

q = rq.RedisIndexJobQueue(url='redis://unused')
print('q client is fake:', q._client is fake)
import backend.src.services.index_retry_queue_redis as redis_mod
print('redis_mod is rq module:', redis_mod is rq)
try:
    client_from_redis_mod = redis_mod.redis.Redis.from_url('redis://unused')
    print('client_from_redis_mod is fake:', client_from_redis_mod is fake)
except Exception as e:
    print('calling redis_mod.redis.Redis.from_url raised', e)
print('q._client is client_from_redis_mod?', q._client is client_from_redis_mod)
print('id(q._client)=', id(q._client), 'id(client_from_redis_mod)=', id(client_from_redis_mod), 'id(fake)=', id(fake))
try:
    keys = fake.keys()
except Exception:
    try:
        keys = list(fake.scan_iter())
    except Exception:
        keys = []
print('fake keys:', keys)
key = getattr(redis_mod.RedisIndexJobQueue, 'KEY')
print('direct client lrange for failed:', client_from_redis_mod.lrange(key+':failed', 0, -1))

try:
    print('fake __dict__ keys:', list(fake.__dict__.keys()))
    if hasattr(fake, '_server'):
        try:
            server = fake._server
            if hasattr(server, 'data'):
                print('server.data keys:', list(server.data.keys()))
        except Exception:
            pass
    if hasattr(fake, '_db'):
        try:
            print('_db keys:', list(fake._db.keys()))
        except Exception:
            pass
except Exception:
    pass

async def run():
    job = await q.enqueue({'texts':['x'], 'metadatas':[{'doc_id':'f1'}], 'max_attempts':2})
    # force add_texts to fail by monkeypatching in module
    rq.add_texts = lambda texts, metadatas=None: False
    await q.process_all()
    print('failed list from q.list_failed():', q.list_failed())
    # inspect client directly after process_all
    print('direct client lrange for failed after processing:', client_from_redis_mod.lrange(key+':failed', 0, -1))
    print('admin_mod file:', getattr(admin_mod, '__file__', None))
    print('admin_mod.list_failed_jobs source:', admin_mod.list_failed_jobs.__code__.co_firstlineno)
    res = await admin_mod.list_failed_jobs()
    print('admin list_failed_jobs result:', res)

asyncio.run(run())
