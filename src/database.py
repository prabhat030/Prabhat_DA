"""
SQLite Database Storage Manager for Alert History and Application Settings.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.config import (
    DATABASE_PATH,
    DEFAULT_BASELINE_WINDOW,
    DEFAULT_DETECTION_METHOD,
    DEFAULT_THRESHOLD_PERCENT,
    ALERT_DEFAULT_RECIPIENT
)


class DatabaseManager:
    """Handles SQLite persistence for alerts, settings, and dataset logs."""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Create SQLite tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Alerts Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric TEXT NOT NULL,
                current_value REAL NOT NULL,
                baseline REAL NOT NULL,
                deviation_percentage REAL NOT NULL,
                anomaly_score REAL,
                severity TEXT NOT NULL,
                explanation TEXT,
                email_sent INTEGER DEFAULT 0
            );
            """)

            # 2. Settings Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY DEFAULT 1,
                baseline_window INTEGER DEFAULT 14,
                detection_method TEXT DEFAULT 'Moving Average',
                threshold REAL DEFAULT 20.0,
                email_recipient TEXT,
                email_enabled INTEGER DEFAULT 1,
                min_email_severity TEXT DEFAULT 'High'
            );
            """)

            # 3. Datasets Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                row_count INTEGER,
                column_count INTEGER,
                metrics_found TEXT
            );
            """)

            # Insert default settings if empty
            cursor.execute("SELECT COUNT(*) FROM settings")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                INSERT INTO settings (id, baseline_window, detection_method, threshold, email_recipient, email_enabled, min_email_severity)
                VALUES (1, ?, ?, ?, ?, 1, 'High')
                """, (DEFAULT_BASELINE_WINDOW, DEFAULT_DETECTION_METHOD, DEFAULT_THRESHOLD_PERCENT, ALERT_DEFAULT_RECIPIENT))

            conn.commit()

    def save_alert(self, alert: Dict[str, Any]) -> int:
        """Save a single alert record into SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO alerts (
                timestamp, metric, current_value, baseline, deviation_percentage,
                anomaly_score, severity, explanation, email_sent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.get("date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                alert.get("metric_name", "Unknown"),
                float(alert.get("current_value", 0.0)),
                float(alert.get("baseline", 0.0)),
                float(alert.get("deviation_pct", 0.0)),
                float(alert.get("anomaly_score", 0.0)),
                alert.get("severity", "Normal"),
                alert.get("explanation", ""),
                1 if alert.get("email_sent", False) else 0
            ))
            conn.commit()
            return cursor.lastrowid

    def save_alerts_batch(self, alerts: List[Dict[str, Any]]) -> int:
        """Save a batch of detected alerts."""
        saved_count = 0
        for alert in alerts:
            if alert.get("is_anomaly", False):
                self.save_alert(alert)
                saved_count += 1
        return saved_count

    def get_alerts(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        metric: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Query alert history with optional date, metric, and severity filters."""
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []

        if date_from:
            query += " AND timestamp >= ?"
            params.append(date_from)
        if date_to:
            query += " AND timestamp <= ?"
            params.append(date_to)
        if metric and metric != "All":
            query += " AND metric = ?"
            params.append(metric)
        if severity and severity != "All":
            query += " AND severity = ?"
            params.append(severity)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def update_alert_email_status(self, alert_id: int, status: bool):
        """Update email_sent flag for an alert."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE alerts SET email_sent = ? WHERE id = ?", (1 if status else 0, alert_id))
            conn.commit()

    def get_settings(self) -> Dict[str, Any]:
        """Fetch current app settings."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM settings WHERE id = 1")
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {
                "baseline_window": DEFAULT_BASELINE_WINDOW,
                "detection_method": DEFAULT_DETECTION_METHOD,
                "threshold": DEFAULT_THRESHOLD_PERCENT,
                "email_recipient": ALERT_DEFAULT_RECIPIENT,
                "email_enabled": 1,
                "min_email_severity": "High"
            }

    def save_settings(self, settings_dict: Dict[str, Any]):
        """Update app settings."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE settings SET
                baseline_window = ?,
                detection_method = ?,
                threshold = ?,
                email_recipient = ?,
                email_enabled = ?,
                min_email_severity = ?
            WHERE id = 1
            """, (
                settings_dict.get("baseline_window", DEFAULT_BASELINE_WINDOW),
                settings_dict.get("detection_method", DEFAULT_DETECTION_METHOD),
                settings_dict.get("threshold", DEFAULT_THRESHOLD_PERCENT),
                settings_dict.get("email_recipient", ""),
                1 if settings_dict.get("email_enabled", True) else 0,
                settings_dict.get("min_email_severity", "High")
            ))
            conn.commit()

    def clear_alert_history(self):
        """Delete all historical alert logs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alerts")
            conn.commit()
