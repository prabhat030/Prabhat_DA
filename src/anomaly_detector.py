"""
Comprehensive Anomaly Detection Module supporting:
- Percentage Change
- Moving Average (Rolling Mean)
- Z-Score
- Isolation Forest
With Severity Classification and Bound Generation for Visualizations.
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from utils.config import (
    DEFAULT_BASELINE_WINDOW,
    DEFAULT_THRESHOLD_PERCENT,
    DEFAULT_Z_THRESHOLD,
    DEFAULT_ISOLATION_CONTAMINATION,
    SEVERITY_LEVELS
)


class AnomalyDetector:
    """Core Anomaly Detection Engine for time-series business metrics."""

    @staticmethod
    def classify_severity(deviation_pct: float, thresholds: Optional[Dict[str, float]] = None) -> str:
        """
        Classify anomaly severity based on percentage deviation magnitude.
        Default ranges:
        0-10%   -> Normal
        10-20%  -> Low
        20-30%  -> Medium
        30-50%  -> High
        >50%    -> Critical
        """
        abs_dev = abs(deviation_pct)
        if thresholds is None:
            thresholds = {
                "low": 10.0,
                "medium": 20.0,
                "high": 30.0,
                "critical": 50.0
            }

        if abs_dev < thresholds["low"]:
            return "Normal"
        elif abs_dev < thresholds["medium"]:
            return "Low"
        elif abs_dev < thresholds["high"]:
            return "Medium"
        elif abs_dev < thresholds["critical"]:
            return "High"
        else:
            return "Critical"

    @staticmethod
    def detect_percentage_change(
        series: pd.Series,
        threshold_pct: float = DEFAULT_THRESHOLD_PERCENT
    ) -> pd.DataFrame:
        """
        METHOD 1: Percentage Change Detection
        Compares each observation with the immediately preceding observation.
        """
        df_res = pd.DataFrame({"actual": series})
        prev_series = series.shift(1)
        df_res["baseline"] = prev_series
        
        # Calculate percentage change
        pct_change = ((series - prev_series) / prev_series.replace(0, np.nan)) * 100
        df_res["deviation_pct"] = pct_change.fillna(0)
        df_res["anomaly_score"] = abs(df_res["deviation_pct"]) / threshold_pct
        
        df_res["is_anomaly"] = abs(df_res["deviation_pct"]) >= threshold_pct
        df_res["severity"] = df_res["deviation_pct"].apply(
            lambda dev: AnomalyDetector.classify_severity(dev, {"low": threshold_pct * 0.5, "medium": threshold_pct, "high": threshold_pct * 1.5, "critical": threshold_pct * 2.5})
        )
        
        # Bounds for visualization
        df_res["upper_bound"] = prev_series * (1 + threshold_pct / 100)
        df_res["lower_bound"] = prev_series * (1 - threshold_pct / 100)
        
        return df_res

    @staticmethod
    def detect_moving_average(
        series: pd.Series,
        window: int = DEFAULT_BASELINE_WINDOW,
        threshold_pct: float = DEFAULT_THRESHOLD_PERCENT
    ) -> pd.DataFrame:
        """
        METHOD 2: Moving Average (Rolling Mean) Detection
        Compares observation with the mean of the previous N observations.
        """
        df_res = pd.DataFrame({"actual": series})
        # Calculate rolling mean using previous window points (excluding current point to avoid contamination)
        rolling_mean = series.shift(1).rolling(window=window, min_periods=1).mean()
        rolling_std = series.shift(1).rolling(window=window, min_periods=1).std().fillna(0)
        
        df_res["baseline"] = rolling_mean
        
        # Calculate percentage deviation from rolling mean
        deviation_pct = ((series - rolling_mean) / rolling_mean.replace(0, np.nan)) * 100
        df_res["deviation_pct"] = deviation_pct.fillna(0)
        
        df_res["anomaly_score"] = abs(df_res["deviation_pct"]) / threshold_pct
        df_res["is_anomaly"] = abs(df_res["deviation_pct"]) >= threshold_pct
        
        df_res["severity"] = df_res["deviation_pct"].apply(
            lambda dev: AnomalyDetector.classify_severity(dev, {"low": threshold_pct * 0.5, "medium": threshold_pct, "high": threshold_pct * 1.5, "critical": threshold_pct * 2.5})
        )
        
        # Dynamic upper & lower bounds for chart plotting
        df_res["upper_bound"] = rolling_mean * (1 + threshold_pct / 100)
        df_res["lower_bound"] = rolling_mean * (1 - threshold_pct / 100)
        
        return df_res

    @staticmethod
    def detect_z_score(
        series: pd.Series,
        window: int = DEFAULT_BASELINE_WINDOW,
        z_threshold: float = DEFAULT_Z_THRESHOLD
    ) -> pd.DataFrame:
        """
        METHOD 3: Z-Score Detection
        z = (x - rolling_mean) / rolling_std
        Flags observations where abs(z) > z_threshold.
        """
        df_res = pd.DataFrame({"actual": series})
        rolling_mean = series.shift(1).rolling(window=window, min_periods=1).mean()
        rolling_std = series.shift(1).rolling(window=window, min_periods=1).std()
        # Replace 0 or NaN std with a small epsilon or overall series std to prevent div-by-zero on flat baselines
        overall_std = series.std()
        default_std = overall_std if (overall_std and overall_std > 0) else 1e-3
        rolling_std = rolling_std.fillna(default_std).replace(0, default_std)
        
        df_res["baseline"] = rolling_mean
        
        # Calculate Z-score
        z_scores = (series - rolling_mean) / rolling_std
        z_scores = z_scores.fillna(0)
        
        df_res["z_score"] = z_scores
        df_res["anomaly_score"] = abs(z_scores)
        
        # Percentage deviation for severity consistency
        deviation_pct = ((series - rolling_mean) / rolling_mean.replace(0, np.nan)) * 100
        df_res["deviation_pct"] = deviation_pct.fillna(0)
        
        df_res["is_anomaly"] = abs(z_scores) >= z_threshold
        
        df_res["severity"] = df_res.apply(
            lambda row: AnomalyDetector.classify_severity(row["deviation_pct"]) if row["is_anomaly"] else "Normal",
            axis=1
        )
        
        # Bounds based on Z-score threshold
        std_clean = rolling_std.fillna(0)
        df_res["upper_bound"] = rolling_mean + (z_threshold * std_clean)
        df_res["lower_bound"] = rolling_mean - (z_threshold * std_clean)
        
        return df_res

    @staticmethod
    def detect_isolation_forest(
        df_metrics: pd.DataFrame,
        target_col: str,
        baseline_window: int = DEFAULT_BASELINE_WINDOW,
        contamination: float = DEFAULT_ISOLATION_CONTAMINATION
    ) -> pd.DataFrame:
        """
        METHOD 4: Isolation Forest (Machine Learning Anomaly Detection)
        Uses sklearn IsolationForest to fit multi-variate or uni-variate feature space.
        """
        series = df_metrics[target_col]
        df_res = pd.DataFrame({"actual": series})
        
        rolling_mean = series.shift(1).rolling(window=baseline_window, min_periods=1).mean()
        df_res["baseline"] = rolling_mean
        
        # Prepare feature matrix (using target metric + rolling stats)
        features = pd.DataFrame({
            "target": series,
            "rolling_mean": rolling_mean.fillna(series.mean()),
            "diff": (series - rolling_mean).fillna(0)
        }).fillna(0)

        # Fit Isolation Forest
        model = IsolationForest(
            contamination=max(0.01, min(0.5, contamination)),
            random_state=42
        )
        preds = model.fit_predict(features)  # -1 for anomaly, 1 for normal
        scores = model.decision_function(features)  # lower = more anomalous
        
        # Invert score so higher = more anomalous (0 to 1 scale roughly)
        norm_scores = (scores.max() - scores) / (scores.max() - scores.min() + 1e-6)
        
        df_res["anomaly_score"] = norm_scores
        df_res["is_anomaly"] = preds == -1
        
        deviation_pct = ((series - rolling_mean) / rolling_mean.replace(0, np.nan)) * 100
        df_res["deviation_pct"] = deviation_pct.fillna(0)
        
        df_res["severity"] = df_res.apply(
            lambda row: AnomalyDetector.classify_severity(row["deviation_pct"]) if row["is_anomaly"] else "Normal",
            axis=1
        )
        
        # Approximate bounds using 2 standard deviations for visualization
        std = series.rolling(window=baseline_window, min_periods=1).std().fillna(series.std())
        df_res["upper_bound"] = rolling_mean + (2 * std)
        df_res["lower_bound"] = rolling_mean - (2 * std)
        
        return df_res

    @classmethod
    def analyze_metric(
        cls,
        df: pd.DataFrame,
        date_col: str,
        metric_col: str,
        method: str = "Moving Average",
        window: int = DEFAULT_BASELINE_WINDOW,
        threshold_pct: float = DEFAULT_THRESHOLD_PERCENT,
        z_threshold: float = DEFAULT_Z_THRESHOLD,
        contamination: float = DEFAULT_ISOLATION_CONTAMINATION
    ) -> pd.DataFrame:
        """
        Unified method router for analyzing a metric.
        Returns DataFrame with Date, Metric, Actual, Baseline, Deviation %, Score, Severity, Is_Anomaly, Upper, Lower.
        """
        series = df[metric_col].astype(float)
        
        if method == "Percentage Change":
            res = cls.detect_percentage_change(series, threshold_pct=threshold_pct)
        elif method == "Z-Score":
            res = cls.detect_z_score(series, window=window, z_threshold=z_threshold)
        elif method == "Isolation Forest":
            res = cls.detect_isolation_forest(df, metric_col, baseline_window=window, contamination=contamination)
        else:  # Default: Moving Average
            res = cls.detect_moving_average(series, window=window, threshold_pct=threshold_pct)

        # Attach Date column
        if date_col in df.columns:
            res["date"] = df[date_col]
        else:
            res["date"] = df.index

        res["metric_name"] = metric_col
        return res
