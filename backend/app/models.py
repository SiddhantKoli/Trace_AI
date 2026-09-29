import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    status = Column(String(50), default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED
    data_mode = Column(String(10), default="real", index=True)  # demo or real
    error_message = Column(Text, nullable=True)
    
    total_entries = Column(Integer, default=0)
    parsed_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    anomaly_count = Column(Integer, default=0)
    incident_count = Column(Integer, default=0)
    
    start_time = Column(DateTime, default=datetime.utcnow)
    completion_time = Column(DateTime, nullable=True)
    
    # Relationships
    logs = relationship("LogEntry", back_populates="run", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="run", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="run", cascade="all, delete-orphan")


class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("analysis_runs.id"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=True, index=True)
    raw_timestamp = Column(String(100), nullable=True)
    severity = Column(String(20), default="INFO", index=True)  # INFO, WARNING, ERROR, CRITICAL, DEBUG
    service = Column(String(100), default="unknown", index=True)
    message = Column(Text, nullable=False)
    raw_text = Column(Text, nullable=False)
    is_malformed = Column(Boolean, default=False)
    
    # Relationships
    run = relationship("AnalysisRun", back_populates="logs")
    anomaly = relationship("Anomaly", uselist=False, back_populates="log")
    evidence_items = relationship("IncidentEvidence", back_populates="log")


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("analysis_runs.id"), nullable=False, index=True)
    log_id = Column(String(36), ForeignKey("log_entries.id"), nullable=False, index=True)
    anomaly_score = Column(Float, nullable=False)  # Relative within-file score, not a calibrated probability
    is_anomaly = Column(Boolean, default=False)
    detection_time = Column(DateTime, default=datetime.utcnow)
    feature_contributions = Column(JSON, nullable=True)  # Dict of feature names to values/weights
    
    # Relationships
    run = relationship("AnalysisRun", back_populates="anomalies")
    log = relationship("LogEntry", back_populates="anomaly")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("analysis_runs.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    severity = Column(String(20), default="WARNING", index=True)  # CRITICAL, WARNING, INFO
    category = Column(String(50), default="unknown", index=True)  # database, networking, application, resource_exhaustion, unknown
    status = Column(String(50), default="INVESTIGATING")  # INVESTIGATING, CONFIRMED, RESOLVED, MANUAL_REVIEW
    detected_time = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    
    # Relationships
    run = relationship("AnalysisRun", back_populates="incidents")
    evidence = relationship("IncidentEvidence", back_populates="incident", cascade="all, delete-orphan")
    diagnosis = relationship("Diagnosis", uselist=False, back_populates="incident", cascade="all, delete-orphan")


class IncidentEvidence(Base):
    __tablename__ = "incident_evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False, index=True)
    log_id = Column(String(36), ForeignKey("log_entries.id"), nullable=False, index=True)
    evidence_type = Column(String(100), default="supporting_anomaly")  # anomalous_burst, direct_error, cascade_indicator, service_correlation
    description = Column(Text, nullable=True)
    
    # Relationships
    incident = relationship("Incident", back_populates="evidence")
    log = relationship("LogEntry", back_populates="evidence_items")


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False, unique=True, index=True)
    possible_cause = Column(String(255), nullable=False)
    confidence = Column(Float, default=0.0)
    explanation = Column(Text, nullable=False)
    uncertainty = Column(String(255), nullable=True)
    recommended_steps = Column(JSON, default=list)  # list of actionable strings
    raw_jev_response = Column(JSON, nullable=True)
    is_demo_mode = Column(Boolean, default=True)
    
    # Relationships
    incident = relationship("Incident", back_populates="diagnosis")
