import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models import AnalysisRun, LogEntry, Anomaly, Incident, IncidentEvidence, Diagnosis
from app.parser import LogParser
from app.anomaly_detector import AnomalyDetector
from app.correlator import IncidentCorrelator
from app.jev_client import jev_client
from app.schemas import AnalysisRunOut

router = APIRouter(prefix="/upload", tags=["Upload & Ingestion"])

ALLOWED_EXTENSIONS = {".log", ".txt", ".csv"}
BASE_SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sample_data")


async def process_log_pipeline(
    filename: str,
    content: str,
    file_size_bytes: int,
    db: Session,
    contamination: Optional[float] = None,
    correlation_window: Optional[int] = None
) -> AnalysisRun:
    """
    Core pipeline executing:
    Log Parsing -> Anomaly Detection -> Incident Correlation -> Jev Diagnosis -> Persistence
    """
    run = AnalysisRun(
        filename=filename,
        file_size_bytes=file_size_bytes,
        status="PROCESSING",
        start_time=datetime.utcnow()
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        # 1. Parse logs
        parser = LogParser()
        raw_entries, parsed_count, rejected_count = parser.parse(content, filename)

        if not raw_entries:
            run.status = "COMPLETED"
            run.total_entries = 0
            run.parsed_count = 0
            run.rejected_count = rejected_count
            run.completion_time = datetime.utcnow()
            db.commit()
            return run

        # Persist LogEntry objects
        db_entries = []
        for e in raw_entries:
            db_entry = LogEntry(
                run_id=run.id,
                line_number=e["line_number"],
                timestamp=e["timestamp"],
                raw_timestamp=e.get("raw_timestamp"),
                severity=e["severity"],
                service=e["service"],
                message=e["message"],
                raw_text=e["raw_text"],
                is_malformed=e["is_malformed"]
            )
            db.add(db_entry)
            db_entries.append(db_entry)

        db.commit()
        for dbe in db_entries:
            db.refresh(dbe)

        # 2. ML Anomaly Detection (Isolation Forest)
        contam = contamination if contamination is not None else settings.DEFAULT_CONTAMINATION
        detector = AnomalyDetector(contamination=contam)
        anomaly_results = detector.detect(raw_entries)

        # Persist Anomalies
        anom_count = 0
        for dbe, anom_res in zip(db_entries, anomaly_results):
            if anom_res["is_anomaly"]:
                anom_count += 1
            anomaly_obj = Anomaly(
                run_id=run.id,
                log_id=dbe.id,
                anomaly_score=anom_res["anomaly_score"],
                is_anomaly=anom_res["is_anomaly"],
                feature_contributions=anom_res.get("feature_contributions")
            )
            db.add(anomaly_obj)

        db.commit()

        # 3. Incident Correlation
        window = correlation_window if correlation_window is not None else settings.DEFAULT_CORRELATION_WINDOW_SECONDS
        correlator = IncidentCorrelator(window_seconds=window)
        candidate_incidents = correlator.correlate(raw_entries, anomaly_results)

        # 4. Jev AI Diagnosis & Incident Persistence
        inc_count = 0
        for cand in candidate_incidents:
            inc_count += 1
            # Perform Jev diagnosis
            diag_res = await jev_client.analyze_incident(cand)

            incident_obj = Incident(
                run_id=run.id,
                title=cand["title"],
                severity=cand["severity"],
                category=cand["category"],
                status="INVESTIGATING" if diag_res.get("confidence", 0.0) >= 0.70 else "MANUAL_REVIEW",
                detected_time=cand["detected_time"],
                summary=cand["summary"],
                confidence=diag_res.get("confidence", 0.0)
            )
            db.add(incident_obj)
            db.commit()
            db.refresh(incident_obj)

            # Persist Evidence items
            for item in cand.get("evidence_items", []):
                # find corresponding LogEntry by line_number
                target_entry = next((d for d in db_entries if d.line_number == item["entry"]["line_number"]), None)
                if target_entry:
                    ev_obj = IncidentEvidence(
                        incident_id=incident_obj.id,
                        log_id=target_entry.id,
                        evidence_type=item["evidence_type"],
                        description=item["description"]
                    )
                    db.add(ev_obj)

            # Persist Diagnosis
            diag_obj = Diagnosis(
                incident_id=incident_obj.id,
                possible_cause=diag_res["possible_cause"],
                confidence=diag_res["confidence"],
                explanation=diag_res["explanation"],
                uncertainty=diag_res.get("uncertainty"),
                recommended_steps=diag_res.get("recommended_steps", []),
                raw_jev_response=diag_res.get("raw_jev_response"),
                is_demo_mode=diag_res.get("is_demo_mode", True)
            )
            db.add(diag_obj)

        db.commit()

        # 5. Finalize AnalysisRun
        run.status = "COMPLETED"
        run.total_entries = len(raw_entries)
        run.parsed_count = parsed_count
        run.rejected_count = rejected_count
        run.anomaly_count = anom_count
        run.incident_count = inc_count
        run.completion_time = datetime.utcnow()
        db.commit()
        db.refresh(run)

        return run

    except Exception as ex:
        db.rollback()
        run.status = "FAILED"
        run.error_message = str(ex)
        run.completion_time = datetime.utcnow()
        db.commit()
        raise


@router.post("", response_model=AnalysisRunOut)
async def upload_log_file(
    file: UploadFile = File(...),
    contamination: Optional[float] = Form(None),
    correlation_window: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload and analyze .log, .txt, or .csv files.
    Enforces file-type and file-size constraints.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported formats: .log, .txt, .csv"
        )

    # Read content
    raw_bytes = await file.read()
    file_size_mb = len(raw_bytes) / (1024 * 1024)
    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size limit of {settings.MAX_FILE_SIZE_MB}MB."
        )

    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = raw_bytes.decode("latin-1", errors="replace")

    run = await process_log_pipeline(
        filename=file.filename,
        content=content,
        file_size_bytes=len(raw_bytes),
        db=db,
        contamination=contamination,
        correlation_window=correlation_window
    )
    return run


@router.post("/sample/{sample_name}", response_model=AnalysisRunOut)
async def load_sample_log(
    sample_name: str,
    db: Session = Depends(get_db)
):
    """
    Loads and runs full analysis on a pre-packaged sample dataset.
    """
    valid_samples = {
        "database": "database_connection_exhaustion.log",
        "http_500": "http_500_cluster.log",
        "memory": "high_memory_oom.log",
        "network": "network_timeout_cascade.log",
        "baseline": "normal_activity_baseline.log",
        "malformed": "mixed_malformed_sample.log"
    }

    filename = valid_samples.get(sample_name)
    if not filename:
        raise HTTPException(status_code=404, detail=f"Sample '{sample_name}' not found. Available: {list(valid_samples.keys())}")

    filepath = os.path.join(BASE_SAMPLE_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Sample file not found on disk.")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    run = await process_log_pipeline(
        filename=filename,
        content=content,
        file_size_bytes=len(content.encode("utf-8")),
        db=db
    )
    return run
