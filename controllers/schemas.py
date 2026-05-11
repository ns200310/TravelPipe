import json
import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_JSON_BYTES = 1 * 1024 * 1024
MAX_STRING_CHARS = 64
HEALTH_RE = re.compile(r"^\d{1,3}(?:\.\d+)?%$")

JSON_COLUMNS = (
    "alert_effects",
    "impacted_routes",
    "fleet_composition",
    "activity_status",
    "routes_status",
)


def _require_tz_aware(v: datetime) -> datetime:
    if v.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return v


class SnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    timestamp: datetime
    vehicles: int = Field(ge=0)
    alerts: int = Field(ge=0)
    routes: int = Field(ge=0)
    health: str

    alert_effects: dict | list
    impacted_routes: dict | list
    fleet_composition: dict | list
    activity_status: dict | list
    routes_status: dict | list

    @field_validator("timestamp")
    @classmethod
    def _tz_aware(cls, v: datetime) -> datetime:
        return _require_tz_aware(v)

    @field_validator("health")
    @classmethod
    def _health_fmt(cls, v: str) -> str:
        if not HEALTH_RE.match(v):
            raise ValueError(f"health must match 'NN.N%' format (got {v!r})")
        pct = float(v.rstrip("%"))
        if not 0.0 <= pct <= 100.0:
            raise ValueError(f"health {pct} out of [0, 100]")
        return v

    def to_parquet_row(self) -> dict[str, Any]:
        row: dict[str, Any] = {
            "timestamp": self.timestamp,
            "vehicles": self.vehicles,
            "alerts": self.alerts,
            "routes": self.routes,
            "health": self.health,
        }
        for col in JSON_COLUMNS:
            payload = json.dumps(getattr(self, col), separators=(",", ":"))
            size = len(payload.encode("utf-8"))
            if size > MAX_JSON_BYTES:
                raise ValueError(
                    f"{col} serialised size {size} > {MAX_JSON_BYTES} bytes"
                )
            row[col] = payload
        return row


class VehiclePositionRow(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    timestamp: datetime
    vehicle_id: str = Field(min_length=1, max_length=MAX_STRING_CHARS)
    route_id: str = Field(min_length=1, max_length=MAX_STRING_CHARS)
    current_status: str | None = Field(default=None, max_length=MAX_STRING_CHARS)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)

    @field_validator("timestamp")
    @classmethod
    def _tz_aware(cls, v: datetime) -> datetime:
        return _require_tz_aware(v)
