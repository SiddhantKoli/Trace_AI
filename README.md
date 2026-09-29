# TRACE AI &bull; AI-Powered Log Analysis & Incident Investigation Platform

TRACE AI is a developer-centric log analysis and incident investigation platform that transforms raw application logs into structured, evidence-based incident reports using Machine Learning (**scikit-learn Isolation Forest**) and AI decision primitives (**TypeSafe Jev System One**).

---

## 🌟 Key Features

1. **Multi-Format Log Ingestion (`/upload`)**:
   - Ingests `.log`, `.txt`, and structured `.csv` files up to 25MB.
   - Robust parsing of ISO timestamps, syslog/bracket formats, logfmt, and JSON lines.
   - Malformed line resilience with parsed vs. rejected counters.
   - Automated redaction of sensitive credentials (tokens, passwords, API keys) before external transmission.
   - 1-Click quick load for 6 pre-packaged, labelled incident scenarios.

2. **Isolation Forest ML Anomaly Detection (`/analysis`)**:
   - Computes multi-dimensional feature vectors per log entry:
     - Log severity weight (DEBUG to CRITICAL)
     - Inter-arrival time deltas (burst velocity)
     - 60-second rolling error frequency & density
     - Service-level error ratios and message characteristics
   - Reports relative within-file Isolation Forest scores between `0.0` and `1.0`; these rank observations and are not probabilities.
   - Explains top contributing drivers for every flagged outlier.
   - Clearly distinguishes anomalies from confirmed incidents.

3. **Temporal & Dependency Incident Correlation (`/incidents`)**:
   - Groups anomalies into coherent incident clusters within configurable sliding time windows (default: 120s).
   - Groups only when events share a concrete event signature or an explicit service dependency, in addition to temporal proximity.
   - Uses neutral incident-candidate titles and records dependency evidence when present.
   - Strictly enforces causation safeguards: *"Temporal order alone is not treated as proof of causation without root-cause validation."*

4. **TypeSafe Jev AI Decision Primitive (`/incidents/[id]`)**:
   - Integrates with TypeSafe's Jev model via `POST https://api.typesafe.ai/v1/systemone`.
   - Uses typed System One decision primitives (`Choice`, `Noul`, `Score`) for deterministic categorization, severity assessment, and operational urgency rating.
   - Model-reported confidence and uncertainty rating; confidence is not presented as calibrated unless separately validated.
   - Insufficient evidence safeguarding: displays "Insufficient evidence" rather than fabricating a diagnosis.
   - Clearly labelled deterministic demo heuristics when live credentials are not supplied; heuristic scores are not probabilities.

5. **Incident Reports & Exporting**:
   - Download executive-grade PDF incident reports generated server-side using **ReportLab**.
   - Download structured JSON incident summaries.

6. **Empirical Evaluation Benchmark Suite (`/evaluation`)**:
   - Automated benchmark evaluation covering 5 labelled ground-truth scenarios:
     1. Database Connection Pool Exhaustion
     2. Repeated HTTP 500 Error Surge
     3. High Memory Usage & Linux OOM Killer
     4. Network Timeout & Circuit Breaker Cascade
     5. Normal Baseline Operational Activity
   - Computes empirical **Precision**, **Recall**, **F1-Score**, **False-Positive Rate (FPR)**, and **Diagnosis Accuracy** from actual test runs without hardcoding.
   - Uses explicit, reviewed per-line annotations for point-anomaly ground truth; incident correlation is evaluated separately from anomaly detection.
   - Reports low recall or false positives as measured rather than converting every error-severity line into a positive label.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 16 (App Router) + TypeScript | Responsive developer interface |
| **Styling** | Tailwind CSS v4 | Charcoal dark theme (`#0d0f12`), subtle borders, emerald/amber/rose state colors |
| **Charts** | Recharts | Anomaly score scatter charts, timeline area charts, severity bars |
| **Backend** | Python 3.11 + FastAPI | Async REST API & ingestion orchestration |
| **ML Engine** | scikit-learn (`IsolationForest`) | Statistical log anomaly detection |
| **AI Decision** | TypeSafe Jev System One (`v1/systemone`) | Structured incident classification & urgency scoring |
| **Database** | SQLite + SQLAlchemy ORM | Local persistence of runs, logs, anomalies, and incidents |
| **Validation** | Pydantic v2 | Strict request/response validation |
| **PDF Generation** | ReportLab | Executive PDF incident investigation reports |
| **Testing** | pytest + pytest-asyncio | Automated backend test suite |

---

## 🚀 Quickstart & Setup Instructions

### Prerequisites
- Python 3.10+ (tested on Python 3.11)
- Node.js 18+ (tested on Node v24)
- npm

### 1. Environment Configuration
Copy the provided `.env.example` into `.env`:
```bash
cp .env.example .env
```
Key configuration parameters:
- `JEV_API_KEY`: *(Optional)* Your TypeSafe AI API key. If left blank, TRACE AI operates in deterministic Demo Mode.
- `DEMO_MODE`: `true` or `false` (default: `true`).
- `DEFAULT_CONTAMINATION`: `0.08` (8% outlier sensitivity).
- `DEFAULT_CORRELATION_WINDOW_SECONDS`: `120` (2-minute incident window).

