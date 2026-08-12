# RPM Escalation Hub

**Project 8 of 10** in the healthcare portfolio series - remote patient monitoring with care-pathway escalation.

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green) ![License](https://img.shields.io/badge/License-MIT-lightgrey)

## What it does

- Simulates **4 RPM patients** with home BP, glucose, and weight device streams
- Evaluates **care-pathway rules**: trending worsening, missed readings, critical thresholds
- Builds a **nurse escalation queue** with priority (critical / high / medium) and recommended actions
- **Live dashboard** via WebSocket (3s refresh)

> **Demo only** - synthetic data, simplified pathways, not for clinical use.

## Quick start (Windows)

```powershell
cd C:\Users\brive\Projects\rpm-escalation-hub
.\run.ps1
```

Open **http://127.0.0.1:8097**

## API

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard UI |
| `GET /api/health` | Health check |
| `GET /api/dashboard` | Snapshot JSON |
| `GET /api/patients/{id}/history/{metric}` | Reading history |
| `WS /ws/rpm` | Live dashboard stream |

## Project structure

```
app/
 main.py FastAPI + WebSocket
 simulator.py RPM patient streams
 pathways.py Care-pathway rules + queue
 models.py Pydantic models
static/ Dashboard UI
```

See **[PORTFOLIO.md](./PORTFOLIO.md)** for interview talking points.

## License

MIT - see [LICENSE](./LICENSE)
