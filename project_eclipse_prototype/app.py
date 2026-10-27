import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Project Eclipse | Autonomous SRE", page_icon="🛡️", layout="wide")

# ---------- Demo data and deterministic incident reasoning ----------
SCENARIOS = {
    "Database connection exhaustion after deployment": {
        "service": "payment-api",
        "severity": "CRITICAL",
        "summary": "Payment failures increased shortly after deployment v1.4.",
        "before": {"error_rate": 27.0, "latency_ms": 4200, "cpu": 82, "memory": 78, "db_connections": 98},
        "after": {"error_rate": 2.0, "latency_ms": 380, "cpu": 44, "memory": 51, "db_connections": 32},
        "logs": [
            ("10:00:00", "INFO", "Deployment v1.4 completed on payment-api."),
            ("10:02:10", "WARN", "Database connection pool usage reached 98%."),
            ("10:03:04", "ERROR", "Database query latency exceeded 4 seconds."),
            ("10:04:18", "ERROR", "Payment request timeout rate increasing."),
            ("10:05:22", "WARN", "External payment provider health check is healthy."),
        ],
        "evidence": [
            ("Database connection pool usage at 98%", "Strongly supports DB connection exhaustion"),
            ("Database latency increased to 4.2 seconds", "Consistent with connection contention"),
            ("Connection-handling change in deployment v1.4", "Links regression to recent deployment"),
            ("External payment provider health check is healthy", "Weakens external-provider-failure hypothesis"),
        ],
        "hypotheses": [
            {"name": "Database connection exhaustion", "score": 92, "reason": "Pool saturation and DB latency rise together; the recent deployment changed connection handling."},
            {"name": "Faulty application deployment", "score": 76, "reason": "The incident began after v1.4. This may be the trigger for the connection-pool regression."},
            {"name": "External payment provider failure", "score": 12, "reason": "Provider health check is healthy, so current evidence does not support this hypothesis."},
        ],
        "action": "Rollback payment-api to the previous stable release (simulated)",
        "risk": "Medium — rollback may briefly interrupt in-flight requests. Human approval is required.",
    },
    "High CPU after traffic spike": {
        "service": "catalog-api",
        "severity": "HIGH",
        "summary": "Request volume spike coincides with elevated CPU and response latency.",
        "before": {"error_rate": 11.0, "latency_ms": 1800, "cpu": 97, "memory": 68, "db_connections": 45},
        "after": {"error_rate": 2.5, "latency_ms": 520, "cpu": 58, "memory": 66, "db_connections": 43},
        "logs": [
            ("10:00:00", "INFO", "Incoming request rate increased 3.8x."),
            ("10:01:12", "WARN", "CPU utilization reached 97%."),
            ("10:02:40", "ERROR", "Catalog API p95 latency exceeded 1.8 seconds."),
            ("10:03:05", "WARN", "Memory and DB connection usage remain within normal bounds."),
        ],
        "evidence": [
            ("CPU utilization reached 97%", "Strongly supports compute saturation"),
            ("Request volume increased 3.8x", "Correlates with the CPU spike"),
            ("Memory and DB connection usage are normal", "Weakens memory or DB exhaustion hypotheses"),
        ],
        "hypotheses": [
            {"name": "Traffic-driven CPU saturation", "score": 94, "reason": "A 3.8x request spike coincides with 97% CPU and high latency."},
            {"name": "Memory exhaustion", "score": 18, "reason": "Memory usage is not elevated in the supplied telemetry."},
            {"name": "Database connection exhaustion", "score": 14, "reason": "Connection usage remains within the normal range."},
        ],
        "action": "Scale catalog-api replicas from 2 to 4 (simulated)",
        "risk": "Low–Medium — additional replicas consume more resources; human approval is required.",
    },
    "External API timeout": {
        "service": "orders-api",
        "severity": "HIGH",
        "summary": "Orders API timeouts correlate with an unhealthy external dependency.",
        "before": {"error_rate": 19.0, "latency_ms": 3100, "cpu": 49, "memory": 54, "db_connections": 28},
        "after": {"error_rate": 4.0, "latency_ms": 650, "cpu": 47, "memory": 54, "db_connections": 29},
        "logs": [
            ("10:00:00", "INFO", "Orders API service health is normal."),
            ("10:01:30", "WARN", "External inventory provider latency increased."),
            ("10:02:12", "ERROR", "Inventory provider requests timed out."),
            ("10:03:15", "WARN", "Local CPU, memory and DB pool remain within normal bounds."),
        ],
        "evidence": [
            ("External provider latency increased", "Supports dependency degradation"),
            ("Inventory provider requests timed out", "Direct evidence of downstream timeout"),
            ("Local resource metrics remain normal", "Weakens local resource exhaustion hypotheses"),
        ],
        "hypotheses": [
            {"name": "External dependency degradation", "score": 93, "reason": "Timeout logs and external latency rise while local metrics remain normal."},
            {"name": "Local CPU saturation", "score": 9, "reason": "CPU utilization is within the supplied normal range."},
            {"name": "Database connection exhaustion", "score": 11, "reason": "DB connection usage is normal in this scenario."},
        ],
        "action": "Enable the simulated fallback response and retry with backoff",
        "risk": "Low — fallback may return temporarily stale or partial data; human approval is required.",
    },
}

