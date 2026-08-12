from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import DashboardState, MetricType
from app.pathways import build_dashboard
from app.simulator import RPMSimulator

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

app = FastAPI(
  title="RPM Escalation Hub",
  description="Remote patient monitoring with care-pathway escalation (demo / portfolio).",
  version="1.0.0",
)

simulator = RPMSimulator()


def snapshot() -> DashboardState:
  patients, queue = build_dashboard(simulator)
  return DashboardState(
    patients=patients,
    escalation_queue=queue,
    server_time_iso=datetime.now(timezone.utc).isoformat(),
  )


@app.get("/api/health")
def health():
  return {"status": "ok", "patients": len(simulator.profiles())}


@app.get("/api/dashboard", response_model=DashboardState)
def get_dashboard():
  return snapshot()


@app.get("/api/patients/{patient_id}/history/{metric}")
def patient_history(patient_id: str, metric: MetricType):
  history = simulator.history(patient_id, metric)
  if not history:
    raise HTTPException(status_code=404, detail="No history for patient/metric")
  return {"patient_id": patient_id, "metric": metric, "readings": history}


@app.websocket("/ws/rpm")
async def rpm_stream(websocket: WebSocket):
  await websocket.accept()
  try:
    while True:
      simulator.tick()
      await websocket.send_json(snapshot().model_dump(mode="json"))
      await asyncio.sleep(3)
  except WebSocketDisconnect:
    return


@app.get("/")
def index():
  return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
