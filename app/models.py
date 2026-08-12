from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MetricType(str, Enum):
    BLOOD_PRESSURE = "blood_pressure"
    GLUCOSE = "glucose"
    WEIGHT = "weight"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Reading(BaseModel):
    metric: MetricType
    value_display: str
    value_numeric: Optional[float] = None
    unit: str
    timestamp_iso: str
    device_id: str


class PatientSnapshot(BaseModel):
    id: str
    name: str
    age: int
    conditions: list[str]
    latest_readings: list[Reading]
    pathway_flags: list[str] = Field(default_factory=list)
    status: str


class EscalationItem(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    priority: Priority
    rule_id: str
    rule_label: str
    recommended_action: str
    detail: str
    created_iso: str


class DashboardState(BaseModel):
    patients: list[PatientSnapshot]
    escalation_queue: list[EscalationItem]
    server_time_iso: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
