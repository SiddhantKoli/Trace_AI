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
    Provides normalized anomaly scores (0.0 to 1.0) and feature explanations.
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

        # If very few samples (e.g. < 4), Isolation Forest cannot reliably fit
        if n_samples < 4:
            results = []
            for _, row in df.iterrows():
                is_err = row["is_error"] == 1.0
                score = 0.85 if is_err else 0.15
                results.append({
                    "anomaly_score": round(score, 4),
                    "is_anomaly": is_err,
                    "feature_contributions": {
                        "severity": row["severity"],
                        "error_frequency": int(row["rolling_error_count_60s"]),
                        "burst_events_60s": int(row["rolling_count_60s"]),
                        "primary_driver": "High severity event" if is_err else "Routine activity"
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

        # Normalize score into [0.0, 1.0] where 1.0 is highest anomaly
        # Invert raw scores: raw_scores are typically in range [-0.5, 0.5]
        min_s = float(np.min(raw_scores))
        max_s = float(np.max(raw_scores))
        spread = max(max_s - min_s, 1e-6)
        
        normalized_scores = 1.0 - ((raw_scores - min_s) / spread)

        results = []
        for i, row in df.iterrows():
            norm_score = float(normalized_scores[i])
            is_anom = bool(predictions[i] == -1 or (row["severity_weight"] >= 0.8 and norm_score > 0.55))
            
            # Boost score slightly if severity is CRITICAL or ERROR
            if row["severity"] in ("CRITICAL", "FATAL"):
                norm_score = max(norm_score, 0.88)
                is_anom = True
            elif row["severity"] == "ERROR":
                norm_score = max(norm_score, 0.72)
                if row["rolling_error_count_60s"] > 2:
                    is_anom = True

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
                    "primary_driver": primary_driver
                }
            })

        return results
