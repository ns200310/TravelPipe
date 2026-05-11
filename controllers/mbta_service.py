import httpx
import asyncio
from typing import Dict, List, Any
import os

BASE_URL = os.getenv("API_URL", "https://api-v3.mbta.com")

class MBTAService:
    async def fetch_raw_data(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            tasks = [
                client.get(f"{BASE_URL}/routes"),
                client.get(f"{BASE_URL}/alerts?filter[lifecycle]=ONGOING"),
                client.get(f"{BASE_URL}/vehicles?include=route")
            ]
            responses = await asyncio.gather(*tasks)
            
            return {
                "routes": responses[0].json().get("data", []),
                "alerts": responses[1].json().get("data", []),
                "vehicles": responses[2].json().get("data", [])
            }

    async def get_kpis(self) -> Dict[str, Any]:
        data = await self.fetch_raw_data()
        num_vehicles = len(data["vehicles"])
        num_alerts = len(data["alerts"])
        num_routes = len(data["routes"])
        
        health = max(0, 100 - (num_alerts / (num_routes if num_routes > 0 else 1) * 100))
        
        return {
            "vehicles": num_vehicles,
            "alerts": num_alerts,
            "routes": num_routes,
            "health": f"{health:.1f}%"
        }

    async def get_chart_data(self) -> Dict[str, Any]:
        data = await self.fetch_raw_data()
        
        # 1. Alert Distribution
        effect_counts = {}
        for alert in data["alerts"]:
            effect = alert.get("attributes", {}).get("effect") or "UNKNOWN"
            effect_counts[effect] = effect_counts.get(effect, 0) + 1
            
        # 2. Impacted Routes
        route_impact = {}
        for alert in data["alerts"]:
            entities = alert.get("attributes", {}).get("informed_entity") or []
            for entity in entities:
                route_id = entity.get("route")
                if route_id:
                    route_impact[route_id] = route_impact.get(route_id, 0) + 1
        
        top_impacted = sorted(route_impact.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 3. Fleet Modal Breakdown
        modal_counts = {"Subway": 0, "Rail": 0, "Bus": 0, "Ferry": 0}
        for vehicle in data["vehicles"]:
            route_data = vehicle.get("relationships", {}).get("route", {}).get("data")
            route_id = route_data.get("id") if route_data else ""
            
            if "CR-" in route_id:
                modal_counts["Rail"] += 1
            elif any(c in route_id for c in ["Red", "Orange", "Blue", "Green"]):
                modal_counts["Subway"] += 1
            elif route_id == "Ferry":
                modal_counts["Ferry"] += 1
            else:
                modal_counts["Bus"] += 1
                
        # 4. Vehicle Activity Status
        status_counts = {}
        for vehicle in data["vehicles"]:
            status = vehicle.get("attributes", {}).get("current_status") or "IDLE"
            status = status.replace("_", " ")
            status_counts[status] = status_counts.get(status, 0) + 1
            
        return {
            "alert_effects": {
                "labels": list(effect_counts.keys()),
                "data": list(effect_counts.values())
            },
            "impacted_routes": {
                "labels": [r[0] for r in top_impacted],
                "data": [r[1] for r in top_impacted]
            },
            "fleet_composition": {
                "labels": list(modal_counts.keys()),
                "data": list(modal_counts.values())
            },
            "activity_status": {
                "labels": list(status_counts.keys()),
                "data": list(status_counts.values())
            }
        }

    async def get_routes_status(self) -> List[Dict[str, Any]]:
        data = await self.fetch_raw_data()
        
        route_alert_map = {}
        for alert in data["alerts"]:
            entities = alert.get("attributes", {}).get("informed_entity") or []
            for entity in entities:
                route_id = entity.get("route")
                if route_id:
                    if route_id not in route_alert_map:
                        route_alert_map[route_id] = []
                    route_alert_map[route_id].append(alert.get("attributes", {}).get("severity", 0))
                    
        results = []
        for route in data["routes"]:
            r_id = route["id"]
            alerts = route_alert_map.get(r_id, [])
            max_severity = max(alerts) if alerts else 0
            
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
                "alert_count": len(alerts),
                "max_severity": max_severity,
                "status_text": status_text,
                "status_class": status_class,
                "modality": self.get_route_type_name(route["attributes"].get("type"))
            })
            
        # Sort by alert count descending
        results.sort(key=lambda x: x["alert_count"], reverse=True)
        return results

    def get_route_type_name(self, route_type: int) -> str:
        types = ["Subway", "Subway", "Commuter Rail", "Bus", "Ferry"]
        try:
            return types[route_type]
        except (IndexError, TypeError):
            return "Transit"

mbta_service = MBTAService()
