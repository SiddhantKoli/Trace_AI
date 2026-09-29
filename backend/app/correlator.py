import re
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


def _as_service_names(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if item]
    return []


def infer_dependency_graph(entries: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Extract explicit service relationships from structured fields or log text."""
    known_services = {str(entry.get("service", "unknown")) for entry in entries}
    edges = set()
    patterns = (
        r"\bdepends\s+on\s+([A-Za-z0-9_.:-]+)",
        r"\b(?:upstream|downstream|callee|dependency)\s*[:=]\s*([A-Za-z0-9_.:-]+)",
    )

    for entry in entries:
        source = str(entry.get("service", "unknown"))
        explicit_targets: List[str] = []
        for key in ("depends_on", "dependencies", "upstream_service", "downstream_service", "callee_service"):
            explicit_targets.extend(_as_service_names(entry.get(key)))

        message = str(entry.get("message", ""))
        for pattern in patterns:
            explicit_targets.extend(re.findall(pattern, message, flags=re.IGNORECASE))

        for target in explicit_targets:
            target = target.strip("[](){}.,;\"")
            if target in known_services and target != source:
                edges.add((source, target))

    return [{"source": source, "target": target} for source, target in sorted(edges)]


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

        dependency_graph = infer_dependency_graph(entries)
        # Sort candidates chronologically
        candidates.sort(key=lambda c: c["entry"]["timestamp"])

        # Cluster by sliding temporal window and service/category proximity
        clusters: List[List[Dict[str, Any]]] = []
        current_cluster: List[Dict[str, Any]] = [candidates[0]]

        for cand in candidates[1:]:
            prev_cand = current_cluster[-1]
            time_gap = (cand["entry"]["timestamp"] - prev_cand["entry"]["timestamp"]).total_seconds()

            current_services = {item["entry"]["service"] for item in current_cluster}
            current_categories = {
                infer_preliminary_category(item["entry"]["message"])
                for item in current_cluster
            }
            candidate_service = cand["entry"]["service"]
            candidate_category = infer_preliminary_category(cand["entry"]["message"])
            shares_dependency = any(
                (edge["source"] == candidate_service and edge["target"] in current_services)
                or (edge["target"] == candidate_service and edge["source"] in current_services)
                for edge in dependency_graph
            )
            same_signal = (
                candidate_service in current_services
                or (
                    candidate_category != "unknown"
                    and candidate_category in current_categories
                )
                or shares_dependency
            )

            # Time is necessary, but not sufficient, for cross-service grouping.
            # Keep related categories, shared services, or explicit dependencies
            # together; otherwise start a separate incident candidate.
            if time_gap <= self.window_seconds and same_signal:
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
            cluster_services = set(services)
            cluster_dependencies = [
                edge for edge in dependency_graph
                if edge["source"] in cluster_services and edge["target"] in cluster_services
            ]
            dependency_services = {
                service
                for edge in cluster_dependencies
                for service in (edge["source"], edge["target"])
            }
            
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

            # Titles describe observed category and grouping only. They do not
            # imply a cascade unless an explicit dependency edge was observed.
            primary_service = services[0] if services else "system"
            if category == "database":
                title = f"Database-related incident candidate in [{', '.join(services[:2])}]"
            elif category == "resource_exhaustion":
                title = f"Resource exhaustion incident candidate in [{primary_service}]"
            elif category == "networking":
                title = f"Network timeout incident candidate across [{', '.join(services[:2])}]"
            elif category == "application":
                title = f"Application exception incident candidate in [{primary_service}]"
            else:
                title = f"System anomaly incident candidate across [{', '.join(services[:3])}]"

            # Evidence logs
            evidence_items = []
            for c in cluster:
                entry = c["entry"]
                anom = c["anomaly"]
                
                # Determine evidence role
                if entry["service"] in dependency_services:
                    ev_type = "dependency_signal"
                elif entry["severity"] in ("CRITICAL", "FATAL"):
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
                    "description": f"Observed in {entry['service']} at {entry['timestamp'].strftime('%H:%M:%S')} (relative score: {anom['anomaly_score']})"
                })

            dependency_edges_text = ", ".join(
                f"{edge['source']} -> {edge['target']}" for edge in cluster_dependencies
            )
            dependency_note = (
                f"Explicit dependency evidence: {dependency_edges_text}."
                if dependency_edges_text
                else "No explicit service dependency evidence was present; temporal proximity is not verified causality."
            )
            summary = (
                f"Cluster of {len(cluster)} anomalous and high-severity events observed over a {duration}s window "
                f"across service(s): {', '.join(services)}. "
                f"Earliest event recorded at {first_time.strftime('%Y-%m-%d %H:%M:%S')}. "
                f"{dependency_note}"
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
                "dependency_edges": cluster_dependencies,
                "correlation_basis": "explicit_dependency_and_temporal" if cluster_dependencies else "temporal_and_error_burst",
                "evidence_items": evidence_items
            })

        return incidents
