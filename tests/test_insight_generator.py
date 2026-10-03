"""
Unit tests for InsightGenerator module.
"""

import unittest
from src.insight_generator import InsightGenerator


class TestInsightGenerator(unittest.TestCase):

    def test_single_anomaly_explanation(self):
        row_snapshot = {"Revenue_dev": -32.0, "Traffic_dev": 0.5, "Conversion_Rate_dev": -18.0}
        exp = InsightGenerator.generate_single_anomaly_explanation(
            target_metric="Revenue",
            current_val=84500.0,
            baseline_val=112300.0,
            dev_pct=-32.0,
            severity="High",
            row_data=row_snapshot
        )

        self.assertIn("explanation", exp)
        self.assertIn("possible_impact", exp)
        self.assertIn("recommended_check", exp)
        self.assertIn("conversion rate declined", exp["explanation"])
        self.assertIn("may", exp["explanation"])  # Asserts no unproven causation language

    def test_rule_based_executive_summary(self):
        anomalies = [
            {"metric_name": "Revenue", "current_value": 80000, "baseline": 100000, "deviation_pct": -20.0, "severity": "High"},
            {"metric_name": "Conversion_Rate", "current_value": 2.1, "baseline": 3.2, "deviation_pct": -34.0, "severity": "Critical"}
        ]
        summary = InsightGenerator.generate_executive_summary(anomalies, baseline_period=14)
        self.assertTrue(len(summary) > 50)
        self.assertIn("monitoring", summary.lower())


if __name__ == "__main__":
    unittest.main()
