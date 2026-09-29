import pytest
from datetime import datetime, timedelta
from app.correlator import IncidentCorrelator, infer_preliminary_category


def test_infer_preliminary_category():
    assert infer_preliminary_category("psycopg2.OperationalError: connection pool exhausted") == "database"
    assert infer_preliminary_category("java.lang.OutOfMemoryError: Java heap space killed") == "resource_exhaustion"
    assert infer_preliminary_category("ConnectTimeoutError: connection timed out after 5000ms") == "networking"
    assert infer_preliminary_category("Unhandled KeyError: 'user_preferences' 500") == "application"


def test_correlator_window_clustering():
    correlator = IncidentCorrelator(window_seconds=60)
    base_time = datetime(2026, 9, 29, 14, 0, 0)
    
    entries = [
        # Cluster 1: Database errors at 14:00:00
        {
            "line_number": 1,
            "timestamp": base_time,
            "severity": "CRITICAL",
            "service": "postgres",
            "message": "connection slots exhausted",
            "raw_text": "log1"
        },
        {
            "line_number": 2,
            "timestamp": base_time + timedelta(seconds=10),
            "severity": "ERROR",
            "service": "order-service",
            "message": "connection pool timeout",
            "raw_text": "log2"
        },
        # Cluster 2: Network timeout at 14:15:00 (15 minutes later)
        {
            "line_number": 3,
            "timestamp": base_time + timedelta(minutes=15),
            "severity": "CRITICAL",
            "service": "payment-gateway",
            "message": "ConnectTimeoutError: connection timed out to external acquirer",
            "raw_text": "log3"
        }
    ]

    anomaly_results = [
        {"is_anomaly": True, "anomaly_score": 0.95},
        {"is_anomaly": True, "anomaly_score": 0.88},
        {"is_anomaly": True, "anomaly_score": 0.92}
    ]

    incidents = correlator.correlate(entries, anomaly_results)
    # Should produce 2 distinct clusters based on time gap > 60s
    assert len(incidents) == 2
    
    assert incidents[0]["category"] == "database"
    assert len(incidents[0]["evidence_items"]) == 2
    assert "postgres" in incidents[0]["services"]
    
    assert incidents[1]["category"] == "networking"
    assert len(incidents[1]["evidence_items"]) == 1
    
    # Check causation disclaimer presence
    assert "not verified causality" in incidents[0]["summary"]


def test_correlator_reports_explicit_dependency_without_claiming_cascade():
    correlator = IncidentCorrelator(window_seconds=60)
    base_time = datetime(2026, 9, 29, 14, 0, 0)
    entries = [
        {
            "line_number": 1,
            "timestamp": base_time,
            "severity": "ERROR",
            "service": "order-service",
            "message": "depends on postgres connection pool",
            "depends_on": ["postgres"],
            "raw_text": "log1",
        },
        {
            "line_number": 2,
            "timestamp": base_time + timedelta(seconds=5),
            "severity": "ERROR",
            "service": "postgres",
            "message": "connection slots exhausted",
            "raw_text": "log2",
        },
    ]

    incidents = correlator.correlate(
        entries,
        [{"is_anomaly": True, "anomaly_score": 0.9}] * 2,
    )

    assert len(incidents) == 1
    assert incidents[0]["dependency_edges"] == [{"source": "order-service", "target": "postgres"}]
    assert incidents[0]["correlation_basis"] == "explicit_dependency_and_temporal"
    assert "cascade" not in incidents[0]["title"].lower()


def test_correlator_does_not_merge_unrelated_categories_by_time_alone():
    correlator = IncidentCorrelator(window_seconds=60)
    base_time = datetime(2026, 9, 29, 14, 0, 0)
    entries = [
        {
            "line_number": 1,
            "timestamp": base_time,
            "severity": "ERROR",
            "service": "postgres",
            "message": "connection slots exhausted",
            "raw_text": "log1",
        },
        {
            "line_number": 2,
            "timestamp": base_time + timedelta(seconds=5),
            "severity": "ERROR",
            "service": "payment-gateway",
            "message": "ConnectTimeoutError to external acquirer",
            "raw_text": "log2",
        },
    ]

    incidents = correlator.correlate(
        entries,
        [{"is_anomaly": True, "anomaly_score": 0.9}] * 2,
    )

    assert len(incidents) == 2


def test_correlator_keeps_different_same_service_signatures_separate():
    correlator = IncidentCorrelator(window_seconds=60)
    base_time = datetime(2026, 9, 29, 14, 0, 0)
    entries = [
        {
            "line_number": 1,
            "timestamp": base_time,
            "severity": "ERROR",
            "service": "auth-service",
            "message": "Failed login for user 42",
            "raw_text": "log1",
        },
        {
            "line_number": 2,
            "timestamp": base_time + timedelta(seconds=2),
            "severity": "ERROR",
            "service": "auth-service",
            "message": "Account locked after too many login attempts",
            "raw_text": "log2",
        },
    ]

    incidents = correlator.correlate(
        entries,
        [{"is_anomaly": True, "anomaly_score": 0.9}] * 2,
    )

    assert len(incidents) == 2
    assert {incident["event_signatures"][0] for incident in incidents} == {
        "authentication_failure",
        "account_lockout",
    }
