from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.config import active_data_mode
from app.database import get_db
from app.models import AnalysisRun, LogEntry, Anomaly, Incident, Diagnosis
from app.schemas import AnalysisRunOut, AnalysisRunDetail, LogEntryOut, AnomalyOut, DashboardStats, IncidentOut

router = APIRouter(prefix="/analysis", tags=["Analysis & Metrics"])


@router.get("/runs", response_model=List[AnalysisRunOut])
def list_analysis_runs(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Lists recent log analysis runs."""
    runs = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.data_mode == active_data_mode())
        .order_by(desc(AnalysisRun.start_time))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return runs


@router.get("/runs/{run_id}", response_model=AnalysisRunDetail)
def get_analysis_run(run_id: str, db: Session = Depends(get_db)):
    """Fetches comprehensive details for a specific run."""
    run = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.id == run_id, AnalysisRun.data_mode == active_data_mode())
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return run


@router.get("/runs/{run_id}/logs")
def get_run_logs(
    run_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    severity: Optional[str] = None,
    is_anomaly: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Paginated logs for a run with multi-criteria filtering.
    """
    run = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.id == run_id, AnalysisRun.data_mode == active_data_mode())
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found in the active data mode")

    query = db.query(LogEntry).filter(LogEntry.run_id == run_id)

    if severity:
        query = query.filter(LogEntry.severity == severity.upper())

    if search:
        query = query.filter(
            (LogEntry.message.ilike(f"%{search}%")) |
            (LogEntry.service.ilike(f"%{search}%"))
        )

    if is_anomaly is not None:
        if is_anomaly:
            query = query.join(Anomaly, Anomaly.log_id == LogEntry.id).filter(Anomaly.is_anomaly == True)
        else:
            query = query.outerjoin(Anomaly, Anomaly.log_id == LogEntry.id).filter(
                (Anomaly.id == None) | (Anomaly.is_anomaly == False)
            )

    total_count = query.count()
    offset = (page - 1) * page_size
    entries = query.order_by(LogEntry.line_number.asc()).offset(offset).limit(page_size).all()

    # Load anomaly scores
    result_items = []
    for e in entries:
        anom = db.query(Anomaly).filter(Anomaly.log_id == e.id).first()
        result_items.append({
            "id": e.id,
            "run_id": e.run_id,
            "line_number": e.line_number,
            "timestamp": e.timestamp,
            "raw_timestamp": e.raw_timestamp,
            "severity": e.severity,
            "service": e.service,
            "message": e.message,
            "raw_text": e.raw_text,
            "is_malformed": e.is_malformed,
            "anomaly_score": anom.anomaly_score if anom else 0.0,
            "is_anomaly": anom.is_anomaly if anom else False,
            "feature_contributions": anom.feature_contributions if anom else None
        })

    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 1,
        "items": result_items
    }


@router.get("/runs/{run_id}/anomalies", response_model=List[AnomalyOut])
def get_run_anomalies(
    run_id: str,
    min_score: float = 0.5,
    db: Session = Depends(get_db)
):
    """
    Returns anomalies with feature contribution metrics for distribution charts.
    """
    anomalies = (
        db.query(Anomaly)
        .join(AnalysisRun, Anomaly.run_id == AnalysisRun.id)
        .filter(
            Anomaly.run_id == run_id,
            AnalysisRun.data_mode == active_data_mode(),
            Anomaly.anomaly_score >= min_score,
        )
        .order_by(desc(Anomaly.anomaly_score))
        .all()
    )
    return anomalies


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    run_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Derives real-time dashboard metrics strictly from ingested database records.
    PRD Section 4.5: 'All metrics and charts must derive from uploaded data, never hardcoded values.'
    """
    # If run_id is not specified, use latest run or aggregate across runs
    target_run = None
    if run_id:
        target_run = (
            db.query(AnalysisRun)
            .filter(AnalysisRun.id == run_id, AnalysisRun.data_mode == active_data_mode())
            .first()
        )
    else:
        target_run = (
            db.query(AnalysisRun)
            .filter(
                AnalysisRun.status == "COMPLETED",
                AnalysisRun.data_mode == active_data_mode(),
            )
            .order_by(desc(AnalysisRun.start_time))
            .first()
        )

    current_run_id = target_run.id if target_run else None

    # Base queries filtered by run if available, or all completed runs
    logs_q = db.query(LogEntry)
    anom_q = db.query(Anomaly)
    inc_q = db.query(Incident)

    if current_run_id:
        logs_q = logs_q.filter(LogEntry.run_id == current_run_id)
        anom_q = anom_q.filter(Anomaly.run_id == current_run_id)
        inc_q = inc_q.filter(Incident.run_id == current_run_id)
    else:
        logs_q = logs_q.join(AnalysisRun, LogEntry.run_id == AnalysisRun.id).filter(AnalysisRun.data_mode == active_data_mode())
        anom_q = anom_q.join(AnalysisRun, Anomaly.run_id == AnalysisRun.id).filter(AnalysisRun.data_mode == active_data_mode())
        inc_q = inc_q.join(AnalysisRun, Incident.run_id == AnalysisRun.id).filter(AnalysisRun.data_mode == active_data_mode())

    total_logs = logs_q.count()
    total_anomalies = anom_q.filter(Anomaly.is_anomaly == True).count()
    total_incidents = inc_q.count()

    # Severity distribution
    sev_rows = logs_q.with_entities(LogEntry.severity, func.count(LogEntry.id)).group_by(LogEntry.severity).all()
    severity_dist = {s: 0 for s in ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]}
    for sev, count in sev_rows:
        severity_dist[str(sev).upper()] = count

    # Category distribution
    cat_rows = inc_q.with_entities(Incident.category, func.count(Incident.id)).group_by(Incident.category).all()
    category_dist = {}
    for cat, count in cat_rows:
        category_dist[str(cat)] = count

    # Error frequency timeline (sampled bucket by minute or sequential groups)
    timeline = []
    recent_logs = logs_q.order_by(LogEntry.timestamp.asc()).all()
    if recent_logs:
        # Group in up to 15 time buckets
        step = max(1, len(recent_logs) // 15)
        for i in range(0, len(recent_logs), step):
            slice_chunk = recent_logs[i:i + step]
            if not slice_chunk:
                continue
            bucket_time = slice_chunk[0].timestamp.strftime("%H:%M:%S") if slice_chunk[0].timestamp else f"Step {i}"
            crit_count = sum(1 for l in slice_chunk if l.severity == "CRITICAL")
            err_count = sum(1 for l in slice_chunk if l.severity == "ERROR")
            warn_count = sum(1 for l in slice_chunk if l.severity == "WARNING")
            info_count = sum(1 for l in slice_chunk if l.severity in ("INFO", "DEBUG"))
            
            timeline.append({
                "time": bucket_time,
                "critical": crit_count,
                "errors": err_count,
                "warnings": warn_count,
                "info": info_count,
                "total": len(slice_chunk)
            })

    # Recent incidents
    recent_incidents = inc_q.order_by(desc(Incident.detected_time)).limit(5).all()

    return DashboardStats(
        total_entries_analysed=total_logs,
        total_anomalies_detected=total_anomalies,
        total_incidents_identified=total_incidents,
        severity_distribution=severity_dist,
        category_distribution=category_dist,
        error_frequency_timeline=timeline,
        recent_incidents=recent_incidents,
        latest_run_id=current_run_id
    )
