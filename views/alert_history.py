"""
Dashboard Page 5: Alert History Page
View, filter, and export historical alerts stored in SQLite database.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any
from src.database import DatabaseManager
from utils.helpers import format_value, get_severity_badge_html
from utils.config import SEVERITY_LEVELS
from src.metrics import MetricRegistry


def render_alert_history_page(db: DatabaseManager):
    st.markdown("## 📜 Alert History & Audit Trail")
    st.markdown("View all historical business metric alerts logged in SQLite database.")

    # --- FILTERS ---
    col1, col2, col3 = st.columns(3)
    with col1:
        metric_filter = st.selectbox("Filter Metric", options=["All"] + list(MetricRegistry.get_supported_metrics().keys()))

    with col2:
        severity_filter = st.selectbox("Filter Severity", options=["All"] + SEVERITY_LEVELS)

    with col3:
        email_sent_filter = st.selectbox("Email Sent Status", options=["All", "Sent Only", "Not Sent"])

    # Query database
    alerts = db.get_alerts(
        metric=metric_filter,
        severity=severity_filter,
        limit=1000
    )

    if email_sent_filter == "Sent Only":
        alerts = [a for a in alerts if a.get("email_sent") == 1]
    elif email_sent_filter == "Not Sent":
        alerts = [a for a in alerts if a.get("email_sent") == 0]

    st.markdown(f"**Total Historical Alerts Logged**: `{len(alerts)}`")

    if not alerts:
        st.info("No alert history found for the active filter selection.")
        return

    # Convert to pandas dataframe
    df_alerts = pd.DataFrame(alerts)

    # Reformat columns for clean display
    display_cols = []
    for _, row in df_alerts.iterrows():
        fmt_type = MetricRegistry.get_format_type(row["metric"])
        display_cols.append({
            "ID": row["id"],
            "Timestamp": str(row["timestamp"])[:19],
            "Metric": row["metric"],
            "Observed Value": format_value(row["current_value"], fmt_type),
            "Baseline": format_value(row["baseline"], fmt_type),
            "Deviation": f"{row['deviation_percentage']:+.2f}%",
            "Severity": row["severity"],
            "Email Sent": "📧 Sent" if row["email_sent"] else "❌ Not Sent",
            "Explanation": row.get("explanation", "")
        })

    df_display = pd.DataFrame(display_cols)

    # Render table
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # Export & Clear Buttons
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        csv_data = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Alert History to CSV",
            data=csv_data,
            file_name="anomaly_alert_history.csv",
            mime="text/csv"
        )

    with col_e2:
        if st.button("🗑️ Clear Alert History"):
            db.clear_alert_history()
            st.success("Alert history cleared successfully!")
            st.rerun()
