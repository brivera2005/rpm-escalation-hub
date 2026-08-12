# RPM Escalation Hub - Portfolio brief (8/10)

## Elevator pitch

Remote patient monitoring demo that streams home BP, glucose, and weight readings for four chronic-care patients, evaluates **care-pathway rules** (trending worsening, missed transmissions - not just static thresholds), and surfaces a prioritized nurse escalation queue with recommended actions.

## Skills demonstrated

- **Backend:** Python, FastAPI, Pydantic, WebSockets, rule engine
- **Frontend:** Live RPM dashboard, escalation queue UX
- **Domain:** Chronic care pathways, RPM adherence, nurse triage workflows
- **Engineering:** Simulator + pathway evaluator + API separation

## Interview line

*"I built an RPM escalation hub that goes beyond alert thresholds - it detects worsening trends and missed device uploads, then routes prioritized nurse actions like you'd see in a real chronic-care program."*

## Run locally in 30 seconds

```powershell
.\run.ps1
# → http://127.0.0.1:8097
```

## Disclaimer

Synthetic patients only. Rules are educational simplifications. Not for clinical use.
