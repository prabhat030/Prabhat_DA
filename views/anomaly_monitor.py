"""
Dashboard Page 2: Anomaly Monitor Page
Interactive filterable table of all detected anomalies with natural language business explanations.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any
from utils.helpers import format_value, get_severity_badge_html
from utils.config import SEVERITY_LEVELS
from src.metrics import MetricRegistry
from src.insight_generator import InsightGenerator
from src.email_service import EmailService
from src.database import DatabaseManager


def render_anomaly_monitor_page(
    anomaly_results: Dict[str, pd.DataFrame],
    db: DatabaseManager,
    email_service: EmailService
):
    st.markdown("## 🔍 Automated Anomaly Monitor")
    st.markdown("Detailed table of detected business anomalies with severity badges and multi-metric explanations.")

    if not anomaly_results:
        st.warning("No data available to monitor.")
        return

    # --- FILTER CONTROLS ---
    col_f1, col_f2, col_f3 = st.columns(3)
    
    metrics_list = ["All"] + list(anomaly_results.keys())
    with col_f1:
        selected_metric = st.selectbox("Filter by Metric", options=metrics_list)

    with col_f2:
        selected_severity = st.selectbox("Filter by Severity", options=["All"] + SEVERITY_LEVELS)

    with col_f3:
        show_anomalies_only = st.checkbox("Show Anomalies Only", value=True)

    # --- AGGREGATE ANOMALY RECORDS ---
    records = []
    for metric, res_df in anomaly_results.items():
        if selected_metric != "All" and metric != selected_metric:
            continue

        for idx, row in res_df.iterrows():
            if show_anomalies_only and not row["is_anomaly"]:
                continue
            if selected_severity != "All" and row["severity"] != selected_severity:
                continue

            # Build cross-metric snapshot for explanation
            row_dict = {}
            for m, mdf in anomaly_results.items():
                if idx < len(mdf):
                    row_dict[f"{m}_dev"] = mdf.iloc[idx]["deviation_pct"]

            # Generate natural language explanation
            exp_dict = InsightGenerator.generate_single_anomaly_explanation(
                target_metric=metric,
                current_val=row["actual"],
                baseline_val=row["baseline"],
                dev_pct=row["deviation_pct"],
                severity=row["severity"],
                row_data=row_dict
            )

            records.append({
                "date": str(row["date"])[:10],
                "metric_name": metric,
                "current_value": float(row["actual"]),
                "baseline": float(row["baseline"]),
                "deviation_pct": float(row["deviation_pct"]),
                "anomaly_score": float(row.get("anomaly_score", 0.0)),
                "severity": row["severity"],
                "is_anomaly": bool(row["is_anomaly"]),
                "explanation": exp_dict["explanation"],
                "possible_impact": exp_dict["possible_impact"],
                "recommended_check": exp_dict["recommended_check"]
            })

    st.markdown(f"**Found `{len(records)}` record(s)** matching filter criteria.")

    if not records:
        st.info("No records found matching the active filters.")
        return

    # Convert to Display DataFrame
    rec_df = pd.DataFrame(records)

    # Render interactive list with expander details
    for idx, rec in rec_df.iterrows():
        fmt_type = MetricRegistry.get_format_type(rec["metric_name"])
        curr_str = format_value(rec["current_value"], fmt_type)
        base_str = format_value(rec["baseline"], fmt_type)
        dev_str = f"{rec['deviation_pct']:+.2f}%"

        sev_badge = get_severity_badge_html(rec["severity"])
        date_str = rec["date"]
        m_name = rec["metric_name"]

        header_title = f"{'🚨' if rec['is_anomaly'] else '✅'} {date_str} | {m_name}: {curr_str} (Baseline: {base_str}, Change: {dev_str}) [{rec['severity']}]"

        with st.expander(header_title, expanded=(idx == 0 and rec["is_anomaly"])):
            st.markdown(f"**Severity**: {sev_badge}", unsafe_allow_html=True)
            st.markdown(f"**Observed Value**: `{curr_str}` | **Expected Baseline**: `{base_str}` | **Deviation**: `{dev_str}` | **Anomaly Score**: `{rec['anomaly_score']:.2f}`")
            
            st.markdown("---")
            st.markdown(f"💡 **Business Explanation**: {rec['explanation']}")
            st.markdown(f"⚠️ **Possible Business Impact**: {rec['possible_impact']}")
            st.markdown(f"🔍 **Recommended Area to Check**: {rec['recommended_check']}")

            # Send Email Alert Manual Trigger Button
            col_b1, col_b2 = st.columns([2, 4])
            with col_b1:
                if st.button(f"📧 Send Email Alert for {m_name} ({date_str})", key=f"btn_mail_{idx}"):
                    settings = db.get_settings()
                    recipient = settings.get("email_recipient")
                    if not recipient:
                        st.error("Please configure an email recipient in Settings first!")
                    else:
                        success, msg = email_service.send_anomaly_alert(recipient, rec)
                        if success:
                            rec["email_sent"] = True
                            db.save_alert(rec)
                            st.success(f"Alert sent successfully to {recipient}!")
                        else:
                            st.error(f"Failed to send email: {msg}")
