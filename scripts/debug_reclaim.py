import time
import json
import asyncio

import sys
import fakeredis

# Create a shared FakeRedis instance and inject a minimal `redis` module into
# sys.modules so importing the project's Redis adapter uses this fake client
fake = fakeredis.FakeRedis()

class _FakeRedisModule:
	class Redis:
		@staticmethod
		def from_url(url, decode_responses=True):
			return fake

sys.modules['redis'] = _FakeRedisModule()
from backend.src.services import index_retry_queue_redis as rq

q = rq.RedisIndexJobQueue(url='redis://unused')
print('client is fake:', q._client is fake)

# enqueue a job
job = asyncio.get_event_loop().run_until_complete(q.enqueue({'texts': ['a'], 'metadatas': [{}]}))
print('enqueued job id:', job['id'])
print('main queue:', fake.lrange(q.KEY, 0, -1))

# claim
claimed = q.claim_next(visibility_seconds=1)
print('claimed:', claimed)
print('processing list after claim:', fake.lrange(q.PROCESSING_KEY, 0, -1))
try:
	pm_keys = fake.hkeys(q.PROCESSING_META)
except Exception:
	try:
		pm_all = fake.hgetall(q.PROCESSING_META)
		pm_keys = list(pm_all.keys())
	except Exception:
		pm_keys = []
print('processing_meta hkeys:', pm_keys)
try:
	pm_val = fake.hget(q.PROCESSING_META, job['id'])
except Exception:
	pm_val = None
print('processing_meta hget for job:', pm_val)

# ack
ok = q.ack(job['id'])
print('acked ok:', ok)
print('processing list after ack:', fake.lrange(q.PROCESSING_KEY, 0, -1))
try:
	pm_keys_ack = fake.hkeys(q.PROCESSING_META)
except Exception:
	try:
		pm_keys_ack = list(fake.hgetall(q.PROCESSING_META).keys())
	except Exception:
		pm_keys_ack = []
print('processing_meta after ack hkeys:', pm_keys_ack)

# enqueue second job
job2 = asyncio.get_event_loop().run_until_complete(q.enqueue({'texts': ['b'], 'metadatas': [{}]}))
print('job2 id:', job2['id'])
claimed2 = q.claim_next(visibility_seconds=1)
print('claimed2:', claimed2)
print('processing list now:', fake.lrange(q.PROCESSING_KEY, 0, -1))
try:
	pm_keys2 = fake.hkeys(q.PROCESSING_META)
except Exception:
	try:
		pm_all2 = fake.hgetall(q.PROCESSING_META)
		pm_keys2 = list(pm_all2.keys())
	except Exception:
		pm_keys2 = []
print('processing_meta hkeys now:', pm_keys2)
try:
	pm_val2 = fake.hget(q.PROCESSING_META, job2['id'])
except Exception:
	pm_val2 = None
print('processing_meta hget now:', pm_val2)

# sleep until expire
print('sleeping 1.3s to let visibility expire...')
time.sleep(1.3)
print('time now:', time.time())
reclaimed = q.reclaim_expired()
print('reclaimed count:', reclaimed)
print('processing list after reclaim:', fake.lrange(q.PROCESSING_KEY, 0, -1))
print('main queue after reclaim:', fake.lrange(q.KEY, 0, -1))
try:
	pm_keys3 = fake.hkeys(q.PROCESSING_META)
except Exception:
	try:
		pm_all3 = fake.hgetall(q.PROCESSING_META)
		pm_keys3 = list(pm_all3.keys())
	except Exception:
		pm_keys3 = []
print('processing_meta after reclaim hkeys:', pm_keys3)
pm_content = {}
for k in pm_keys3:
	try:
		pm_content[k] = fake.hget(q.PROCESSING_META, k)
	except Exception:
		pm_content[k] = None
print('processing_meta content:', pm_content)

# show failed/scheduled
print('failed list:', fake.lrange(q.KEY + ':failed', 0, -1))
print('scheduled zrange:', fake.zrange(q.SCHEDULED_KEY, 0, -1, withscores=True))
