import asyncio
import logging
import os

from controllers import storage
from controllers.mbta_service import mbta_service

log = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))


async def _poll_once() -> None:
    try:
        snapshot = await mbta_service.compute_snapshot()
        positions = snapshot.pop("vehicle_positions", [])
        storage.append_snapshot(snapshot)
        storage.append_vehicle_positions(positions, snapshot["timestamp"])
        log.info(
            "Snapshot stored: vehicles=%s alerts=%s routes=%s positions=%s",
            snapshot["vehicles"],
            snapshot["alerts"],
            snapshot["routes"],
            len(positions),
        )
    except Exception:
        log.exception("Failed to poll MBTA / write snapshot")


async def run_poller() -> None:
    await _poll_once()
    while True:
        try:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            log.info("Poller cancelled")
            raise
        await _poll_once()
