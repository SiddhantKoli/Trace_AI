from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Signatures for category categorization heuristics and correlation
CATEGORY_RULES = {
    "database": [
        "postgres", "mysql", "sqlalchemy", "psycopg2", "connection pool",
        "connection slots", "deadlock", "databaseerror", "operationalerror",
        "redis", "mongo", "db", "query timeout", "table lock"
    ],
    "resource_exhaustion": [
        "outofmemory", "heap space", "oom-killer", "gc pause", "garbage collection",
        "sigkill", "cgroup", "high memory", "cpu throttle", "disk full", "thread starvation"
    ],
    "networking": [
        "connecttimeout", "readtimeout", "socket", "circuit breaker", "dns",
        "connection reset", "504 gateway timeout", "packet loss", "handshake latency",
        "network mesh", "egress gateway"
    ],
    "application": [
        "http 500", "internal server error", "nullpointerexception", "keyerror",
        "typeerror", "unhandled exception", "slo limit", "traceback", "runtimeerror"
    ]
}


def infer_preliminary_category(text: str) -> str:
    """Classifies log text against rule-based signatures."""
    lower = text.lower()
    for cat, keywords in CATEGORY_RULES.items():
        if any(kw in lower for kw in keywords):
            return cat
    return "unknown"


class IncidentCorrelator:
    """
    Groups anomalous logs and high-severity events into coherent candidate incidents.
    Applies sliding-window time clustering, service dependency analysis,
    and rule-based pattern correlation.
    
    Adheres strictly to PRD Section 4.4:
    'Temporal order alone must not be treated as proof of causation.'
    """

    def __init__(self, window_seconds: int = 120):
        self.window_seconds = window_seconds

    def correlate(
        self,
        entries: List[Dict[str, Any]],
        anomaly_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Groups candidate anomalies into incidents.
        Returns list of structured incident candidates.
        """
        if not entries:
            return []

        # Identify candidate entries from model evidence. Severity is useful
        # context, but it is not sufficient on its own to create an incident.
        error_times = [
            entry["timestamp"]
            for entry in entries
            if entry["severity"] in ("ERROR", "CRITICAL", "FATAL")
        ]

        def belongs_to_error_burst(entry: Dict[str, Any]) -> bool:
            if entry["severity"] not in ("ERROR", "CRITICAL", "FATAL"):
                return False
            nearby_errors = sum(
                abs((entry["timestamp"] - other_time).total_seconds()) <= 60
                for other_time in error_times
            )
            return nearby_errors >= 2

        candidates = []
        for entry, anom in zip(entries, anomaly_results):
            if anom.get("is_anomaly", False) or belongs_to_error_burst(entry):
                candidates.append({
                    "entry": entry,
                    "anomaly": anom
                })

        if not candidates:
            return []

        # Sort candidates chronologically
        candidates.sort(key=lambda c: c["entry"]["timestamp"])

        # Cluster by sliding temporal window and service/category proximity
        clusters: List[List[Dict[str, Any]]] = []
        current_cluster: List[Dict[str, Any]] = [candidates[0]]

        for cand in candidates[1:]:
            prev_cand = current_cluster[-1]
            time_gap = (cand["entry"]["timestamp"] - prev_cand["entry"]["timestamp"]).total_seconds()
            
            # If within window, check compatibility
            if time_gap <= self.window_seconds:
                current_cluster.append(cand)
            else:
                clusters.append(current_cluster)
                current_cluster = [cand]

        if current_cluster:
            clusters.append(current_cluster)

        # Build candidate incidents from clusters
        incidents = []
        for idx, cluster in enumerate(clusters, start=1):
            if len(cluster) == 0:
                continue

            # A pair of isolated model outliers in otherwise healthy INFO
            # traffic is not enough to call an incident. Require at least one
            # error-level event so the incident represents operational impact.
            if not any(
                c["entry"]["severity"] in ("ERROR", "CRITICAL", "FATAL")
                for c in cluster
            ):
                continue

            # Gather metadata across cluster
            services = sorted(list(set(c["entry"]["service"] for c in cluster)))
            severities = [c["entry"]["severity"] for c in cluster]
            
            # Highest severity
            if "CRITICAL" in severities or "FATAL" in severities:
                incident_severity = "CRITICAL"
            elif "ERROR" in severities:
                incident_severity = "ERROR"
            elif "WARNING" in severities:
                incident_severity = "WARNING"
            else:
                incident_severity = "INFO"

            # Combine message text for category inference
            all_text = " ".join([c["entry"]["message"] for c in cluster])
            category = infer_preliminary_category(all_text)

            first_time = cluster[0]["entry"]["timestamp"]
            last_time = cluster[-1]["entry"]["timestamp"]
            duration = int((last_time - first_time).total_seconds())

            # Title formulation
            primary_service = services[0] if services else "system"
            if category == "database":
                title = f"Database Saturation and Cascade Failures in [{', '.join(services[:2])}]"
            elif category == "resource_exhaustion":
                title = f"Resource Exhaustion & Process Termination in [{primary_service}]"
            elif category == "networking":
                title = f"Network Timeout Cascade across [{', '.join(services[:2])}]"
            elif category == "application":
                title = f"Surge in Application Exceptions in [{primary_service}]"
            else:
                title = f"System Anomalies detected across [{', '.join(services[:3])}]"

            # Evidence logs
            evidence_items = []
            for c in cluster:
                entry = c["entry"]
                anom = c["anomaly"]
                
                # Determine evidence role
                if entry["severity"] in ("CRITICAL", "FATAL"):
                    ev_type = "critical_impact"
                elif anom["anomaly_score"] > 0.8:
                    ev_type = "anomalous_burst"
                elif any(word in entry["message"].lower() for word in ("timeout", "503", "504", "failed")):
                    ev_type = "cascade_indicator"
                else:
                    ev_type = "service_correlation"

                evidence_items.append({
                    "entry": entry,
                    "anomaly": anom,
                    "evidence_type": ev_type,
                    "description": f"Observed in {entry['service']} at {entry['timestamp'].strftime('%H:%M:%S')} (Score: {anom['anomaly_score']})"
                })

            summary = (
                f"Cluster of {len(cluster)} anomalous and high-severity events observed over a {duration}s window "
                f"across service(s): {', '.join(services)}. "
                f"Earliest event recorded at {first_time.strftime('%Y-%m-%d %H:%M:%S')}. "
                f"NOTE: Events are ordered chronologically; correlation indicates temporal grouping, not verified causality."
            )

            incidents.append({
                "cluster_index": idx,
                "title": title,
                "severity": incident_severity,
                "category": category,
                "status": "INVESTIGATING",
                "detected_time": first_time,
                "summary": summary,
                "services": services,
                "evidence_items": evidence_items
            })

        return incidents
