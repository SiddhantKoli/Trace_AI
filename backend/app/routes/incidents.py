from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.database import get_db
from app.models import Incident, IncidentEvidence, Diagnosis
from app.schemas import IncidentOut, IncidentUpdate

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=List[IncidentOut])
def list_incidents(
    run_id: Optional[str] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Browse, filter, and search incidents across runs.
    """
    query = (
        db.query(Incident)
        .options(
            joinedload(Incident.evidence).joinedload(IncidentEvidence.log),
            joinedload(Incident.diagnosis)
        )
    )

    if run_id:
        query = query.filter(Incident.run_id == run_id)
    if severity:
        query = query.filter(Incident.severity == severity.upper())
    if category:
        query = query.filter(Incident.category == category.lower())
    if status:
        query = query.filter(Incident.status == status.upper())
    if search:
        query = query.filter(
            (Incident.title.ilike(f"%{search}%")) |
            (Incident.summary.ilike(f"%{search}%"))
        )

    incidents = query.order_by(desc(Incident.detected_time)).offset(offset).limit(limit).all()
    return incidents


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """
    Returns deep investigation details for a specific incident.
    """
    incident = (
        db.query(Incident)
        .options(
            joinedload(Incident.evidence).joinedload(IncidentEvidence.log),
            joinedload(Incident.diagnosis)
        )
        .filter(Incident.id == incident_id)
        .first()
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}", response_model=IncidentOut)
def update_incident(
    incident_id: str,
    update_data: IncidentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update incident status (e.g., CONFIRMED, RESOLVED, MANUAL_REVIEW).
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if update_data.status:
        incident.status = update_data.status.upper()
        db.commit()
        db.refresh(incident)

    return incident
