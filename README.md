# TravelPipe

A FastAPI service that polls the MBTA v3 API every 30 seconds, computes a fleet/alert snapshot, and appends it to parquet files. Parquet writes are dispatched to a Celery worker (Redis broker) and monitored with Flower.

## Architecture

```
FastAPI lifespan ──▶ poller (asyncio, 30s tick) ──▶ Celery .delay()
                                                       │
                                                       ▼
                                                Redis (broker)
                                                       │
                                                       ▼
                                          Celery worker ──▶ data/*.parquet
                                                       ▲
                                                       │
                                                     Flower (UI on :5555)
```

The poller is the scheduler; only the parquet appends run in the worker. The worker uses `--concurrency=1` so the read-modify-write append in `controllers/storage.py` stays race-free.

## Running locally

Install deps:

```
uv sync
```

Copy `.env.example` to `.env` and adjust if needed.

Start the four processes (separate terminals):

1. **Redis broker**

   ```
   redis-server
   ```

   Or via Docker: `docker run --rm -p 6379:6379 redis:7`. Verify with `redis-cli ping`.

2. **Celery worker**

   ```
   uv run celery -A controllers.celery_app worker --loglevel=info --concurrency=1 -Q parquet_writes
   ```

   On Windows, also pass `--pool=solo` (Celery's default prefork pool doesn't work on Windows):

   ```
   uv run celery -A controllers.celery_app worker --loglevel=info --concurrency=1 --pool=solo -Q parquet_writes
   ```

3. **Flower (queue monitor)**

   ```
   uv run celery -A controllers.celery_app flower --port=5555
   ```

   Open <http://localhost:5555>.

4. **FastAPI app**

   ```
   uv run fastapi dev main.py
   ```

After ~30 seconds the worker should process `parquet.append_snapshot` and `parquet.append_vehicle_positions` tasks; Flower's **Tasks** tab shows them in real time and `data/*.parquet` grows.
