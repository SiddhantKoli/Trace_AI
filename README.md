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
   - Normalizes statistical decision scores between `0.0` and `1.0`.
   - Explains top contributing drivers for every flagged outlier.
   - Clearly distinguishes anomalies from confirmed incidents.

3. **Temporal & Dependency Incident Correlation (`/incidents`)**:
   - Groups anomalies into coherent incident clusters within configurable sliding time windows (default: 120s).
   - Maps cascading failure paths across upstream APIs, microservices, and databases.
   - Strictly enforces causation safeguards: *"Temporal order alone is not treated as proof of causation without root-cause validation."*

4. **TypeSafe Jev AI Decision Primitive (`/incidents/[id]`)**:
   - Integrates with TypeSafe's Jev model via `POST https://api.typesafe.ai/v1/systemone`.
   - Uses typed System One decision primitives (`Choice`, `Noul`, `Score`) for deterministic categorization, severity assessment, and operational urgency rating.
   - Calibrated confidence scoring and uncertainty rating.
   - Insufficient evidence safeguarding: displays "Insufficient evidence" rather than fabricating a diagnosis.
   - Clearly labelled deterministic demo mode when live credentials are not supplied.

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
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
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
│   │   ├── correlator.py          # Temporal sliding window incident grouping
│   │   ├── jev_client.py          # TypeSafe Jev System One client & demo mock
│   │   ├── report_generator.py    # ReportLab PDF & JSON exporter
│   │   ├── evaluation.py          # Benchmark suite & empirical metric calculations
│   │   ├── main.py                # FastAPI entrypoint & middleware
│   │   └── routes/                # Modular API endpoints
│   ├── tests/                     # 12 automated unit & integration tests
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
│   │   └── lib/api.ts             # Typed API client
│   └── package.json
├── TRACE_AI_PRD.pdf               # Original Product Requirements Document
├── .env.example
└── README.md
```

---

## 🔒 Security & Privacy Posture
- **Secret Isolation**: `JEV_API_KEY` is loaded exclusively on the FastAPI backend and never leaked to frontend browser bundles.
- **Evidence Sanitization**: Log messages are scanned and redacted (`[REDACTED_TOKEN]`, `[REDACTED_PASSWORD]`, `[REDACTED_API_KEY]`) before being processed by AI models.
- **Selective Payloads**: Only structured, relevant incident evidence lines are sent to external decision APIs—never whole log files.
