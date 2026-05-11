import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query

from controllers import static_data, storage

MBTA_BASE_URL = os.getenv("API_URL", "https://api-v3.mbta.com")

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _require_latest() -> dict:
    snapshot = storage.latest_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=503, detail="No snapshot available yet")
    return snapshot


def _series_from_dict(d: dict[str, int]) -> dict[str, list]:
    return {"labels": list(d.keys()), "data": list(d.values())}


@router.get("/kpis")
async def get_kpis():
    s = _require_latest()
    return {
        "vehicles": s["vehicles"],
        "alerts": s["alerts"],
        "routes": s["routes"],
        "health": s["health"],
    }


@router.get("/charts")
async def get_charts():
    s = _require_latest()
    impacted = s["impacted_routes"] or {}
    top_impacted = dict(sorted(impacted.items(), key=lambda kv: kv[1], reverse=True)[:5])
    return {
        "alert_effects": _series_from_dict(s["alert_effects"] or {}),
        "impacted_routes": _series_from_dict(top_impacted),
        "fleet_composition": _series_from_dict(s["fleet_composition"] or {}),
        "activity_status": _series_from_dict(s["activity_status"] or {}),
    }


@router.get("/routes")
async def get_routes():
    s = _require_latest()
    return s["routes_status"] or []


@router.get("/history")
async def get_history(
    since: datetime | None = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=10000),
):
    if since is None:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
    rows = storage.history(since=since, limit=limit)

    def health_pct(h: str) -> float:
        try:
            return float(h.rstrip("%"))
        except (AttributeError, ValueError):
            return 0.0

    return [
        {
            "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
            "vehicles": row["vehicles"],
            "alerts": row["alerts"],
            "routes": row["routes"],
            "health_pct": health_pct(row["health"]),
        }
        for row in rows
    ]


@router.get("/shapes")
async def get_shapes():
    s = _require_latest()
    routes_status = s["routes_status"] or []
    severity_by_route = {r["id"]: r.get("max_severity", 0) for r in routes_status}
    color_by_route = {r["id"]: r.get("color") for r in routes_status}

    out: list[dict[str, Any]] = []
    for route_id, shapes in static_data.shapes_by_route().items():
        if not shapes:
            continue
        for shape in shapes:
            out.append({
                "route_id": route_id,
                "shape_id": shape["shape_id"],
                "polyline": shape["polyline"],
                "color": color_by_route.get(route_id),
                "max_severity": severity_by_route.get(route_id, 0),
            })
    return out


@router.get("/alert-stops")
async def get_alert_stops():
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(f"{MBTA_BASE_URL}/alerts?filter[lifecycle]=ONGOING")
    alerts = resp.json().get("data", [])

    stop_summary: dict[str, dict[str, Any]] = {}
    for alert in alerts:
        attrs = alert.get("attributes", {}) or {}
        severity = attrs.get("severity", 0) or 0
        entities = attrs.get("informed_entity") or []
        for entity in entities:
            stop_id = entity.get("stop")
            if not stop_id:
                continue
            entry = stop_summary.setdefault(stop_id, {
                "stop_id": stop_id,
                "alert_count": 0,
                "max_severity": 0,
            })
            entry["alert_count"] += 1
            if severity > entry["max_severity"]:
                entry["max_severity"] = severity

    out: list[dict[str, Any]] = []
    for stop_id, entry in stop_summary.items():
        stop = static_data.get_stop(stop_id)
        if stop is None:
            continue
        out.append({
            **entry,
            "name": stop["name"],
            "latitude": stop["latitude"],
            "longitude": stop["longitude"],
        })
    return out
