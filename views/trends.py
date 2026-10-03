"""
Dashboard Page 3: Metric Trends Page
Displays interactive Plotly time-series charts with actuals, moving average baselines, upper/lower bounds, and anomaly markers.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict
from utils.helpers import format_value
from utils.config import SEVERITY_COLORS
from src.metrics import MetricRegistry


def render_trends_page(anomaly_results: Dict[str, pd.DataFrame]):
    st.markdown("## 📈 Metric Trend Analysis & Time-Series Visualizer")
    st.markdown("Explore historical behavior, baseline thresholds, upper/lower boundaries, and highlighted anomaly markers.")

    if not anomaly_results:
        st.warning("No data available to display trends.")
        return

    # Metric Selector
    metrics_list = list(anomaly_results.keys())
    selected_metric = st.selectbox("Select Metric to Visualize", options=metrics_list, index=0)

    metric_df = anomaly_results[selected_metric]
    if metric_df.empty:
        st.warning(f"No observations found for {selected_metric}.")
        return

    fmt_type = MetricRegistry.get_format_type(selected_metric)

    # --- METRIC SUMMARY CARDS ---
    c1, c2, c3, c4 = st.columns(4)
    total_anom = metric_df["is_anomaly"].sum()
    max_drop = metric_df["deviation_pct"].min()
    max_surge = metric_df["deviation_pct"].max()
    avg_val = metric_df["actual"].mean()

    c1.metric("Total Anomalies", f"{total_anom}", help="Count of flagged points")
    c2.metric("Average Value", format_value(avg_val, fmt_type))
    c3.metric("Max Drop", f"{max_drop:.2f}%" if max_drop < 0 else "0.00%")
    c4.metric("Max Surge", f"{max_surge:+.2f}%" if max_surge > 0 else "0.00%")

    st.markdown("---")

    # --- PLOTLY INTERACTIVE CHART ---
    fig = go.Figure()

    # 1. Shaded Upper/Lower Bound Confidence Interval
    fig.add_trace(go.Scatter(
        x=metric_df["date"],
        y=metric_df["upper_bound"],
        mode='lines',
        line=dict(width=0),
        showlegend=False,
        name='Upper Bound'
    ))
    
    fig.add_trace(go.Scatter(
        x=metric_df["date"],
        y=metric_df["lower_bound"],
        mode='lines',
        line=dict(width=0),
        fill='tonexty',
        fillcolor='rgba(239, 68, 68, 0.12)', # Soft red shading
        name='Threshold Bounds'
    ))

    # 2. Baseline / Rolling Mean
    fig.add_trace(go.Scatter(
        x=metric_df["date"],
        y=metric_df["baseline"],
        mode='lines',
        name='Expected Baseline',
        line=dict(color='#64748B', width=2, dash='dash')
    ))

    # 3. Actual Values
    fig.add_trace(go.Scatter(
        x=metric_df["date"],
        y=metric_df["actual"],
        mode='lines+markers',
        name='Actual Observed',
        line=dict(color='#2563EB', width=2.5),
        marker=dict(size=4)
    ))

    # 4. Highlighted Anomaly Markers
    anom_points = metric_df[metric_df["is_anomaly"]]
    if not anom_points.empty:
        # Group markers by severity colors
        for sev, color in SEVERITY_COLORS.items():
            sev_anom = anom_points[anom_points["severity"] == sev]
            if not sev_anom.empty:
                fig.add_trace(go.Scatter(
                    x=sev_anom["date"],
                    y=sev_anom["actual"],
                    mode='markers',
                    name=f'Anomaly ({sev})',
                    marker=dict(
                        color=color,
                        size=12,
                        symbol='circle',
                        line=dict(color='#FFFFFF', width=2)
                    ),
                    text=[f"Date: {str(d)[:10]}<br>Actual: {format_value(a, fmt_type)}<br>Dev: {dev:+.2f}%<br>Severity: {sev}"
                          for d, a, dev in zip(sev_anom["date"], sev_anom["actual"], sev_anom["deviation_pct"])],
                    hoverinfo='text'
                ))

    # Layout Styling
    fig.update_layout(
        title=f"Time-Series Performance & Threshold Boundaries: <b>{selected_metric}</b>",
        xaxis_title="Date",
        yaxis_title=f"{selected_metric}",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        template="plotly_white",
        height=520,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)
