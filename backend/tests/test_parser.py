import pytest
from datetime import datetime
from app.parser import LogParser, sanitize_message, parse_timestamp, normalize_severity


def test_sanitize_message():
    raw = "User auth with bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 and password=SuperSecretPassword123"
    sanitized = sanitize_message(raw)
    assert "[REDACTED_TOKEN]" in sanitized
    assert "[REDACTED_PASSWORD]" in sanitized
    assert "SuperSecretPassword123" not in sanitized


def test_normalize_severity():
    assert normalize_severity("fatal") == "CRITICAL"
    assert normalize_severity("error") == "ERROR"
    assert normalize_severity("warn") == "WARNING"
    assert normalize_severity("warning") == "WARNING"
    assert normalize_severity("info") == "INFO"
    assert normalize_severity("debug") == "DEBUG"
    assert normalize_severity("unknown") == "INFO"


def test_parse_standard_text_logs():
    parser = LogParser()
    content = """
2026-09-29 14:00:01.120 [INFO] [order-service] Processed order #10492 successfully
2026-09-29 14:00:20.100 [WARNING] [postgres-primary] Active connection count reached 92/100
2026-09-29 14:00:28.900 [ERROR] [postgres-primary] FATAL: remaining connection slots are reserved
    """
    entries, parsed_count, rejected_count = parser.parse(content, "test.log")
    
    assert parsed_count == 3
    assert rejected_count == 0
    assert len(entries) == 3
    
    assert entries[0]["service"] == "order-service"
    assert entries[0]["severity"] == "INFO"
    assert "Processed order" in entries[0]["message"]
    
    assert entries[2]["service"] == "postgres-primary"
    assert entries[2]["severity"] in ("ERROR", "CRITICAL")
    assert "connection slots" in entries[2]["message"]


def test_parse_csv_logs():
    parser = LogParser()
    csv_content = """timestamp,level,service,message
2026-09-29 14:00:01,INFO,order-service,Order created
2026-09-29 14:00:05,ERROR,payment-service,Payment gateway timed out
"""
    entries, parsed_count, rejected_count = parser.parse(csv_content, "test.csv")
    assert parsed_count == 2
    assert rejected_count == 0
    assert entries[1]["severity"] == "ERROR"
    assert entries[1]["service"] == "payment-service"


def test_malformed_log_handling():
    parser = LogParser()
    mixed_content = """
2026-09-29 14:00:01 [INFO] [web] Valid entry
GARBAGE_UNPARSEABLE_LINE_CORRUPTED
2026-09-29 14:00:05 [ERROR] [api] Another valid entry
"""
    entries, parsed_count, rejected_count = parser.parse(mixed_content, "mixed.log")
    assert parsed_count == 2
    assert rejected_count == 1
    assert any(e["is_malformed"] for e in entries)