def init_state():
    defaults = {
        "scenario_name": list(SCENARIOS.keys())[0],
        "incident_detected": True,
        "recovery_approved": False,
        "recovered": False,
        "timeline": [],
        "incident_id": "INC-2026-1042",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def add_event(message):
    st.session_state.timeline.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "event": message,
    })

def reset_demo():
    st.session_state.incident_detected = False
    st.session_state.recovery_approved = False
    st.session_state.recovered = False
    st.session_state.timeline = []
    add_event("Demo reset. Monitoring is ready.")

init_state()
scenario = SCENARIOS[st.session_state.scenario_name]
current = scenario["after"] if st.session_state.recovered else scenario["before"]

# ---------- Sidebar ----------
with st.sidebar:
    st.title("🛡️ Project Eclipse")
    st.caption("AI-Powered Autonomous SRE")
    st.markdown("---")
    chosen = st.selectbox("Incident scenario", list(SCENARIOS.keys()), index=list(SCENARIOS.keys()).index(st.session_state.scenario_name))
    if chosen != st.session_state.scenario_name:
        st.session_state.scenario_name = chosen
        st.session_state.incident_detected = True
        st.session_state.recovery_approved = False
        st.session_state.recovered = False
        st.session_state.timeline = []
        st.session_state.incident_id = f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        add_event(f"Scenario selected: {chosen}")
        st.rerun()
    st.markdown("### Demo controls")
    if st.button("🚨 Trigger / Detect Incident", use_container_width=True):
        st.session_state.incident_detected = True
        st.session_state.recovery_approved = False
        st.session_state.recovered = False
        add_event("Incident detected from simulated telemetry.")
        st.rerun()
    if st.button("↻ Reset demo", use_container_width=True):
        reset_demo()
        st.rerun()
    st.markdown("---")
    st.caption("Prototype mode: synthetic data only. No production systems are connected.")

# ---------- Header ----------
st.title("Production Incident Investigation & Recovery")
st.markdown("**Detect → Investigate → Reason → Recover → Verify → Learn**")
st.caption("Team Titans • Project Eclipse • Simulated production environment")

status = "RECOVERED" if st.session_state.recovered else ("CRITICAL" if st.session_state.incident_detected else "MONITORING")
color = "🟢" if status == "RECOVERED" else ("🔴" if status == "CRITICAL" else "🟡")
st.markdown(f"### {color} System status: **{status}** &nbsp;&nbsp; · &nbsp;&nbsp; Incident: `{st.session_state.incident_id}` &nbsp;&nbsp; · &nbsp;&nbsp; Service: `{scenario['service']}`")

# ---------- Metric row ----------
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Error rate", f"{current['error_rate']:.1f}%", delta="Recovered" if st.session_state.recovered else "Above threshold", delta_color="normal" if st.session_state.recovered else "inverse")
m2.metric("Latency (p95)", f"{current['latency_ms']} ms", delta="Recovered" if st.session_state.recovered else "High latency", delta_color="normal" if st.session_state.recovered else "inverse")
m3.metric("CPU usage", f"{current['cpu']}%", delta="Stable" if st.session_state.recovered else "Elevated", delta_color="normal" if st.session_state.recovered else "inverse")
m4.metric("Memory usage", f"{current['memory']}%", delta="Stable")
m5.metric("DB connections", f"{current['db_connections']}%", delta="Stable" if st.session_state.recovered else "Check pool", delta_color="normal" if st.session_state.recovered else "inverse")

st.markdown("---")
left, right = st.columns([1.15, 0.85], gap="large")

with left:
    st.subheader("1 · Incident investigation")
    st.info(scenario["summary"])
    st.markdown("**Simulated application logs**")
    log_df = pd.DataFrame(scenario["logs"], columns=["Time", "Level", "Message"])
    st.dataframe(log_df, use_container_width=True, hide_index=True)
    st.markdown("**Evidence collected**")
    evidence_df = pd.DataFrame(scenario["evidence"], columns=["Evidence", "Interpretation"])
    st.dataframe(evidence_df, use_container_width=True, hide_index=True)

