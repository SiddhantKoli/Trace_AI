import pytest
from datetime import datetime, timedelta
from app.anomaly_detector import AnomalyDetector


def test_anomaly_detector_feature_extraction():
    detector = AnomalyDetector(contamination=0.1)
    base_time = datetime(2026, 9, 29, 14, 0, 0)
    
    entries = [
        {
            "line_number": 1,
            "timestamp": base_time,
            "severity": "INFO",
            "service": "auth-service",
            "message": "User login success",
            "raw_text": "log1",
            "is_malformed": False
        },
        {
            "line_number": 2,
            "timestamp": base_time + timedelta(seconds=2),
            "severity": "CRITICAL",
            "service": "auth-service",
            "message": "Database pool exhausted, fatal connection error",
            "raw_text": "log2",
            "is_malformed": False
        }
    ]

    features_df = detector.extract_features(entries)
    assert not features_df.empty
    assert "severity_weight" in features_df.columns
    assert "rolling_count_60s" in features_df.columns
    assert "time_delta_prev" in features_df.columns
    assert features_df.loc[1, "severity_weight"] == 1.0


def test_anomaly_detector_scoring():
    detector = AnomalyDetector(contamination=0.1)
    base_time = datetime(2026, 9, 29, 14, 0, 0)
    
    # Create 20 baseline INFO logs followed by 3 CRITICAL errors
    entries = []
    for i in range(20):
        entries.append({
            "line_number": i + 1,
            "timestamp": base_time + timedelta(seconds=i * 2),
            "severity": "INFO",
            "service": "web-server",
            "message": f"Processed request {i}",
            "raw_text": f"raw {i}",
            "is_malformed": False
        })

    for i in range(3):
        entries.append({
            "line_number": 21 + i,
            "timestamp": base_time + timedelta(seconds=42 + i),
            "severity": "CRITICAL",
            "service": "database",
            "message": f"Connection pool exhausted critical failure {i}",
            "raw_text": f"crit {i}",
            "is_malformed": False
        })

    results = detector.detect(entries)
    assert len(results) == len(entries)
    
    # The model should identify at least some of the distinct critical events,
    # without forcing every high-severity row to be anomalous.
    crit_scores = [r["anomaly_score"] for r in results[20:]]
    info_scores = [r["anomaly_score"] for r in results[:10]]
    
    assert sum(r["is_anomaly"] for r in results[20:]) >= 2
    assert sum(r["is_anomaly"] for r in results[20:]) < len(results[20:])
    assert max(crit_scores) > max(info_scores)
    assert "primary_driver" in results[20]["feature_contributions"]
