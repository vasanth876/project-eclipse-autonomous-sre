# Project Eclipse — Team Titans
## AI-Powered Production Incident Investigation & Recovery

A hackathon-ready Streamlit prototype that demonstrates:
- Simulated incident telemetry and application logs
- Evidence-based root-cause hypotheses
- Human approval before a simulated remediation
- Before/after recovery verification
- Incident timeline and downloadable JSON report

### Requirements
- Python 3.10 or newer (Python 3.11/3.12 recommended)
- VS Code
- Internet access for the first package installation

### Run on Windows (VS Code integrated terminal / PowerShell)
Open this folder in VS Code, then run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

If PowerShell blocks activation, use:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL Streamlit prints, usually http://localhost:8501.

### Demo sequence
1. Choose an incident scenario from the sidebar.
2. Show metrics and logs before recovery.
3. Explain the leading root-cause hypothesis using the evidence table.
4. Tick the approval checkbox and click **Execute approved recovery**.
5. Show the improved metrics, verification status, timeline and JSON report.
6. Download the incident report.

### Important scope statement
This is a **simulation using synthetic scenario data**. It does not connect to or modify production systems. Hypothesis scores are evidence-support scores, not calibrated probabilities. Do not present the illustrative values as real measurements.
