from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app.models import MetricType, Reading


@dataclass
class PatientProfile:
    id: str
    name: str
    age: int
    conditions: list[str]
    bp_trend: float = 0.0
    glucose_trend: float = 0.0
    weight_trend: float = 0.0
    skip_bp: bool = False
    skip_glucose: bool = False
    history: dict[str, list[Reading]] = field(default_factory=dict)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RPMSimulator:
  """Simulates remote monitoring streams for four chronic-care patients."""

  def __init__(self) -> None:
    self._tick = 0
    self._profiles: list[PatientProfile] = [
      PatientProfile(
        "p-101",
        "Maria Santos",
        67,
        ["Type 2 diabetes", "Hypertension"],
        bp_trend=1.8,
        glucose_trend=4.5,
      ),
      PatientProfile(
        "p-102",
        "James Okonkwo",
        54,
        ["Heart failure", "CKD stage 3"],
        bp_trend=-0.5,
        weight_trend=0.35,
      ),
      PatientProfile(
        "p-103",
        "Elena Vasquez",
        72,
        ["COPD", "Prediabetes"],
        glucose_trend=2.2,
        skip_glucose=True,
      ),
      PatientProfile(
        "p-104",
        "Robert Chen",
        61,
        ["Obesity", "Hypertension"],
        bp_trend=2.5,
        weight_trend=0.5,
        skip_bp=True,
      ),
    ]
    self._seed_history()

  def _seed_history(self) -> None:
    now = _now()
    for profile in self._profiles:
      for metric in MetricType:
        readings: list[Reading] = []
        for hours_ago in range(72, 0, -6):
          ts = now - timedelta(hours=hours_ago)
          readings.append(self._synthetic_reading(profile, metric, ts))
        profile.history[metric.value] = readings

  def _synthetic_reading(
    self, profile: PatientProfile, metric: MetricType, ts: datetime
  ) -> Reading:
    jitter = random.uniform(-0.8, 0.8)
    if metric == MetricType.BLOOD_PRESSURE:
      base_sys = 128 + profile.bp_trend * 3 + jitter * 4
      base_dia = 78 + profile.bp_trend * 1.5
      return Reading(
        metric=metric,
        value_display=f"{int(base_sys)}/{int(base_dia)}",
        value_numeric=base_sys,
        unit="mmHg",
        timestamp_iso=ts.isoformat(),
        device_id=f"bp-{profile.id}",
      )
    if metric == MetricType.GLUCOSE:
      base = 118 + profile.glucose_trend * 2.5 + jitter * 8
      return Reading(
        metric=metric,
        value_display=f"{int(base)}",
        value_numeric=base,
        unit="mg/dL",
        timestamp_iso=ts.isoformat(),
        device_id=f"glu-{profile.id}",
      )
    base_wt = 198 + profile.weight_trend * 4 + jitter * 0.6
    return Reading(
      metric=metric,
      value_display=f"{base_wt:.1f}",
      value_numeric=base_wt,
      unit="lb",
      timestamp_iso=ts.isoformat(),
      device_id=f"wt-{profile.id}",
    )

  def tick(self) -> None:
    self._tick += 1
    now = _now()
    for profile in self._profiles:
      if self._tick % 3 == 0 and profile.id == "p-103":
        profile.skip_glucose = not profile.skip_glucose
      if self._tick % 4 == 0 and profile.id == "p-104":
        profile.skip_bp = not profile.skip_bp

      for metric in MetricType:
        if metric == MetricType.BLOOD_PRESSURE and profile.skip_bp:
          continue
        if metric == MetricType.GLUCOSE and profile.skip_glucose:
          continue
        reading = self._synthetic_reading(profile, metric, now)
        bucket = profile.history.setdefault(metric.value, [])
        bucket.append(reading)
        profile.history[metric.value] = bucket[-24:]

  def profiles(self) -> list[PatientProfile]:
    return self._profiles

  def history(self, patient_id: str, metric: MetricType) -> list[Reading]:
    for profile in self._profiles:
      if profile.id == patient_id:
        return list(profile.history.get(metric.value, []))
    return []
