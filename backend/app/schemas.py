from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# Log Schemas
class LogEntryBase(BaseModel):
    line_number: int
    timestamp: Optional[datetime] = None
    raw_timestamp: Optional[str] = None
    severity: str
    service: str
    message: str
    is_malformed: bool = False


class LogEntryOut(LogEntryBase):
    id: str
    run_id: str
    raw_text: str

    class Config:
        from_attributes = True


# Anomaly Schemas
class AnomalyOut(BaseModel):
    id: str
    run_id: str
    log_id: str
    anomaly_score: float
    is_anomaly: bool
    detection_time: datetime
    feature_contributions: Optional[Dict[str, Any]] = None
    log: Optional[LogEntryOut] = None

    class Config:
        from_attributes = True


# Diagnosis Schemas
class DiagnosisOut(BaseModel):
    id: str
    incident_id: str
    possible_cause: str
    confidence: float
    explanation: str
    uncertainty: Optional[str] = None
    recommended_steps: List[str] = []
    is_demo_mode: bool = True
    raw_jev_response: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Evidence Schemas
class IncidentEvidenceOut(BaseModel):
    id: str
    incident_id: str
    log_id: str
    evidence_type: str
    description: Optional[str] = None
    log: Optional[LogEntryOut] = None

    class Config:
        from_attributes = True


# Incident Schemas
class IncidentOut(BaseModel):
    id: str
    run_id: str
    title: str
    severity: str
    category: str
    status: str
    detected_time: datetime
    summary: Optional[str] = None
    confidence: float = 0.0
    evidence: List[IncidentEvidenceOut] = []
    diagnosis: Optional[DiagnosisOut] = None

    class Config:
        from_attributes = True


class IncidentUpdate(BaseModel):
    status: Optional[str] = None


# Analysis Run Schemas
class AnalysisRunOut(BaseModel):
    id: str
    filename: str
    file_size_bytes: int
    status: str
    data_mode: str = "real"
    error_message: Optional[str] = None
    total_entries: int
    parsed_count: int
    rejected_count: int
    anomaly_count: int
    incident_count: int
    start_time: datetime
    completion_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisRunDetail(AnalysisRunOut):
    incidents: List[IncidentOut] = []
    anomalies: List[AnomalyOut] = []

    class Config:
        from_attributes = True


# Dashboard Statistics Schema
class DashboardStats(BaseModel):
    total_entries_analysed: int
    total_anomalies_detected: int
    total_incidents_identified: int
    severity_distribution: Dict[str, int]
    category_distribution: Dict[str, int]
    error_frequency_timeline: List[Dict[str, Any]]
    recent_incidents: List[IncidentOut]
    latest_run_id: Optional[str] = None


# Settings Schema
class SettingsOut(BaseModel):
    jev_api_key_configured: bool
    jev_api_key_masked: str
    jev_api_url: str
    demo_mode: bool
    default_contamination: float
    default_correlation_window_seconds: int
    max_file_size_mb: int


class SettingsUpdate(BaseModel):
    jev_api_key: Optional[str] = None
    demo_mode: Optional[bool] = None
    default_contamination: Optional[float] = None
    default_correlation_window_seconds: Optional[int] = None


# Evaluation Schema
class EvaluationMetricResult(BaseModel):
    scenario_name: str
    total_logs: int
    true_anomalies: int
    detected_anomalies: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    diagnosis_match: bool
    predicted_category: str
    expected_category: str
    diagnosis_confidence: float
    details: str


class EvaluationSummary(BaseModel):
    overall_precision: float
    overall_recall: float
    overall_f1: float
    overall_false_positive_rate: float
    diagnosis_accuracy: float
    scenario_results: List[EvaluationMetricResult]
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
