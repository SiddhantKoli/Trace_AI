import os
from typing import Dict, Any, List
from datetime import datetime

from app.parser import LogParser
from app.anomaly_detector import AnomalyDetector
from app.correlator import IncidentCorrelator
from app.jev_client import JevClient
from app.schemas import EvaluationMetricResult, EvaluationSummary

BASE_SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data")

SCENARIO_CONFIGS = [
    {
        "filename": "database_connection_exhaustion.log",
        "name": "Database Connection Pool Exhaustion",
        "expected_category": "database",
        "true_anomaly_lines": list(range(7, 21)),
    },
    {
        "filename": "http_500_cluster.log",
        "name": "Repeated HTTP 500 Error Surge",
        "expected_category": "application",
        "true_anomaly_lines": list(range(4, 16)),
    },
    {
        "filename": "high_memory_oom.log",
        "name": "High Memory Usage & OOM Killer",
        "expected_category": "resource_exhaustion",
        "true_anomaly_lines": list(range(3, 12)),
    },
    {
        "filename": "network_timeout_cascade.log",
        "name": "Network Timeout & Circuit Breaker Cascade",
        "expected_category": "networking",
        "true_anomaly_lines": list(range(3, 12)),
    },
    {
        "filename": "normal_activity_baseline.log",
        "name": "Normal Baseline Operational Activity",
        "expected_category": "unknown",
        "true_anomaly_lines": [],
    }
]


class BenchmarkEvaluator:
    """
    Evaluates ML anomaly detection and Jev incident classification
    against ground truth benchmark scenarios.
    
    Adheres strictly to PRD Section 12 & Section 15:
    'Calculate all evaluation scores from actual test results.
     Evaluate anomaly detection separately from Jev incident classification.
     Do not hardcode or claim unverified scores.'
    """

    def __init__(self):
        self.parser = LogParser()
        self.detector = AnomalyDetector(contamination=0.08)
        self.correlator = IncidentCorrelator(window_seconds=120)
        self.jev = JevClient()

    async def run_evaluation(self) -> EvaluationSummary:
        scenario_results: List[EvaluationMetricResult] = []

        total_tp = 0
        total_fp = 0
        total_fn = 0
        total_tn = 0
        correct_diagnoses = 0
        total_evaluable_diagnoses = 0

        for config in SCENARIO_CONFIGS:
            filepath = os.path.join(BASE_SAMPLE_DIR, config["filename"])
            if not os.path.exists(filepath):
                continue

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            entries, parsed_count, rejected_count = self.parser.parse(content, config["filename"])
            anomalies = self.detector.detect(entries)

            # Ground truth is an independent, reviewed annotation of the
            # benchmark fixture, never inferred from the detector's features
            # or from severity alone.
            true_anomaly_lines = set(config["true_anomaly_lines"])

            tp = 0
            fp = 0
            fn = 0
            tn = 0

            for entry, anom in zip(entries, anomalies):
                is_true_anom = entry["line_number"] in true_anomaly_lines
                is_predicted_anom = bool(anom["is_anomaly"])

                if is_predicted_anom and is_true_anom:
                    tp += 1
                elif is_predicted_anom and not is_true_anom:
                    fp += 1
                elif not is_predicted_anom and is_true_anom:
                    fn += 1
                else:
                    tn += 1

            total_tp += tp
            total_fp += fp
            total_fn += fn
            total_tn += tn

            precision = float(tp / (tp + fp)) if (tp + fp) > 0 else (1.0 if (tp + fn) == 0 else 0.0)
            recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 1.0
            f1 = float(2 * (precision * recall) / (precision + recall)) if (precision + recall) > 0 else 0.0
            fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

            # Run Correlation & Jev diagnosis evaluation
            incidents = self.correlator.correlate(entries, anomalies)
            
            predicted_cat = "unknown"
            diag_conf = 0.0
            diag_match = False

            if incidents:
                primary_inc = incidents[0]
                diag_res = await self.jev.analyze_incident(primary_inc)
                predicted_cat = diag_res.get("category", "unknown")
                diag_conf = diag_res.get("confidence", 0.0)
                
                if config["expected_category"] != "unknown":
                    total_evaluable_diagnoses += 1
                    if predicted_cat.lower() == config["expected_category"].lower():
                        diag_match = True
                        correct_diagnoses += 1
            else:
                # No incident detected (expected for normal baseline)
                if config["expected_category"] == "unknown":
                    diag_match = True
                    predicted_cat = "none"

            scenario_results.append(EvaluationMetricResult(
                scenario_name=config["name"],
                total_logs=len(entries),
                true_anomalies=tp + fn,
                detected_anomalies=tp + fp,
                true_positives=tp,
                false_positives=fp,
                false_negatives=fn,
                precision=round(precision, 4),
                recall=round(recall, 4),
                f1_score=round(f1, 4),
                false_positive_rate=round(fpr, 4),
                diagnosis_match=diag_match,
                predicted_category=predicted_cat,
                expected_category=config["expected_category"],
                diagnosis_confidence=round(diag_conf, 3),
                details=(
                    f"TP: {tp}, FP: {fp}, FN: {fn}, TN: {tn}; "
                    f"ground truth lines: {sorted(true_anomaly_lines)}"
                )
            ))

        # Overall summary calculations
        overall_prec = float(total_tp / (total_tp + total_fp)) if (total_tp + total_fp) > 0 else 1.0
        overall_rec = float(total_tp / (total_tp + total_fn)) if (total_tp + total_fn) > 0 else 1.0
        overall_f1 = float(2 * (overall_prec * overall_rec) / (overall_prec + overall_rec)) if (overall_prec + overall_rec) > 0 else 0.0
        overall_fpr = float(total_fp / (total_fp + total_tn)) if (total_fp + total_tn) > 0 else 0.0
        
        diag_accuracy = float(correct_diagnoses / total_evaluable_diagnoses) if total_evaluable_diagnoses > 0 else 1.0

        return EvaluationSummary(
            overall_precision=round(overall_prec, 4),
            overall_recall=round(overall_rec, 4),
            overall_f1=round(overall_f1, 4),
            overall_false_positive_rate=round(overall_fpr, 4),
            diagnosis_accuracy=round(diag_accuracy, 4),
            scenario_results=scenario_results,
            evaluated_at=datetime.utcnow()
        )


evaluator = BenchmarkEvaluator()
