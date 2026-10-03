"""
Dashboard Page 4: AI Insights Page
Displays AI Executive Summaries, multi-metric interaction analysis, root cause hypotheses, and recommended business actions.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any
from src.insight_generator import InsightGenerator
from utils.config import SEVERITY_COLORS


def render_ai_insights_page(
    anomaly_results: Dict[str, pd.DataFrame],
    baseline_window: int,
    gemini_key: str = "",
    openai_key: str = ""
):
    st.markdown("## 🤖 AI Business Insights & Narrative Summary")
    st.markdown("Executive narrative analysis, multi-metric cross-correlation, and recommended action steps.")

    if not anomaly_results:
        st.warning("No data loaded for insight generation.")
        return

    # Extract all detected anomalies
    all_anomalies = []
    for metric, res_df in anomaly_results.items():
        anom_rows = res_df[res_df["is_anomaly"]].copy()
        if not anom_rows.empty:
            for idx, r in anom_rows.iterrows():
                # Extract cross-metric snapshot
                row_dict = {}
                for m, mdf in anomaly_results.items():
                    if idx < len(mdf):
                        row_dict[f"{m}_dev"] = mdf.iloc[idx]["deviation_pct"]

                exp = InsightGenerator.generate_single_anomaly_explanation(
                    metric, r["actual"], r["baseline"], r["deviation_pct"], r["severity"], row_dict
                )

                all_anomalies.append({
                    "metric_name": metric,
                    "date": str(r["date"])[:10],
                    "current_value": float(r["actual"]),
                    "baseline": float(r["baseline"]),
                    "deviation_pct": float(r["deviation_pct"]),
                    "severity": r["severity"],
                    "explanation": exp["explanation"],
                    "possible_impact": exp["possible_impact"],
                    "recommended_check": exp["recommended_check"]
                })

    # --- EXECUTIVE SUMMARY CARD ---
    st.markdown("### 📝 Executive Summary")
    
    with st.spinner("Generating AI Narrative..."):
        exec_summary = InsightGenerator.generate_executive_summary(
            all_anomalies, baseline_window, gemini_key=gemini_key, openai_key=openai_key
        )

    st.markdown(
        f"""
        <div style="background-color: #F0Fdf4; border: 1.5px solid #10B981; border-radius: 12px; padding: 20px; margin-bottom: 24px;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #065F46; margin-bottom: 8px;">
                💡 Executive Intelligence Briefing
            </div>
            <p style="font-size: 1.05rem; line-height: 1.6; color: #1F2937; margin: 0;">
                {exec_summary}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- MULTI-METRIC INTERACTION INSIGHTS ---
    st.markdown("---")
    st.markdown("### 🔗 Multi-Metric Relationship Breakdown")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            #### 📊 Revenue & Conversion Dynamics
            - **Revenue Down + Traffic Stable + Conversion Down**:
              *Indicates checkout friction, payment gateway errors, or pricing resistance rather than lower visitor traffic.*
            - **Revenue Down + Traffic Down**:
              *Points toward a top-of-funnel customer acquisition issue or ad campaign disruption.*
            - **Revenue Up + Orders Up**:
              *Reflects healthy overall demand acceleration across sales channels.*
            """
        )

    with col2:
        st.markdown(
            """
            #### ⚖️ Efficiency & Quality Dynamics
            - **Marketing Cost Up + Revenue Flat**:
              *Highlights lower return on ad spend (ROAS) and potential budget overspending.*
            - **Refunds Surge**:
              *May signal product quality defects, fulfillment delays, or billing discrepancies.*
            - **Traffic Up + Conversion Down**:
              *Suggests lower intent ad traffic or landing page messaging misalignment.*
            """
        )

    # --- RECOMMENDED INVESTIGATION CHECKLIST ---
    st.markdown("---")
    st.markdown("### 📋 Recommended Investigation Checklist")
    st.markdown("Use this interactive checklist to assign and track resolution steps for detected anomalies:")

    st.checkbox("Audit checkout page loading times and payment gateway success rates", value=False)
    st.checkbox("Review top marketing ad campaigns and bidding strategies for spend anomalies", value=False)
    st.checkbox("Inspect recent customer support tickets and refund reason codes", value=False)
    st.checkbox("Verify landing page links, UTM tags, and organic search ranking stability", value=False)
    st.checkbox("Check inventory stock availability for top-selling SKUs", value=False)
