import logging
import os
from typing import Any

import httpx

log = logging.getLogger(__name__)

BASE_URL = os.getenv("API_URL", "https://api-v3.mbta.com")

_shapes_by_route: dict[str, list[dict[str, Any]]] = {}
_stops_by_id: dict[str, dict[str, Any]] = {}
_warmed = False


async def warm() -> None:
    global _warmed
    if _warmed:
        return

    async with httpx.AsyncClient(timeout=60.0) as client:
        shapes_resp, stops_resp = await _gather(
            client.get(f"{BASE_URL}/shapes"),
            client.get(f"{BASE_URL}/stops"),
        )

    for shape in shapes_resp.json().get("data", []):
        polyline = shape.get("attributes", {}).get("polyline")
        if not polyline:
            continue
        route_rel = shape.get("relationships", {}).get("route", {}).get("data") or {}
        route_id = route_rel.get("id")
        if not route_id:
            continue
        _shapes_by_route.setdefault(route_id, []).append({
            "shape_id": shape.get("id"),
            "polyline": polyline,
        })

    for stop in stops_resp.json().get("data", []):
        sid = stop.get("id")
        attrs = stop.get("attributes", {}) or {}
        lat = attrs.get("latitude")
        lon = attrs.get("longitude")
        if sid is None or lat is None or lon is None:
            continue
        _stops_by_id[sid] = {
            "name": attrs.get("name"),
            "latitude": lat,
            "longitude": lon,
        }

    _warmed = True
    log.info(
        "static cache warmed: %d route shapes, %d stops",
        sum(len(v) for v in _shapes_by_route.values()),
        len(_stops_by_id),
    )


async def _gather(*coros):
    import asyncio
    return await asyncio.gather(*coros)


def shapes_by_route() -> dict[str, list[dict[str, Any]]]:
    return _shapes_by_route


def get_stop(stop_id: str) -> dict[str, Any] | None:
    return _stops_by_id.get(stop_id)
