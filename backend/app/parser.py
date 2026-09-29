import re
import csv
import json
from io import StringIO
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional

# Regular expressions for log formats
ISO_TS_PATTERN = r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
SEVERITY_PATTERN = r"\b(CRITICAL|FATAL|ERROR|WARN(?:ING)?|INFO|DEBUG|TRACE)\b"
BRACKET_SERVICE_PATTERN = r"\[([a-zA-Z0-9_\-\.]+)\]"

# Common timestamp formats
TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S,%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
    "%d/%b/%Y:%H:%M:%S %z",
    "%b %d %H:%M:%S",
]

# Sensitive patterns for redaction
REDACTION_PATTERNS = [
    (re.compile(r"(bearer\s+)[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"(api[_-]?key[\s:=]+)[a-zA-Z0-9_\-]{16,}", re.IGNORECASE), r"\1[REDACTED_API_KEY]"),
    (re.compile(r"(password[\s:=]+)[^\s,;]+", re.IGNORECASE), r"\1[REDACTED_PASSWORD]"),
    (re.compile(r"(secret[\s:=]+)[^\s,;]+", re.IGNORECASE), r"\1[REDACTED_SECRET]"),
    (re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"), "[REDACTED_CARD]"),
]


def sanitize_message(text: str) -> str:
    """Sanitizes sensitive patterns from log text before external processing."""
    sanitized = text
    for pattern, replacement in REDACTION_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def _as_utc_naive(value: datetime) -> datetime:
    """Store timestamps as UTC without tzinfo for SQLite compatibility."""
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse a timestamp and normalize offset-bearing values to UTC."""
    clean_ts = ts_str.strip()
    for fmt in TIMESTAMP_FORMATS:
        try:
            return _as_utc_naive(datetime.strptime(clean_ts, fmt))
        except ValueError:
            continue
    # Try ISO fromisoformat for modern python
    try:
        # replace Z with +00:00 for fromisoformat
        if clean_ts.endswith("Z"):
            clean_ts = clean_ts[:-1] + "+00:00"
        return _as_utc_naive(datetime.fromisoformat(clean_ts))
    except Exception:
        pass
    return None


def normalize_severity(severity_str: Optional[str]) -> str:
    """Normalizes various log severity representations."""
    if not severity_str:
        return "INFO"
    s = severity_str.strip().upper()
    if s in ("CRITICAL", "FATAL"):
        return "CRITICAL"
    if s in ("ERROR", "ERR"):
        return "ERROR"
    if s in ("WARN", "WARNING"):
        return "WARNING"
    if s in ("INFO", "NOTICE"):
        return "INFO"
    if s in ("DEBUG", "TRACE"):
        return "DEBUG"
    return "INFO"


class LogParser:
    """
    Robust log file parser supporting .log, .txt, and .csv formats.
    Extracts timestamps, severity levels, service names, and clean messages.
    Tracks parsed vs rejected/malformed counts.
    """

    def parse_csv_content(self, content: str) -> Tuple[List[Dict[str, Any]], int, int]:
        parsed_entries = []
        rejected_count = 0
        reader = csv.reader(StringIO(content))
        rows = list(reader)
        if not rows:
            return [], 0, 0

        header = [h.strip().lower() for h in rows[0]]
        
        # Identify columns
        ts_idx = -1
        sev_idx = -1
        service_idx = -1
        msg_idx = -1

        for i, col in enumerate(header):
            if any(k in col for k in ("time", "date", "ts", "@timestamp")):
                ts_idx = i
            elif any(k in col for k in ("level", "severity", "priority")):
                sev_idx = i
            elif any(k in col for k in ("service", "app", "logger", "source", "host", "component")):
                service_idx = i
            elif any(k in col for k in ("message", "msg", "log", "text", "body")):
                msg_idx = i

        data_rows = rows[1:] if (ts_idx != -1 or msg_idx != -1) else rows

        for line_num, row in enumerate(data_rows, start=1):
            if not row or not any(field.strip() for field in row):
                continue
            try:
                raw_text = ",".join(row)
                raw_ts = row[ts_idx].strip() if (ts_idx != -1 and ts_idx < len(row)) else None
                parsed_ts = parse_timestamp(raw_ts) if raw_ts else None
                
                sev = normalize_severity(row[sev_idx] if (sev_idx != -1 and sev_idx < len(row)) else "INFO")
                service = row[service_idx].strip() if (service_idx != -1 and service_idx < len(row)) else "system"
                msg = row[msg_idx].strip() if (msg_idx != -1 and msg_idx < len(row)) else raw_text
                
                is_malformed = parsed_ts is None and len(msg) < 5
                if is_malformed:
                    rejected_count += 1
                
                parsed_entries.append({
                    "line_number": line_num,
                    "timestamp": parsed_ts or datetime.utcnow(),
                    "raw_timestamp": raw_ts,
                    "severity": sev,
                    "service": service,
                    "message": sanitize_message(msg),
                    "raw_text": raw_text,
                    "is_malformed": is_malformed
                })
            except Exception:
                rejected_count += 1
                parsed_entries.append({
                    "line_number": line_num,
                    "timestamp": datetime.utcnow(),
                    "raw_timestamp": None,
                    "severity": "WARNING",
                    "service": "parser",
                    "message": "Malformed CSV row",
                    "raw_text": str(row),
                    "is_malformed": True
                })

        parsed_count = len([e for e in parsed_entries if not e["is_malformed"]])
        return parsed_entries, parsed_count, rejected_count

    def parse_json_line(self, line: str, line_num: int) -> Optional[Dict[str, Any]]:
        """Attempt parsing line as JSON structured log."""
        try:
            data = json.loads(line)
            if isinstance(data, dict):
                raw_ts = data.get("timestamp") or data.get("time") or data.get("@timestamp") or data.get("date")
                parsed_ts = parse_timestamp(str(raw_ts)) if raw_ts else None
                sev = normalize_severity(data.get("level") or data.get("severity") or data.get("status"))
                service = data.get("service") or data.get("app") or data.get("component") or "system"
                msg = data.get("message") or data.get("msg") or data.get("error") or json.dumps(data)
                
                return {
                    "line_number": line_num,
                    "timestamp": parsed_ts or datetime.utcnow(),
                    "raw_timestamp": str(raw_ts) if raw_ts else None,
                    "severity": sev,
                    "service": str(service),
                    "message": sanitize_message(str(msg)),
                    "raw_text": line,
                    "is_malformed": False
                }
        except Exception:
            pass
        return None

    def parse_text_line(self, line: str, line_num: int) -> Dict[str, Any]:
        """Parses a text line using regex heuristics."""
        stripped = line.strip()
        if not stripped:
            return {
                "line_number": line_num,
                "timestamp": datetime.utcnow(),
                "raw_timestamp": None,
                "severity": "INFO",
                "service": "system",
                "message": "[Empty line]",
                "raw_text": line,
                "is_malformed": True
            }

        # First try JSON
        if stripped.startswith("{") and stripped.endswith("}"):
            json_entry = self.parse_json_line(stripped, line_num)
            if json_entry:
                return json_entry

        # Try regex extraction
        # Example: 2026-09-29 14:00:01.120 [INFO] [order-service] Processed order ...
        ts_match = re.search(ISO_TS_PATTERN, stripped)
        sev_match = re.search(SEVERITY_PATTERN, stripped, re.IGNORECASE)
        bracket_matches = re.findall(BRACKET_SERVICE_PATTERN, stripped)

        parsed_ts = None
        raw_ts = None
        if ts_match:
            raw_ts = ts_match.group(1)
            parsed_ts = parse_timestamp(raw_ts)

        severity = "INFO"
        if sev_match:
            severity = normalize_severity(sev_match.group(1))

        service = "system"
        if bracket_matches:
            # Check if one of brackets is severity, pick the other as service
            for b in bracket_matches:
                if b.upper() not in ("INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "DEBUG", "TRACE"):
                    service = b
                    break

        # Extract message body
        msg = stripped
        if ts_match:
            msg = msg.replace(ts_match.group(0), "", 1).strip()
        for b in bracket_matches:
            msg = msg.replace(f"[{b}]", "", 1).strip()
        # Remove standalone severity token if remaining
        msg = re.sub(rf"^\s*{SEVERITY_PATTERN}\s*[:-]?\s*", "", msg, flags=re.IGNORECASE).strip()
        if not msg:
            msg = stripped

        is_malformed = (parsed_ts is None and not sev_match)

        return {
            "line_number": line_num,
            "timestamp": parsed_ts or datetime.utcnow(),
            "raw_timestamp": raw_ts,
            "severity": severity,
            "service": service,
            "message": sanitize_message(msg),
            "raw_text": line,
            "is_malformed": is_malformed
        }

    def parse(self, content: str, filename: str) -> Tuple[List[Dict[str, Any]], int, int]:
        """
        Main parse method. Returns (entries, parsed_count, rejected_count).
        """
        if filename.lower().endswith(".csv"):
            return self.parse_csv_content(content)

        lines = content.splitlines()
        entries = []
        parsed_count = 0
        rejected_count = 0

        for idx, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            entry = self.parse_text_line(line, idx)
            entries.append(entry)
            if entry["is_malformed"]:
                rejected_count += 1
            else:
                parsed_count += 1

        return entries, parsed_count, rejected_count