with right:
    st.subheader("2 · Root cause hypotheses")
    for i, item in enumerate(scenario["hypotheses"], start=1):
        st.markdown(f"**{i}. {item['name']}**")
        st.progress(item["score"] / 100, text=f"Evidence support score: {item['score']} / 100")
        st.caption(item["reason"])
    st.warning("Scores are prototype evidence-support scores, not calibrated probabilities.")
    st.markdown("**Recommended recovery**")
    st.write(scenario["action"])
    st.caption(scenario["risk"])
    if not st.session_state.recovered:
        approval = st.checkbox("I approve this simulated recovery action", value=st.session_state.recovery_approved, key="approve_checkbox")
        st.session_state.recovery_approved = approval
        if st.button("🛠️ Execute approved recovery", type="primary", use_container_width=True, disabled=not approval):
            add_event(f"Human approved action: {scenario['action']}")
            add_event("Recovery action simulated successfully.")
            st.session_state.recovered = True
            add_event("Verification passed: service metrics returned to the scenario's expected healthy values.")
            st.rerun()
    else:
        st.success("Recovery simulation complete. Verification passed.")
        if st.button("Run recovery again / reset incident", use_container_width=True):
            st.session_state.recovered = False
            st.session_state.recovery_approved = False
            st.session_state.timeline = []
            add_event("Incident reset for another demonstration.")
            st.rerun()

# ---------- Before/after and workflow ----------
st.markdown("---")
st.subheader("3 · Recovery verification")
before = scenario["before"]
after = scenario["after"] if st.session_state.recovered else None
comparison = pd.DataFrame({
    "Metric": ["Error rate (%)", "Latency (ms)", "CPU (%)", "Memory (%)", "DB connections (%)"],
    "Before recovery": [before["error_rate"], before["latency_ms"], before["cpu"], before["memory"], before["db_connections"]],
    "Current / after recovery": [current["error_rate"], current["latency_ms"], current["cpu"], current["memory"], current["db_connections"]],
})
st.dataframe(comparison, use_container_width=True, hide_index=True)
if st.session_state.recovered:
    st.success("Verification passed in the simulator: error rate and latency have decreased. These are illustrative scenario values, not measurements from a real production system.")
else:
    st.info("Approve the recovery action to simulate remediation and reveal the post-recovery state.")

st.markdown("#### Workflow status")
steps = [
    ("Detect", st.session_state.incident_detected),
    ("Investigate", st.session_state.incident_detected),
    ("Reason", st.session_state.incident_detected),
    ("Recover", st.session_state.recovered),
    ("Verify", st.session_state.recovered),
    ("Learn", st.session_state.recovered),
]
cols = st.columns(6)
for col, (label, done) in zip(cols, steps):
    col.metric(label, "Complete" if done else "Pending")

st.markdown("---")
st.subheader("4 · Incident timeline & downloadable report")
if not st.session_state.timeline:
    st.session_state.timeline = [{
        "time": datetime.now().strftime("%H:%M:%S"),
        "event": "Monitoring dashboard initialized with simulated incident data."
    }]
timeline_df = pd.DataFrame(st.session_state.timeline)
st.dataframe(timeline_df, use_container_width=True, hide_index=True)

report = {
    "project": "Project Eclipse - Team Titans",
    "incident_id": st.session_state.incident_id,
    "scenario": st.session_state.scenario_name,
    "service": scenario["service"],
    "status": "RECOVERED" if st.session_state.recovered else status,
    "summary": scenario["summary"],
    "evidence": [{"item": a, "interpretation": b} for a, b in scenario["evidence"]],
    "hypotheses": scenario["hypotheses"],
    "recommended_action": scenario["action"],
    "human_approved": bool(st.session_state.recovery_approved),
    "recovery_simulated": bool(st.session_state.recovered),
    "before_metrics": scenario["before"],
    "current_metrics": current,
    "timeline": st.session_state.timeline,
    "disclaimer": "Simulation only; no live production systems were accessed or changed.",
}
st.download_button(
    "⬇️ Download incident report (JSON)",
    data=json.dumps(report, indent=2),
    file_name=f"{st.session_state.incident_id.lower()}_report.json",
    mime="application/json",
    use_container_width=True,
)

with st.expander("Prototype scope and evaluation notes"):
    st.markdown("""
    - **Implemented:** scenario-based incident detection, evidence display, hypothesis ranking, human approval, simulated recovery, verification state, timeline and JSON report.
    - **Not connected:** Prometheus, Loki/ELK, Jaeger, GitHub API, Docker, PostgreSQL or live infrastructure.
    - **Reasoning method:** transparent scenario rules and evidence-support scores; not a trained ML model or calibrated probability.
    - **Safety:** recovery is simulated only. A real implementation must add authentication, authorization, audit controls, rollback safeguards and environment-specific validation.
    """)