The Settings page exposes the same choice as a Demo Data / Real Data toggle. Demo mode shows bundled scenario runs. Real mode hides those runs and starts the dashboard at zero until you upload a real log file. Switching modes does not delete either dataset; it changes which namespace is visible.

While Real Data mode is active, Settings also provides **Clear Real Data**. It requires confirmation and deletes uploaded real-mode runs plus their logs, anomalies, incidents, evidence, and diagnoses. Demo data is preserved.

All parsed timestamps with offsets are normalized to UTC at ingestion. Incident cards and event timelines display UTC explicitly so event ordering and incident start times use the same reference zone.

### 2. Backend Setup
From the repository root:
```powershell
# Activate Python virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies (if not already installed)
pip install -r backend/requirements.txt

# Run automated tests
pytest backend/tests/ -v

# Start FastAPI development server (running on port 8000)
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger API documentation will be available at: `http://127.0.0.1:8000/docs`.

### 3. Frontend Setup
In a separate terminal:
```powershell
cd frontend

# Install dependencies
npm install

# Start Next.js development server (running on port 3000)
npm run dev
```
Open your browser at: `http://localhost:3000`.

---

## 🧪 Running the Evaluation Benchmark

Run the empirical evaluation benchmark directly from the CLI:
```powershell
.\venv\Scripts\python -c "import sys; sys.path.insert(0, 'backend'); import asyncio; from app.evaluation import evaluator; res = asyncio.run(evaluator.run_evaluation()); print(res.model_dump_json(indent=2))"
```
Or navigate to the `/evaluation` page in the web interface and click **"Run Evaluation Suite"**.

The benchmark intentionally separates three claims: Isolation Forest point anomalies, multi-error incident clusters, and diagnosis category matches. A demo diagnosis is an evidence-based hypothesis with a heuristic score cap; it is not a verified root cause and must be checked against metrics, traces, and deployment context.

---

## 📂 Project Structure

```
Trace AI/
├── backend/
│   ├── app/
│   │   ├── config.py              # Pydantic v2 configuration & env vars
│   │   ├── database.py            # SQLite & SQLAlchemy engine
│   │   ├── models.py              # LogEntry, Anomaly, Incident, Diagnosis, AnalysisRun
│   │   ├── schemas.py             # Pydantic validation schemas
│   │   ├── parser.py              # LogParser (.log, .txt, .csv) & sanitization
│   │   ├── anomaly_detector.py    # Isolation Forest feature extraction & scoring
│   │   ├── correlator.py          # Signature/dependency-aware incident grouping
│   │   ├── jev_client.py          # TypeSafe Jev System One client & demo mock
│   │   ├── report_generator.py    # ReportLab PDF & JSON exporter
│   │   ├── evaluation.py          # Benchmark suite & empirical metric calculations
│   │   ├── main.py                # FastAPI entrypoint & middleware
│   │   └── routes/                # Modular API endpoints
│   ├── tests/                     # Automated parser, ML, correlation, Jev, and evaluation tests
│   ├── sample_data/               # 6 labelled scenario log datasets
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx           # Overview Dashboard (KPIs, Charts, Recent Incidents)
│   │   │   ├── upload/page.tsx    # Drag-and-drop ingestion & sample catalogue
│   │   │   ├── analysis/page.tsx  # Isolation Forest spectrum & log explorer
│   │   │   ├── incidents/page.tsx # Incident browser with multi-facet filters
│   │   │   ├── incidents/[id]/    # Deep dive, AI diagnosis, timeline & PDF export
│   │   │   ├── evaluation/        # Benchmark scorecards & confusion matrix
│   │   │   └── settings/page.tsx  # Jev API key configuration & ML sliders
│   │   ├── components/            # Badges, Navbar, Chart wrappers
│   │   └── lib/                   # Typed API client and UTC display helpers
│   └── package.json
├── TRACE_AI_PRD.pdf               # Original Product Requirements Document
├── .env.example
└── README.md
```

---

## 🔒 Security & Privacy Posture
- **Secret Handling**: `JEV_API_KEY` is submitted to the FastAPI backend when saved and remembered in browser `localStorage` so the settings field survives refreshes. Browser storage is not encrypted; use this only on a trusted device.
- **Evidence Sanitization**: Log messages are scanned and redacted (`[REDACTED_TOKEN]`, `[REDACTED_PASSWORD]`, `[REDACTED_API_KEY]`) before being processed by AI models.
- **Selective Payloads**: Only structured, relevant incident evidence lines are sent to external decision APIs—never whole log files.
- **Uncertainty Handling**: Demo diagnoses are labeled heuristic hypotheses, live Jev responses are validated before use, and unsupported responses become manual-review results rather than asserted diagnoses.
