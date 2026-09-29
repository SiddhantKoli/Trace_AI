from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Incident, IncidentEvidence
from app.report_generator import report_generator
from app.schemas import IncidentOut

router = APIRouter(prefix="/reports", tags=["Reports & Export"])


@router.get("/incident/{incident_id}/pdf")
def export_incident_pdf(incident_id: str, db: Session = Depends(get_db)):
    """
    Exports a professional, branded PDF incident report.
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

    # Serialize to schema dict
    incident_data = IncidentOut.from_orm(incident).model_dump()
    pdf_bytes = report_generator.generate_pdf_report(incident_data)

    filename = f"trace_ai_incident_{incident_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/incident/{incident_id}/json")
def export_incident_json(incident_id: str, db: Session = Depends(get_db)):
    """
    Exports structured incident details as JSON.
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

    incident_data = IncidentOut.from_orm(incident).model_dump()
    json_str = report_generator.generate_json_report(incident_data)

    filename = f"trace_ai_incident_{incident_id[:8]}.json"
    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
