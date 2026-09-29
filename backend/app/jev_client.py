import logging
from typing import Dict, Any, List, Optional
import httpx
from app.config import settings

logger = logging.getLogger("trace_ai.jev")


class JevClient:
    """
    Official integration with TypeSafe AI's Jev model (System One decision primitive).
    Endpoint: POST https://api.typesafe.ai/v1/systemone
    
    Adheres strictly to PRD Section 4.3, Section 8, and Section 15:
    - Never fakes a live API call if credentials are missing
    - Communicates via server-side Bearer token (never exposed to frontend)
    - Sends sanitized, structured incident evidence rather than entire raw files
    - Handles rate limits, timeouts, and network failures gracefully
    - Emits 'Insufficient evidence' if data is ambiguous or scarce
    """

    def __init__(self, api_key: Optional[str] = None, demo_mode: Optional[bool] = None):
        self.api_key = api_key if api_key is not None else settings.JEV_API_KEY
        self.demo_mode = demo_mode if demo_mode is not None else settings.DEMO_MODE
        self.api_url = settings.JEV_API_URL

    def build_structured_evidence(self, incident: Dict[str, Any]) -> str:
        """
        Extracts and formats sanitized evidence items into structured text state.
        Never transmits sensitive credentials or unnecessary file lines.
        """
        evidence_items = incident.get("evidence_items", [])
        services = incident.get("services", [])
        
        lines = [
            f"INCIDENT_SERVICES: {', '.join(services)}",
            f"PRIMARY_CATEGORY_HINT: {incident.get('category', 'unknown')}",
            f"EVENT_COUNT: {len(evidence_items)}",
            "CHRONOLOGICAL_EVIDENCE_SEQUENCE:"
        ]
        
        for idx, item in enumerate(evidence_items[:12], start=1):  # Cap to most relevant 12 items
            entry = item["entry"]
            lines.append(
                f"[{idx}] {entry['timestamp'].strftime('%H:%M:%S')} | "
                f"SVC: {entry['service']} | LEVEL: {entry['severity']} | MSG: {entry['message']}"
            )
            
        return "\n".join(lines)

    async def analyze_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs incident classification, uncertainty estimation, and diagnosis.
        Calls live Jev System One API or returns deterministic demo response.
        """
        evidence_items = incident.get("evidence_items", [])
        
        # PRD Section 8: "If evidence is insufficient, display 'Insufficient evidence' rather than fabricate a diagnosis."
        if len(evidence_items) < 2:
            return {
                "category": "unknown",
                "possible_cause": "Insufficient evidence",
                "confidence": 0.25,
                "explanation": (
                    "Only a single isolated event was detected in this time cluster. "
                    "Insufficient supporting evidence exists to formulate a conclusive diagnosis without further telemetry."
                ),
                "uncertainty": "HIGH: Insufficient corroborating events (requires manual investigation)",
                "recommended_steps": [
                    "Increase log verbosity on affected services",
                    "Verify host resource metrics (CPU, RAM, Disk I/O) at timestamp",
                    "Monitor for recurring occurrences over the next 15 minutes"
                ],
                "is_demo_mode": False,
                "raw_jev_response": {
                    "reason": "insufficient_evidence",
                    "event_count": len(evidence_items)
                }
            }

        structured_state = self.build_structured_evidence(incident)

        # Questions formatted strictly per TypeSafe Jev System One documentation
        questions_payload = {
            "category": {
                "type": "choice",
                "options": ["database", "networking", "application", "resource_exhaustion", "unknown"]
            },
            "severity": {
                "type": "choice",
                "options": ["CRITICAL", "WARNING", "INFO"]
            },
            "requires_immediate_action": {
                "type": "noul"
            },
            "impact_score": {
                "type": "score",
                "scale": [1, 2, 3, 4, 5]
            }
        }

        # Check if live call is viable
        can_call_live = bool(self.api_key and self.api_key.strip() and not self.demo_mode)

        if can_call_live:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key.strip()}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "state": structured_state,
                    "questions": questions_payload
                }
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(self.api_url, json=payload, headers=headers)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        return self._synthesize_live_response(data, incident)
                    elif resp.status_code == 401:
                        logger.error("Jev API returned 401 Unauthorized. Falling back to explicit Demo Mode.")
                    elif resp.status_code == 429:
                        logger.warning("Jev API Rate limit reached (429).")
                    else:
                        logger.error(f"Jev API returned unexpected status {resp.status_code}: {resp.text}")
            except (httpx.TimeoutException, httpx.RequestError) as ex:
                logger.error(f"Failed to communicate with Jev API: {str(ex)}")

        # Fallback to deterministic demo response (clearly labelled)
        return self._generate_deterministic_demo_response(incident)

    def _synthesize_live_response(self, jev_response: Dict[str, Any], incident: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesizes Jev System One answers into human-readable diagnosis."""
        answers = jev_response.get("answers", {})
        
        cat_answer = answers.get("category", {}).get("answer", incident.get("category", "unknown"))
        cat_conf = answers.get("category", {}).get("confidence", 0.75)
        
        sev_answer = answers.get("severity", {}).get("answer", incident.get("severity", "WARNING"))
        sev_conf = answers.get("severity", {}).get("confidence", 0.8)
        
        action_prob = answers.get("requires_immediate_action", {}).get("probability", 0.5)
        impact_score = answers.get("impact_score", {}).get("score", 3)

        combined_conf = round(float((cat_conf + sev_conf) / 2.0), 3)

        explanation = (
            f"TypeSafe Jev System One classified incident under '{cat_answer}' with {round(cat_conf * 100, 1)}% confidence. "
            f"Assessed severity: {sev_answer} (impact scale: {impact_score}/5). "
            f"Probability of immediate operational remediation requirement: {round(action_prob * 100, 1)}%."
        )

        uncertainty_level = "LOW" if combined_conf >= 0.85 else ("MEDIUM" if combined_conf >= 0.65 else "HIGH")
        uncertainty = f"{uncertainty_level} (Calibrated model confidence: {round(combined_conf * 100, 1)}%)"

        steps = self._get_recommended_steps_for_category(cat_answer)

        return {
            "category": str(cat_answer),
            "possible_cause": f"Probable {cat_answer.replace('_', ' ').title()} Anomaly",
            "confidence": combined_conf,
            "explanation": explanation,
            "uncertainty": uncertainty,
            "recommended_steps": steps,
            "is_demo_mode": False,
            "raw_jev_response": jev_response
        }

    def _generate_deterministic_demo_response(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """
        PRD Section 15:
        'If credentials are unavailable, provide a clearly labelled demo mode using deterministic sample responses,
         never fake a successful live API call.'
        """
        category = incident.get("category", "unknown").lower()
        services = incident.get("services", ["system"])
        messages = [
            str(item.get("entry", {}).get("message", "")).strip()
            for item in incident.get("evidence_items", [])
        ]
        observed = [message for message in messages if message][:3]
        evidence_excerpt = "; ".join(observed)
        evidence_count = len([message for message in messages if message])
        confidence = round(min(0.78, 0.42 + min(evidence_count, 6) * 0.05), 2)

        category_labels = {
            "database": "database connection-pool exhaustion pattern",
            "resource_exhaustion": "memory exhaustion pattern",
            "networking": "network timeout and circuit-breaker pattern",
            "application": "application exception and HTTP 5xx pattern",
        }
        cause = f"Observed {category_labels.get(category, 'unclassified system anomaly pattern')}"
        explanation = (
            "[DEMO MODE - EVIDENCE-BASED HEURISTIC] This is a hypothesis derived from the "
            f"{evidence_count} correlated log entries across {len(services)} service(s). "
            f"Observed signals: {evidence_excerpt or 'No readable message evidence'}. "
            "The log evidence does not establish root cause or causality; validate with metrics, traces, and deployment context."
        )
        uncertainty = (
            "MEDIUM: Demo classification is based only on correlated log text and severity; "
            "root cause remains unverified."
        )
        steps = self._get_recommended_steps_for_category(category)

        mock_raw = {
            "mode": "DEMO_MODE",
            "note": "Evidence-based heuristic response for testing without live API keys; not a verified diagnosis",
            "observed_signals": observed,
            "confidence_cap": 0.78,
            "simulated_answers": {
                "category": {"answer": category, "confidence": confidence},
                "severity": {"answer": incident.get("severity", "WARNING"), "confidence": 0.88},
                "requires_immediate_action": {"probability": 0.85 if confidence > 0.8 else 0.4},
                "impact_score": {"score": 5 if incident.get("severity") == "CRITICAL" else 3, "confidence": 0.9}
            }
        }

        return {
            "category": category,
            "possible_cause": cause,
            "confidence": confidence,
            "explanation": explanation,
            "uncertainty": uncertainty,
            "recommended_steps": steps,
            "is_demo_mode": True,
            "raw_jev_response": mock_raw
        }

    def _get_recommended_steps_for_category(self, category: str) -> List[str]:
        cat = category.lower()
        if "database" in cat:
            return [
                "Review active connection metrics in database management console",
                "Check for long-running uncommitted transactions or lock contention",
                "Inspect connection pool sizing in application configuration"
            ]
        elif "resource" in cat:
            return [
                "Review host memory and CPU utilization graphs",
                "Analyze memory heap dump or CPU profiling flamegraphs",
                "Consider increasing pod/process memory allocation"
            ]
        elif "network" in cat:
            return [
                "Verify DNS resolution and network routing tables",
                "Check external vendor endpoint latency and status pages",
                "Inspect firewall rules and egress NAT limits"
            ]
        else:
            return [
                "Check application stack trace in logs",
                "Verify recent deployment or configuration changes",
                "Inspect service dependencies for error propagation"
            ]


# Singleton instance
jev_client = JevClient()
