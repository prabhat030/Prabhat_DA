"""
SMTP Email Alert Service for notifying team members when significant business anomalies occur.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Tuple, Optional
from utils.config import (
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    ALERT_SENDER_EMAIL,
    ALERT_DEFAULT_RECIPIENT,
    SEVERITY_COLORS
)
from utils.helpers import format_value
from src.metrics import MetricRegistry


class EmailService:
    """Handles SMTP connection, email rendering, and dispatch for anomaly alerts."""

    def __init__(
        self,
        server: str = SMTP_SERVER,
        port: int = SMTP_PORT,
        username: str = SMTP_USERNAME,
        password: str = SMTP_PASSWORD,
        sender: str = ALERT_SENDER_EMAIL
    ):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender or username

    def is_configured(self) -> bool:
        """Check if SMTP credentials are fully provided."""
        return bool(self.server and self.port and self.username and self.password)

    def send_anomaly_alert(
        self,
        recipient: str,
        anomaly: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Send HTML email notification for a detected anomaly.
        Returns (success: bool, message: str).
        """
        if not recipient:
            recipient = ALERT_DEFAULT_RECIPIENT

        if not recipient:
            return False, "Recipient email address is missing."

        if not self.is_configured():
            return False, "SMTP credentials are not fully configured in settings or environment."

        metric = anomaly.get("metric_name", "Business Metric")
        curr_val = anomaly.get("current_value", 0.0)
        base_val = anomaly.get("baseline", 0.0)
        dev_pct = anomaly.get("deviation_pct", 0.0)
        severity = anomaly.get("severity", "High").upper()
        explanation = anomaly.get("explanation", "An unexpected variation was detected.")
        impact = anomaly.get("possible_impact", "Potential change in operational metric performance.")
        rec_check = anomaly.get("recommended_check", "Review channel metrics and system logs.")
        detected_at = anomaly.get("date", "Today")

        fmt_type = MetricRegistry.get_format_type(metric)
        curr_str = format_value(curr_val, fmt_type)
        base_str = format_value(base_val, fmt_type)
        sev_color = SEVERITY_COLORS.get(anomaly.get("severity", "High"), "#EF4444")

        subject = f"[{severity} ALERT] {metric} Anomaly Detected ({dev_pct:+.2f}%)"

        # Construct Professional HTML Body
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; color: #1f2937; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e5e7eb; }}
            .header {{ background: #1e293b; color: #ffffff; padding: 24px; text-align: center; }}
            .header h2 {{ margin: 0; font-size: 20px; font-weight: 600; letter-spacing: 0.5px; }}
            .badge {{ display: inline-block; background-color: {sev_color}; color: #ffffff; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-top: 8px; text-transform: uppercase; }}
            .content {{ padding: 24px; }}
            .metrics-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 20px 0; background: #f8fafc; padding: 16px; border-radius: 8px; }}
            .metric-box {{ text-align: center; }}
            .metric-label {{ font-size: 12px; color: #64748b; text-transform: uppercase; font-weight: 600; }}
            .metric-value {{ font-size: 20px; font-weight: bold; color: #0f172a; margin-top: 4px; }}
            .section {{ margin-bottom: 20px; }}
            .section-title {{ font-size: 14px; font-weight: bold; color: #334155; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; margin-bottom: 8px; }}
            .footer {{ background: #f1f5f9; padding: 16px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h2>🤖 AI Business Anomaly Monitor</h2>
              <div class="badge">{severity} SEVERITY ALERT</div>
            </div>
            
            <div class="content">
              <p style="font-size: 15px; margin-top: 0;">An anomaly has been detected for <strong>{metric}</strong> on <strong>{detected_at}</strong>.</p>
              
              <div class="metrics-grid">
                <div class="metric-box">
                  <div class="metric-label">Observed Value</div>
                  <div class="metric-value">{curr_str}</div>
                </div>
                <div class="metric-box">
                  <div class="metric-label">Expected Baseline</div>
                  <div class="metric-value">{base_str}</div>
                </div>
              </div>

              <div style="text-align: center; margin-bottom: 20px;">
                <span style="font-size: 16px; font-weight: bold; color: {sev_color};">
                  Deviation: {dev_pct:+.2f}%
                </span>
              </div>

              <div class="section">
                <div class="section-title">📊 Business Analysis</div>
                <p style="margin: 0; line-height: 1.5;">{explanation}</p>
              </div>

              <div class="section">
                <div class="section-title">⚠️ Possible Impact</div>
                <p style="margin: 0; line-height: 1.5;">{impact}</p>
              </div>

              <div class="section">
                <div class="section-title">🔍 Recommended Action</div>
                <p style="margin: 0; line-height: 1.5;">{rec_check}</p>
              </div>
            </div>

            <div class="footer">
              Automated Alert sent by AI Business Anomaly Agent • Date: {detected_at}
            </div>
          </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = recipient
        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(self.server, self.port, timeout=10) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.sender, [recipient], msg.as_string())
            return True, f"Email alert successfully sent to {recipient}."
        except Exception as e:
            return False, f"Failed to send email alert via SMTP: {str(e)}"

    def send_test_email(self, recipient: str) -> Tuple[bool, str]:
        """Send a test email to verify SMTP credentials."""
        dummy_anomaly = {
            "metric_name": "Revenue",
            "current_value": 84500.0,
            "baseline": 112300.0,
            "deviation_pct": -24.75,
            "severity": "High",
            "explanation": "Revenue declined 24.75% compared with the 14-day average baseline. Traffic remained steady while conversion rate dropped 18%.",
            "possible_impact": "Potential loss in conversion efficiency.",
            "recommended_check": "Review store checkout flow and recent pricing or ad campaigns.",
            "date": "2026-10-03"
        }
        return self.send_anomaly_alert(recipient, dummy_anomaly)
