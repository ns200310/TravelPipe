import asyncio
import logging
import os

from controllers.mbta_service import mbta_service
from controllers.tasks import append_snapshot_task, append_vehicle_positions_task

log = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))


async def _poll_once() -> None:
    try:
        snapshot = await mbta_service.compute_snapshot()
        positions = snapshot.pop("vehicle_positions", [])
        timestamp_iso = snapshot["timestamp"].isoformat()
        payload = {**snapshot, "timestamp": timestamp_iso}
        append_snapshot_task.delay(payload)
        append_vehicle_positions_task.delay(positions, timestamp_iso)
        log.info(
            "Snapshot enqueued: vehicles=%s alerts=%s routes=%s positions=%s",
            snapshot["vehicles"],
            snapshot["alerts"],
            snapshot["routes"],
            len(positions),
        )
    except Exception:
        log.exception("Failed to poll MBTA / enqueue snapshot")


async def run_poller() -> None:
    await _poll_once()
    while True:
        try:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            log.info("Poller cancelled")
            raise
        await _poll_once()
