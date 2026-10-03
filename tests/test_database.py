"""
Unit tests for DatabaseManager module.
"""

import unittest
import os
import tempfile
from src.database import DatabaseManager


class TestDatabaseManager(unittest.TestCase):

    def setUp(self):
        # Use temporary file for test database
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db = DatabaseManager(db_path=self.temp_db.name)

    def tearDown(self):
        try:
            if os.path.exists(self.temp_db.name):
                os.remove(self.temp_db.name)
        except Exception:
            pass

    def test_init_and_default_settings(self):
        settings = self.db.get_settings()
        self.assertEqual(settings["baseline_window"], 14)
        self.assertEqual(settings["detection_method"], "Moving Average")

    def test_save_and_retrieve_alert(self):
        alert_dict = {
            "date": "2026-10-03 10:00:00",
            "metric_name": "Revenue",
            "current_value": 75000.0,
            "baseline": 100000.0,
            "deviation_pct": -25.0,
            "anomaly_score": 1.25,
            "severity": "Medium",
            "explanation": "Revenue fell 25% due to reduced orders.",
            "email_sent": False
        }

        alert_id = self.db.save_alert(alert_dict)
        self.assertGreater(alert_id, 0)

        alerts = self.db.get_alerts(metric="Revenue")
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["metric"], "Revenue")
        self.assertEqual(alerts[0]["deviation_percentage"], -25.0)

    def test_clear_alert_history(self):
        self.db.save_alert({"metric_name": "Orders", "current_value": 10, "baseline": 20, "deviation_pct": -50.0, "severity": "High"})
        self.db.clear_alert_history()
        alerts = self.db.get_alerts()
        self.assertEqual(len(alerts), 0)


if __name__ == "__main__":
    unittest.main()
