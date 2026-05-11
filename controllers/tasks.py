from datetime import datetime
from typing import Any

from controllers import storage
from controllers.celery_app import app


@app.task(name="parquet.append_snapshot")
def append_snapshot_task(snapshot: dict[str, Any]) -> None:
    ts = snapshot.get("timestamp")
    if isinstance(ts, str):
        snapshot = {**snapshot, "timestamp": datetime.fromisoformat(ts)}
    storage.append_snapshot(snapshot)


@app.task(name="parquet.append_vehicle_positions")
def append_vehicle_positions_task(
    positions: list[dict[str, Any]], timestamp_iso: str
) -> None:
    timestamp = datetime.fromisoformat(timestamp_iso)
    storage.append_vehicle_positions(positions, timestamp)
