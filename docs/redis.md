Redis for local development
===========================

This project supports an optional Redis-backed index retry queue. For local development you can run Redis via WSL2, a native Windows build, or Docker. Tests use `fakeredis` so a running Redis is not required for CI/local tests.

Quick options
-------------

- WSL2 (recommended):
  - Install WSL and Ubuntu, then inside WSL run:
    ```bash
    sudo apt update
    sudo apt install -y redis-server
    sudo service redis-server start
    redis-cli ping  # should reply PONG
    ```
  - Use `REDIS_URL=redis://127.0.0.1:6379/0` from Windows to connect.

- Docker (fast, reproducible):
  - From repo root:
    ```powershell
    docker compose -f docker-compose.redis.yml up -d
    # tear down:
    docker compose -f docker-compose.redis.yml down
    ```

- Native Windows (alternative):
  - Use Chocolatey `choco install redis-64` or Memurai (Windows-native Redis-compatible server).

Env vars
--------

- `INDEX_RETRY_QUEUE_BACKEND=redis` to enable the Redis adapter.
- `REDIS_URL` default: `redis://127.0.0.1:6379/0`

Testing
-------

Unit tests include `fakeredis` so they don't require a running Redis. To run the Redis-adapter tests locally:

```powershell
cd backend
uv run pytest tests/unit/test_index_retry_queue_redis_adapter.py -q
```

Security
--------

For development bind Redis to `127.0.0.1` and avoid exposing it publicly. For production use secure passwords, firewall rules, and managed Redis services.
