import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime
from sklearn.ensemble import IsolationForest

SEVERITY_WEIGHT_MAP = {
    "DEBUG": 0.0,
    "INFO": 0.2,
    "WARNING": 0.5,
    "ERROR": 0.8,
    "CRITICAL": 1.0,
}


class AnomalyDetector:
    """
    ML Anomaly Detector using scikit-learn Isolation Forest.
    Extracts time-based, frequency-based, and severity-based features.
    Provides relative within-file anomaly scores (0.0 to 1.0) and feature explanations.
    Scores are ranking signals, not calibrated probabilities.
    """

    def __init__(self, contamination: float = 0.08, random_state: int = 42):
        self.contamination = max(0.01, min(0.3, contamination))
        self.random_state = random_state

    def extract_features(self, entries: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Extract numerical features from parsed log entries for Isolation Forest.
        Features:
        - severity_weight: mapped numeric weight
        - time_delta_prev: seconds since previous event
        - rolling_count_60s: density of log events within 60s
        - rolling_error_count_60s: density of error events within 60s
        - msg_length: character length
        - is_error_flag: binary indicator for ERROR/CRITICAL
        """
        if not entries:
            return pd.DataFrame()

        df = pd.DataFrame(entries)
        
        # Ensure timestamp is datetime
        df["ts"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values(by="ts").reset_index(drop=True)

        # 1. Severity weight
        df["severity_weight"] = df["severity"].map(lambda s: SEVERITY_WEIGHT_MAP.get(str(s).upper(), 0.2))
        df["is_error"] = df["severity"].map(lambda s: 1.0 if str(s).upper() in ("ERROR", "CRITICAL") else 0.0)

        # 2. Time delta from previous entry in seconds
        df["time_delta_prev"] = df["ts"].diff().dt.total_seconds().fillna(0.0)
        # Cap extremes
        df["time_delta_prev"] = df["time_delta_prev"].clip(lower=0.0, upper=3600.0)

        # 3. Rolling window metrics (60-second window)
        # Set datetime index for rolling calculation
        temp_df = df.set_index("ts")
        rolling_total = temp_df["severity_weight"].rolling("60s", closed="both").count().values
        rolling_errors = temp_df["is_error"].rolling("60s", closed="both").sum().values

        df["rolling_count_60s"] = rolling_total
        df["rolling_error_count_60s"] = rolling_errors

        # 4. Message characteristics
        df["msg_length"] = df["message"].astype(str).str.len().clip(upper=1000)
        
        # 5. Service-level error density
        service_error_rates = df.groupby("service")["is_error"].transform("mean").fillna(0.0)
        df["service_error_rate"] = service_error_rates

        return df

    def detect(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Executes feature extraction and Isolation Forest inference.
        Returns list of anomaly result dicts aligned with input entries.
        """
        if not entries:
            return []

        df = self.extract_features(entries)
        n_samples = len(df)

        feature_cols = [
            "severity_weight",
            "time_delta_prev",
            "rolling_count_60s",
            "rolling_error_count_60s",
            "msg_length",
            "service_error_rate"
        ]

        X = df[feature_cols].values

        # With too little history there is no meaningful baseline to learn from.
        # Returning an explicit indeterminate result is safer than labeling a
        # high-severity event anomalous without a learned comparison set.
        if n_samples < 4:
            results = []
            for _, row in df.iterrows():
                results.append({
                    "anomaly_score": 0.0,
                    "is_anomaly": False,
                    "feature_contributions": {
                        "severity": row["severity"],
                        "error_frequency": int(row["rolling_error_count_60s"]),
                        "burst_events_60s": int(row["rolling_count_60s"]),
                        "primary_driver": "Insufficient baseline for anomaly detection"
                    }
                })
            return results

        # Configure Isolation Forest
        model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100,
            n_jobs=-1
        )
        
        # Fit and score
        model.fit(X)
        raw_scores = model.decision_function(X)  # lower = more abnormal
        predictions = model.predict(X)          # -1 = anomaly, 1 = normal

        # Normalize within this file into [0.0, 1.0] where 1.0 is the most
        # abnormal observed row. This is a ranking signal, not a probability.
        # Invert raw scores: raw_scores are typically in range [-0.5, 0.5]
        min_s = float(np.min(raw_scores))
        max_s = float(np.max(raw_scores))
        spread = max(max_s - min_s, 1e-6)
        
        normalized_scores = 1.0 - ((raw_scores - min_s) / spread)

        results = []
        for i, row in df.iterrows():
            norm_score = float(normalized_scores[i])
            # Isolation Forest's binary prediction is the source of truth for
            # is_anomaly. Severity remains a feature and explanation signal,
            # but it cannot override the learned decision.
            is_anom = bool(predictions[i] == -1)

            # Determine primary contributing factor for explainability
            reasons = []
            if row["rolling_error_count_60s"] >= 2:
                reasons.append(f"Error surge ({int(row['rolling_error_count_60s'])} errors in 60s)")
            if row["severity_weight"] >= 0.8:
                reasons.append(f"High severity flag: {row['severity']}")
            if row["service_error_rate"] > 0.5:
                reasons.append(f"Degraded service health: {row['service']}")
            if row["time_delta_prev"] < 0.05 and row["rolling_count_60s"] > 5:
                reasons.append("High burst velocity")
            
            primary_driver = "; ".join(reasons) if reasons else "Statistical behavioral deviation"

            results.append({
                "anomaly_score": round(norm_score, 4),
                "is_anomaly": is_anom,
                "feature_contributions": {
                    "severity": row["severity"],
                    "error_frequency_60s": int(row["rolling_error_count_60s"]),
                    "burst_events_60s": int(row["rolling_count_60s"]),
                    "time_delta_seconds": round(float(row["time_delta_prev"]), 2),
                    "score_semantics": "Relative within-file Isolation Forest score; not a probability",
                    "primary_driver": primary_driver
                }
            })

        return results
