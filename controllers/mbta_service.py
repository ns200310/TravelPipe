import asyncio
import os
from datetime import datetime, timezone
from typing import Any

import httpx

BASE_URL = os.getenv("API_URL", "https://api-v3.mbta.com")


class MBTAService:
    async def fetch_raw_data(self) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            tasks = [
                client.get(f"{BASE_URL}/routes"),
                client.get(f"{BASE_URL}/alerts?filter[lifecycle]=ONGOING"),
                client.get(f"{BASE_URL}/vehicles?include=route"),
            ]
            responses = await asyncio.gather(*tasks)
            return {
                "routes": responses[0].json().get("data", []),
                "alerts": responses[1].json().get("data", []),
                "vehicles": responses[2].json().get("data", []),
            }

    async def compute_snapshot(self) -> dict[str, Any]:
        data = await self.fetch_raw_data()
        return {
            "timestamp": datetime.now(timezone.utc),
            **self._kpis(data),
            "alert_effects": self._alert_effects(data),
            "impacted_routes": self._impacted_routes(data),
            "fleet_composition": self._fleet_composition(data),
            "activity_status": self._activity_status(data),
            "routes_status": self._routes_status(data),
            "vehicle_positions": self._vehicle_positions(data),
        }

    def _vehicle_positions(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        positions: list[dict[str, Any]] = []
        for vehicle in data["vehicles"]:
            attrs = vehicle.get("attributes", {}) or {}
            lat = attrs.get("latitude")
            lon = attrs.get("longitude")
            if lat is None or lon is None:
                continue
            route_data = vehicle.get("relationships", {}).get("route", {}).get("data")
            route_id = route_data.get("id") if route_data else None
            positions.append({
                "vehicle_id": vehicle.get("id"),
                "route_id": route_id,
                "latitude": lat,
                "longitude": lon,
                "current_status": attrs.get("current_status"),
            })
        return positions

    def _kpis(self, data: dict[str, Any]) -> dict[str, Any]:
        num_vehicles = len(data["vehicles"])
        num_alerts = len(data["alerts"])
        num_routes = len(data["routes"])
        health = max(0, 100 - (num_alerts / (num_routes if num_routes > 0 else 1) * 100))
        return {
            "vehicles": num_vehicles,
            "alerts": num_alerts,
            "routes": num_routes,
            "health": f"{health:.1f}%",
        }

    def _alert_effects(self, data: dict[str, Any]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for alert in data["alerts"]:
            effect = alert.get("attributes", {}).get("effect") or "UNKNOWN"
            counts[effect] = counts.get(effect, 0) + 1
        return counts

    def _impacted_routes(self, data: dict[str, Any]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for alert in data["alerts"]:
            entities = alert.get("attributes", {}).get("informed_entity") or []
            for entity in entities:
                route_id = entity.get("route")
                if route_id:
                    counts[route_id] = counts.get(route_id, 0) + 1
        return counts

    def _fleet_composition(self, data: dict[str, Any]) -> dict[str, int]:
        modal = {"Subway": 0, "Rail": 0, "Bus": 0, "Ferry": 0}
        for vehicle in data["vehicles"]:
            route_data = vehicle.get("relationships", {}).get("route", {}).get("data")
            route_id = route_data.get("id") if route_data else ""

            if "CR-" in route_id:
                modal["Rail"] += 1
            elif any(c in route_id for c in ["Red", "Orange", "Blue", "Green"]):
                modal["Subway"] += 1
            elif route_id == "Ferry":
                modal["Ferry"] += 1
            else:
                modal["Bus"] += 1
        return modal

    def _activity_status(self, data: dict[str, Any]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for vehicle in data["vehicles"]:
            status = vehicle.get("attributes", {}).get("current_status") or "IDLE"
            status = status.replace("_", " ")
            counts[status] = counts.get(status, 0) + 1
        return counts

    def _routes_status(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        route_alert_map: dict[str, list[int]] = {}
        for alert in data["alerts"]:
            entities = alert.get("attributes", {}).get("informed_entity") or []
            for entity in entities:
                route_id = entity.get("route")
                if route_id:
                    route_alert_map.setdefault(route_id, []).append(
                        alert.get("attributes", {}).get("severity", 0)
                    )

        results = []
        for route in data["routes"]:
            r_id = route["id"]
            severities = route_alert_map.get(r_id, [])
            max_severity = max(severities) if severities else 0

            status_text = "Operations Stable"
            status_class = "stable"
            if max_severity >= 7:
                status_text = "Severe Disruption"
                status_class = "severe"
            elif max_severity > 0:
                status_text = "Minor Service Alert"
                status_class = "minor"

            results.append({
                "id": r_id,
                "long_name": route["attributes"].get("long_name"),
                "color": route["attributes"].get("color"),
                "type": route["attributes"].get("type"),
                "alert_count": len(severities),
                "max_severity": max_severity,
                "status_text": status_text,
                "status_class": status_class,
                "modality": self._route_type_name(route["attributes"].get("type")),
            })

        results.sort(key=lambda x: x["alert_count"], reverse=True)
        return results

    def _route_type_name(self, route_type: int | None) -> str:
        types = ["Subway", "Subway", "Commuter Rail", "Bus", "Ferry"]
        try:
            return types[route_type]
        except (IndexError, TypeError):
            return "Transit"


mbta_service = MBTAService()
