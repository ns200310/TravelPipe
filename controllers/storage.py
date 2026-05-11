import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from pydantic import ValidationError

from controllers.schemas import JSON_COLUMNS, SnapshotRow, VehiclePositionRow

log = logging.getLogger(__name__)

SNAPSHOT_PATH = Path(os.getenv("SNAPSHOT_PATH", "data/snapshots.parquet"))
VEHICLE_POSITIONS_PATH = Path(os.getenv("VEHICLE_POSITIONS_PATH", "data/vehicle_positions.parquet"))

SCHEMA = pa.schema([
    ("timestamp", pa.timestamp("us", tz="UTC")),
    ("vehicles", pa.int64()),
    ("alerts", pa.int64()),
    ("routes", pa.int64()),
    ("health", pa.string()),
    ("alert_effects", pa.string()),
    ("impacted_routes", pa.string()),
    ("fleet_composition", pa.string()),
    ("activity_status", pa.string()),
    ("routes_status", pa.string()),
])


def _row_to_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    snapshot = {
        "timestamp": row["timestamp"],
        "vehicles": row["vehicles"],
        "alerts": row["alerts"],
        "routes": row["routes"],
        "health": row["health"],
    }
    for col in JSON_COLUMNS:
        snapshot[col] = json.loads(row[col]) if row[col] is not None else None
    return snapshot


def append_snapshot(snapshot: dict[str, Any]) -> None:
    try:
        row = SnapshotRow.model_validate(snapshot).to_parquet_row()
    except (ValidationError, ValueError) as e:
        log.warning(
            "Dropping snapshot row: %s | payload_keys=%s",
            e,
            sorted(snapshot.keys()),
        )
        return

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    new_table = pa.Table.from_pylist([row], schema=SCHEMA)

    if SNAPSHOT_PATH.exists():
        existing = pq.read_table(SNAPSHOT_PATH, schema=SCHEMA)
        combined = pa.concat_tables([existing, new_table])
    else:
        combined = new_table

    tmp_path = SNAPSHOT_PATH.with_suffix(SNAPSHOT_PATH.suffix + ".tmp")
    pq.write_table(combined, tmp_path, compression="zstd")
    os.replace(tmp_path, SNAPSHOT_PATH)


def latest_snapshot() -> dict[str, Any] | None:
    if not SNAPSHOT_PATH.exists():
        return None
    table = pq.read_table(SNAPSHOT_PATH, schema=SCHEMA)
    if table.num_rows == 0:
        return None
    # Pull just the last row to avoid materializing the whole table.
    last_row = table.slice(table.num_rows - 1, 1).to_pylist()[0]
    return _row_to_snapshot(last_row)


VEHICLE_POSITIONS_SCHEMA = pa.schema([
    ("timestamp", pa.timestamp("us", tz="UTC")),
    ("vehicle_id", pa.string()),
    ("route_id", pa.string()),
    ("latitude", pa.float64()),
    ("longitude", pa.float64()),
    ("current_status", pa.string()),
])


def append_vehicle_positions(positions: list[dict[str, Any]], timestamp: datetime) -> None:
    if not positions:
        return

    rows: list[dict[str, Any]] = []
    for idx, p in enumerate(positions):
        try:
            vp = VehiclePositionRow.model_validate({**p, "timestamp": timestamp})
        except (ValidationError, ValueError) as e:
            log.warning(
                "Dropping vehicle position idx=%d vehicle_id=%r: %s",
                idx,
                p.get("vehicle_id"),
                e,
            )
            continue
        rows.append(
            {
                "timestamp": vp.timestamp,
                "vehicle_id": vp.vehicle_id,
                "route_id": vp.route_id,
                "latitude": vp.latitude,
                "longitude": vp.longitude,
                "current_status": vp.current_status,
            }
        )

    if not rows:
        log.warning(
            "All %d vehicle positions dropped; skipping parquet write",
            len(positions),
        )
        return

    VEHICLE_POSITIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    new_table = pa.Table.from_pylist(rows, schema=VEHICLE_POSITIONS_SCHEMA)

    if VEHICLE_POSITIONS_PATH.exists():
        existing = pq.read_table(VEHICLE_POSITIONS_PATH, schema=VEHICLE_POSITIONS_SCHEMA)
        combined = pa.concat_tables([existing, new_table])
    else:
        combined = new_table

    tmp_path = VEHICLE_POSITIONS_PATH.with_suffix(VEHICLE_POSITIONS_PATH.suffix + ".tmp")
    pq.write_table(combined, tmp_path, compression="zstd")
    os.replace(tmp_path, VEHICLE_POSITIONS_PATH)


def history(since: datetime, limit: int = 1000) -> list[dict[str, Any]]:
    if not SNAPSHOT_PATH.exists():
        return []
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)

    table = pq.read_table(
        SNAPSHOT_PATH,
        columns=["timestamp", "vehicles", "alerts", "routes", "health"],
    )
    mask = pc.greater_equal(table["timestamp"], pa.scalar(since, type=pa.timestamp("us", tz="UTC")))
    filtered = table.filter(mask)
    if filtered.num_rows > limit:
        filtered = filtered.slice(filtered.num_rows - limit, limit)
    return filtered.to_pylist()
