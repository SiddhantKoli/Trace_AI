import pytest
from datetime import datetime
from app.jev_client import JevClient


@pytest.mark.asyncio
async def test_jev_client_insufficient_evidence():
    # If fewer than 2 evidence items, client must return "Insufficient evidence"
    client = JevClient(demo_mode=True)
    sparse_incident = {
        "title": "Single isolated ping",
        "category": "unknown",
        "severity": "WARNING",
        "services": ["edge"],
        "evidence_items": [
            {
                "entry": {
                    "line_number": 1,
                    "timestamp": datetime(2026, 9, 29, 14, 0, 0),
                    "service": "edge",
                    "severity": "WARNING",
                    "message": "Transient glitch"
                },
                "anomaly": {"anomaly_score": 0.65}
            }
        ]
    }

    result = await client.analyze_incident(sparse_incident)
    assert result["possible_cause"] == "Insufficient evidence"
    assert result["confidence"] <= 0.3
    assert "Insufficient" in result["uncertainty"]


@pytest.mark.asyncio
async def test_jev_client_demo_mode_deterministic():
    client = JevClient(demo_mode=True)
    db_incident = {
        "title": "Database Saturation",
        "category": "database",
        "severity": "CRITICAL",
        "services": ["postgres-primary", "order-service"],
        "evidence_items": [
            {
                "entry": {
                    "line_number": 1,
                    "timestamp": datetime(2026, 9, 29, 14, 0, 0),
                    "service": "postgres-primary",
                    "severity": "CRITICAL",
                    "message": "FATAL: remaining connection slots are reserved"
                },
                "anomaly": {"anomaly_score": 0.95}
            },
            {
                "entry": {
                    "line_number": 2,
                    "timestamp": datetime(2026, 9, 29, 14, 0, 2),
                    "service": "order-service",
                    "severity": "ERROR",
                    "message": "connection pool exhausted"
                },
                "anomaly": {"anomaly_score": 0.90}
            }
        ]
    }

    result = await client.analyze_incident(db_incident)
    assert result["is_demo_mode"] is True
    assert "DEMO MODE - DETERMINISTIC MOCK" in result["explanation"]
    assert "Connection Pool" in result["possible_cause"]
    assert result["confidence"] >= 0.9
    assert len(result["recommended_steps"]) > 0


def test_jev_client_evidence_sanitization():
    client = JevClient(demo_mode=True)
    incident = {
        "title": "Test",
        "category": "database",
        "services": ["auth"],
        "evidence_items": [
            {
                "entry": {
                    "timestamp": datetime(2026, 9, 29, 14, 0, 0),
                    "service": "auth",
                    "severity": "ERROR",
                    "message": "DB error with bearer [REDACTED_TOKEN]"
                }
            },
            {
                "entry": {
                    "timestamp": datetime(2026, 9, 29, 14, 0, 1),
                    "service": "auth",
                    "severity": "CRITICAL",
                    "message": "DB fail"
                }
            }
        ]
    }
    structured = client.build_structured_evidence(incident)
    assert "INCIDENT_SERVICES: auth" in structured
    assert "CHRONOLOGICAL_EVIDENCE_SEQUENCE:" in structured
