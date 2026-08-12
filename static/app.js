const liveStatus = document.getElementById("liveStatus");
const serverTime = document.getElementById("serverTime");
const patientGrid = document.getElementById("patientGrid");
const queueList = document.getElementById("queueList");

function setLive(online) {
 liveStatus.classList.toggle("offline", !online);
 liveStatus.innerHTML = online
 ? '<span class="pulse-dot"></span>Live · WebSocket'
 : '<span class="pulse-dot"></span>Reconnecting…';
}

function render(data) {
 serverTime.textContent = new Date(data.server_time_iso).toLocaleTimeString();

 const q = data.escalation_queue || [];
 document.getElementById("statPatients").textContent = data.patients.length;
 document.getElementById("statCritical").textContent = q.filter((e) => e.priority === "critical").length;
 document.getElementById("statHigh").textContent = q.filter((e) => e.priority === "high").length;
 document.getElementById("statMedium").textContent = q.filter((e) => e.priority === "medium").length;

 patientGrid.innerHTML = data.patients
 .map(
 (p) => `
 <article class="patient-card ${p.status}">
 <div class="patient-name">${p.name}</div>
 <div class="patient-meta">Age ${p.age} · ${p.conditions.join(", ")}</div>
 <div class="readings">
 ${p.latest_readings
 .map((r) => `<span class="chip">${r.metric.replace("_", " ")}: ${r.value_display} ${r.unit}</span>`)
 .join("")}
 </div>
 ${p.pathway_flags.length ? `<div class="flags">${p.pathway_flags.join(" · ")}</div>` : ""}
 </article>`
 )
 .join("");

 queueList.innerHTML = q.length
 ? q
 .map(
 (e) => `
 <div class="queue-item ${e.priority}">
 <div class="queue-head">
 <span class="queue-rule">${e.rule_label}</span>
 <span class="priority-badge">${e.priority}</span>
 </div>
 <div class="queue-detail">${e.patient_name} - ${e.detail}</div>
 <div class="queue-action">→ ${e.recommended_action}</div>
 </div>`
 )
 .join("")
 : '<p class="queue-detail">No escalations - all pathways within range.</p>';
}

function connect() {
 const proto = location.protocol === "https:" ? "wss" : "ws";
 const ws = new WebSocket(`${proto}://${location.host}/ws/rpm`);

 ws.onopen = () => setLive(true);
 ws.onclose = () => {
 setLive(false);
 setTimeout(connect, 2000);
 };
 ws.onmessage = (ev) => render(JSON.parse(ev.data));
}

connect();
