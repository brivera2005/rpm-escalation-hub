from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.models import EscalationItem, MetricType, PatientSnapshot, Priority, Reading
from app.simulator import PatientProfile, RPMSimulator


@dataclass(frozen=True)
class PathwayRule:
  id: str
  label: str
  priority: Priority
  recommended_action: str


RULES = {
  "trend_bp_worsening": PathwayRule(
    "trend_bp_worsening",
    "BP trending upward (3 readings)",
    Priority.HIGH,
    "Nurse outreach within 4h; review antihypertensive adherence and home cuff technique.",
  ),
  "trend_glucose_worsening": PathwayRule(
    "trend_glucose_worsening",
    "Glucose trending upward (3 readings)",
    Priority.HIGH,
    "Schedule telehealth med review; reinforce carb logging and medication timing.",
  ),
  "trend_weight_gain": PathwayRule(
    "trend_weight_gain",
    "Weight gain >2 lb in 48h (HF pathway)",
    Priority.CRITICAL,
    "Escalate to cardiology RN: assess fluid status, diuretic dose, same-day callback.",
  ),
  "missed_bp": PathwayRule(
    "missed_bp",
    "Missed BP transmission >12h",
    Priority.MEDIUM,
    "Send device reminder SMS; if no upload in 24h, assign care-coordinator call.",
  ),
  "missed_glucose": PathwayRule(
    "missed_glucose",
    "Missed glucose transmission >12h",
    Priority.MEDIUM,
    "Verify glucometer connectivity; coach patient on morning fasting log.",
  ),
  "critical_hypoglycemia": PathwayRule(
    "critical_hypoglycemia",
    "Glucose below 70 mg/dL",
    Priority.CRITICAL,
    "Immediate nurse phone call; confirm symptoms and 15g fast carb protocol.",
  ),
  "critical_hypertension": PathwayRule(
    "critical_hypertension",
    "Systolic BP ≥ 180 mmHg",
    Priority.CRITICAL,
    "Same-day clinician review; assess headache, chest pain, vision changes.",
  ),
}


def _parse_ts(iso: str) -> datetime:
  return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def _hours_since(reading: Reading | None) -> float:
  if not reading:
    return 999.0
  delta = datetime.now(timezone.utc) - _parse_ts(reading.timestamp_iso)
  return delta.total_seconds() / 3600.0


def _trend_worsening(readings: list[Reading], min_delta: float) -> bool:
  nums = [r.value_numeric for r in readings[-3:] if r.value_numeric is not None]
  if len(nums) < 3:
    return False
  return nums[0] < nums[1] < nums[2] and (nums[2] - nums[0]) >= min_delta


def _weight_gain_48h(readings: list[Reading]) -> bool:
  nums = [(r.value_numeric, _parse_ts(r.timestamp_iso)) for r in readings if r.value_numeric]
  if len(nums) < 2:
    return False
  recent = nums[-1][0]
  cutoff = datetime.now(timezone.utc).timestamp() - 48 * 3600
  older = [n for n, ts in nums if ts.timestamp() <= cutoff]
  if not older:
    return False
  return (recent - older[-1]) >= 2.0


def _latest(readings: list[Reading]) -> Reading | None:
  return readings[-1] if readings else None


def evaluate_patient(profile: PatientProfile) -> tuple[PatientSnapshot, list[EscalationItem]]:
  flags: list[str] = []
  escalations: list[EscalationItem] = []
  now_iso = datetime.now(timezone.utc).isoformat()

  bp_hist = profile.history.get(MetricType.BLOOD_PRESSURE.value, [])
  glu_hist = profile.history.get(MetricType.GLUCOSE.value, [])
  wt_hist = profile.history.get(MetricType.WEIGHT.value, [])

  latest_bp = _latest(bp_hist)
  latest_glu = _latest(glu_hist)
  latest_wt = _latest(wt_hist)

  def add(rule_key: str, detail: str) -> None:
    rule = RULES[rule_key]
    flags.append(rule.label)
    escalations.append(
      EscalationItem(
        id=f"{profile.id}-{rule_key}",
        patient_id=profile.id,
        patient_name=profile.name,
        priority=rule.priority,
        rule_id=rule.id,
        rule_label=rule.label,
        recommended_action=rule.recommended_action,
        detail=detail,
        created_iso=now_iso,
      )
    )

  if _trend_worsening(bp_hist, 6):
    add("trend_bp_worsening", f"Last BP readings climbing: {[r.value_display for r in bp_hist[-3:]]}")
  if _trend_worsening(glu_hist, 12):
    add("trend_glucose_worsening", f"Glucose trend: {[r.value_display for r in glu_hist[-3:]]} mg/dL")
  if "Heart failure" in profile.conditions and _weight_gain_48h(wt_hist):
    add("trend_weight_gain", f"Weight rose to {latest_wt.value_display if latest_wt else '?'} lb")

  if _hours_since(latest_bp) > 12:
    add("missed_bp", f"No BP upload in {_hours_since(latest_bp):.0f}h")
  if _hours_since(latest_glu) > 12:
    add("missed_glucose", f"No glucose upload in {_hours_since(latest_glu):.0f}h")

  if latest_glu and latest_glu.value_numeric is not None and latest_glu.value_numeric < 70:
    add("critical_hypoglycemia", f"Reading {latest_glu.value_display} mg/dL at {latest_glu.timestamp_iso}")
  if latest_bp and latest_bp.value_numeric is not None and latest_bp.value_numeric >= 180:
    add("critical_hypertension", f"Reading {latest_bp.value_display} mmHg at {latest_bp.timestamp_iso}")

  latest = [r for r in (latest_bp, latest_glu, latest_wt) if r]
  status = "stable"
  if any(e.priority == Priority.CRITICAL for e in escalations):
    status = "critical"
  elif any(e.priority == Priority.HIGH for e in escalations):
    status = "elevated"
  elif escalations:
    status = "watch"

  snapshot = PatientSnapshot(
    id=profile.id,
    name=profile.name,
    age=profile.age,
    conditions=profile.conditions,
    latest_readings=latest,
    pathway_flags=flags,
    status=status,
  )
  return snapshot, escalations


PRIORITY_ORDER = {
  Priority.CRITICAL: 0,
  Priority.HIGH: 1,
  Priority.MEDIUM: 2,
  Priority.LOW: 3,
}


def build_dashboard(sim: RPMSimulator) -> tuple[list[PatientSnapshot], list[EscalationItem]]:
  patients: list[PatientSnapshot] = []
  queue: list[EscalationItem] = []
  for profile in sim.profiles():
    snap, items = evaluate_patient(profile)
    patients.append(snap)
    queue.extend(items)
  queue.sort(key=lambda e: (PRIORITY_ORDER[e.priority], e.patient_name))
  return patients, queue
