"""
Dashboard Page 1: Overview Page
Displays business KPI cards, quick status badges, recent anomaly highlight list, and data quality preview.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
from utils.helpers import format_value, format_delta, get_severity_badge_html, get_status_indicator_html
from utils.config import SEVERITY_COLORS
from src.metrics import MetricRegistry


def render_overview_page(df: pd.DataFrame, date_col: str, anomaly_results: Dict[str, pd.DataFrame], audit_summary: Dict[str, Any]):
    st.markdown("## 📊 Executive Business Overview")
    st.markdown("Monitor key business performance indicators, recent trends, and automated anomaly status.")

    if df is None or df.empty or not anomaly_results:
        st.warning("⚠️ No data loaded or analyzed yet. Please upload a dataset or use sample data.")
        return

    # --- KPI METRIC CARDS ---
    st.markdown("### 🔑 Key Metric Performance")
    
    available_metrics = list(anomaly_results.keys())
    # Selected top metrics to showcase in 3x2 grid
    cols = st.columns(3)

    for i, metric in enumerate(available_metrics):
        col = cols[i % 3]
        metric_df = anomaly_results[metric]
        if metric_df.empty:
            continue

        latest_row = metric_df.iloc[-1]
        curr_val = latest_row["actual"]
        base_val = latest_row["baseline"]
        dev_pct = latest_row["deviation_pct"]
        is_anomaly = latest_row["is_anomaly"]
        severity = latest_row["severity"]

        fmt_type = MetricRegistry.get_format_type(metric)
        curr_str = format_value(curr_val, fmt_type)
        base_str = format_value(base_val, fmt_type)
        delta_str = format_delta(dev_pct)

        # Status badge styling
        card_border = SEVERITY_COLORS.get(severity, "#E5E7EB") if is_anomaly else "#10B981"
        card_bg = f"{card_border}11" if is_anomaly else "#F9FAFB"
        trend_icon = "📈" if dev_pct > 0 else ("📉" if dev_pct < 0 else "➡️")
        status_text = "⚠️ Anomaly" if is_anomaly else "✅ Normal"

        with col:
            st.markdown(
                f"""
                <div style="background-color: {card_bg}; border: 1.5px solid {card_border}; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-weight: 600; color: #4B5563; font-size: 0.95rem;">{metric}</span>
                        <span>{get_severity_badge_html(severity) if is_anomaly else '<span style="color:#10B981; font-weight:600; font-size:0.8rem;">NORMAL</span>'}</span>
                    </div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #111827; margin-bottom: 4px;">
                        {curr_str}
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; color: #6B7280;">
                        <span>Baseline: {base_str}</span>
                        <span style="font-weight: 700; color: {'#EF4444' if dev_pct < 0 else '#10B981'};">
                            {trend_icon} {delta_str}
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("---")

    # --- RECENT ANOMALIES & DATA SUMMARY ---
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### 🚨 Recent Critical & High Anomalies")
        
        # Aggregate all detected anomalies across metrics
        all_anomalies = []
        for metric, res_df in anomaly_results.items():
            anom_rows = res_df[res_df["is_anomaly"]].copy()
            if not anom_rows.empty:
                for _, r in anom_rows.iterrows():
                    all_anomalies.append({
                        "Date": str(r["date"])[:10],
                        "Metric": metric,
                        "Observed": format_value(r["actual"], MetricRegistry.get_format_type(metric)),
                        "Baseline": format_value(r["baseline"], MetricRegistry.get_format_type(metric)),
                        "Deviation": f"{r['deviation_pct']:+.2f}%",
                        "Severity": r["severity"]
                    })

        if all_anomalies:
            anom_df = pd.DataFrame(all_anomalies)
            # Sort by Severity priority then Date
            sev_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Normal": 4}
            anom_df["sev_rank"] = anom_df["Severity"].map(sev_order)
            anom_df = anom_df.sort_values(by=["sev_rank", "Date"], ascending=[True, False]).drop(columns=["sev_rank"])

            st.dataframe(
                anom_df.head(10),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("🎉 No anomalies detected in current dataset parameters!")

    with col_right:
        st.markdown("### 📋 Data Quality Audit")
        st.markdown(
            f"""
            - **Total Rows**: `{audit_summary.get('total_rows_clean', 0):,}`
            - **Date Range**: `{audit_summary.get('date_range_start', 'N/A')}` to `{audit_summary.get('date_range_end', 'N/A')}`
            - **Monitored Metrics**: `{len(available_metrics)}`
            - **Missing Values Handled**: `{audit_summary.get('total_missing_values', 0)}`
            - **Duplicates Removed**: `{audit_summary.get('duplicate_rows_removed', 0)}`
            """
        )
