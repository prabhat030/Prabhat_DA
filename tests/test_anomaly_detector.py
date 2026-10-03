"""
Unit tests for AnomalyDetector algorithms and severity logic.
"""

import unittest
import pandas as pd
import numpy as np
from src.anomaly_detector import AnomalyDetector


class TestAnomalyDetector(unittest.TestCase):

    def setUp(self):
        # Create normal sequence with single sharp drop at index 10
        dates = pd.date_range("2026-01-01", periods=15, freq="D")
        values = [100.0] * 10 + [40.0] + [100.0] * 4  # 60% drop at index 10
        self.df = pd.DataFrame({"Date": dates, "Revenue": values})

    def test_percentage_change_detection(self):
        res = AnomalyDetector.detect_percentage_change(self.df["Revenue"], threshold_pct=20.0)
        self.assertTrue(res.iloc[10]["is_anomaly"])
        self.assertEqual(res.iloc[10]["severity"], "Critical")
        self.assertFalse(res.iloc[2]["is_anomaly"])

    def test_moving_average_detection(self):
        res = AnomalyDetector.detect_moving_average(self.df["Revenue"], window=5, threshold_pct=20.0)
        self.assertTrue(res.iloc[10]["is_anomaly"])
        self.assertGreater(abs(res.iloc[10]["deviation_pct"]), 30.0)

    def test_z_score_detection(self):
        res = AnomalyDetector.detect_z_score(self.df["Revenue"], window=7, z_threshold=2.0)
        self.assertTrue(res.iloc[10]["is_anomaly"])

    def test_isolation_forest_detection(self):
        res = AnomalyDetector.detect_isolation_forest(self.df, target_col="Revenue", baseline_window=5, contamination=0.1)
        self.assertIn("anomaly_score", res.columns)
        self.assertIn("is_anomaly", res.columns)

    def test_severity_classification(self):
        self.assertEqual(AnomalyDetector.classify_severity(5.0), "Normal")
        self.assertEqual(AnomalyDetector.classify_severity(-15.0), "Low")
        self.assertEqual(AnomalyDetector.classify_severity(-25.0), "Medium")
        self.assertEqual(AnomalyDetector.classify_severity(-40.0), "High")
        self.assertEqual(AnomalyDetector.classify_severity(-60.0), "Critical")


if __name__ == "__main__":
    unittest.main()
