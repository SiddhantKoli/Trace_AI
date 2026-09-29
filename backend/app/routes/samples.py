import os
from typing import List, Dict, Any
from fastapi import APIRouter

router = APIRouter(prefix="/samples", tags=["Sample Logs"])

SAMPLES_CATALOG = [
    {
        "id": "database",
        "title": "Database Connection Pool Exhaustion",
        "category": "database",
        "description": "High connection pool utilization leading to slots exhaustion, 503 cascades in checkout and payment.",
        "filename": "database_connection_exhaustion.log",
        "recommended_for": "Verifying database cascade detection and Jev pool starvation classification"
    },
    {
        "id": "http_500",
        "title": "Repeated HTTP 500 Error Surge",
        "category": "application",
        "description": "Canary deployment bug (KeyError: 'user_preferences') triggering 5.8% SLO error breach.",
        "filename": "http_500_cluster.log",
        "recommended_for": "Testing application-level exception clustering and rapid incident formulation"
    },
    {
        "id": "memory",
        "title": "High Memory Usage & Linux OOM Killer",
        "category": "resource_exhaustion",
        "description": "Buffer bloat during parquet ingestion, GC stop-the-world spikes, Java heap exhaustion, and SIGKILL 137.",
        "filename": "high_memory_oom.log",
        "recommended_for": "Evaluating resource exhaustion isolation and container memory leak diagnosis"
    },
    {
        "id": "network",
        "title": "Network Timeout & Circuit Breaker Cascade",
        "category": "networking",
        "description": "TCP handshake latency to external acquirer, connect timeouts, circuit breaker trip, and 504 gateway timeout.",
        "filename": "network_timeout_cascade.log",
        "recommended_for": "Evaluating cascading dependency failures and timeout sequence mapping"
    },
    {
        "id": "baseline",
        "title": "Normal Activity Baseline (No Incidents)",
        "category": "baseline",
        "description": "Routine health checks, cache hits, successful order checkouts, and periodic heartbeats.",
        "filename": "normal_activity_baseline.log",
        "recommended_for": "Testing false positive suppression and healthy state validation"
    },
    {
        "id": "malformed",
        "title": "Mixed Malformed & Corrupted Logs",
        "category": "parser_testing",
        "description": "Missing timestamps, binary bytes, corrupted text lines mixed with valid structured events.",
        "filename": "mixed_malformed_sample.log",
        "recommended_for": "Testing parser resilience, error recovery, and parsed vs rejected accounting"
    }
]


@router.get("", response_model=List[Dict[str, Any]])
def list_sample_logs():
    """Returns curated catalogue of labelled sample logs."""
    return SAMPLES_CATALOG
