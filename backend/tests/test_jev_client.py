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
    assert "DEMO MODE - EVIDENCE-BASED HEURISTIC" in result["explanation"]
    assert "connection-pool exhaustion pattern" in result["possible_cause"]
    assert result["confidence"] <= 0.78
    assert "root cause" in result["explanation"]
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


def test_jev_client_rejects_malformed_live_response():
    client = JevClient(demo_mode=False, api_key="test-key")
    result = client._synthesize_live_response(
        {"answers": {"category": {"answer": "database"}}},
        {"category": "database"},
    )

    assert result["category"] == "unknown"
    assert result["confidence"] == 0.0
    assert "could not be validated" in result["explanation"]
    assert "manual review required" in result["uncertainty"]


def test_jev_client_labels_live_confidence_as_uncalibrated():
    client = JevClient(demo_mode=False, api_key="test-key")
    result = client._synthesize_live_response(
        {
            "answers": {
                "category": {"answer": "database", "confidence": 0.91},
                "severity": {"answer": "WARNING", "confidence": 0.63},
                "requires_immediate_action": {"probability": 0.7},
                "impact_score": {"score": 4},
            }
        },
        {"category": "database"},
    )

    assert result["confidence"] == 0.91
    assert "not calibrated" in result["uncertainty"]
