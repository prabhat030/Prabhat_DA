"""
AI Anomaly Agent for Business Metrics
Main Streamlit Application Entry Point.
"""

import os
from pathlib import Path
import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(
    page_title="AI Anomaly Agent for Business Metrics",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils.config import (
    SAMPLE_DATA_PATH,
    SAMPLE_DATA_CSV,
    DEFAULT_BASELINE_WINDOW,
    DEFAULT_DETECTION_METHOD,
    DEFAULT_THRESHOLD_PERCENT
)
from src.data_loader import DataLoader
from src.data_cleaner import DataCleaner
from src.anomaly_detector import AnomalyDetector
from src.insight_generator import InsightGenerator
from src.email_service import EmailService
from src.database import DatabaseManager

# Import view pages
from views.overview import render_overview_page
from views.anomaly_monitor import render_anomaly_monitor_page
from views.trends import render_trends_page
from views.ai_insights import render_ai_insights_page
from views.alert_history import render_alert_history_page
from views.settings import render_settings_page


# --- GLOBAL APP STYLING ---
st.markdown(
    """
    <style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .stAlert { border-radius: 8px; }
    .stButton>button { border-radius: 8px; font-weight: 600; }
    .stSelectbox label, .stMultiSelect label, .stSlider label { font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize Database and Email Service
@st.cache_resource
def get_db_and_services():
    db = DatabaseManager()
    email_svc = EmailService()
    return db, email_svc

db, email_service = get_db_and_services()


# --- SIDEBAR & SETUP ---
st.sidebar.markdown("## 🤖 AI Anomaly Agent")
st.sidebar.markdown("*Intelligent Business Metrics Monitor*")
st.sidebar.markdown("---")

# Navigation Menu
page_selection = st.sidebar.radio(
    "Navigation",
    options=[
        "📊 Overview",
        "🔍 Anomaly Monitor",
        "📈 Metric Trends",
        "🤖 AI Insights",
        "📜 Alert History",
        "⚙️ Settings"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📁 Data Source")

uploaded_file = st.sidebar.file_uploader("Upload Business Data (Excel or CSV)", type=["xlsx", "xls", "csv"])
use_sample = st.sidebar.button("📊 Load Sample 180-Day Dataset", use_container_width=True)

# Determine data source
df_raw = None
filename_used = "sample_business_data.xlsx"

if uploaded_file is not None:
    loader = DataLoader(uploaded_file, filename=uploaded_file.name)
    df_raw = loader.load()
    filename_used = uploaded_file.name
elif use_sample or "df_loaded" not in st.session_state:
    if SAMPLE_DATA_PATH.exists():
        loader = DataLoader(str(SAMPLE_DATA_PATH))
        df_raw = loader.load()
        st.session_state["df_loaded"] = True
    elif SAMPLE_DATA_CSV.exists():
        loader = DataLoader(str(SAMPLE_DATA_CSV))
        df_raw = loader.load()
        st.session_state["df_loaded"] = True
    else:
        st.warning("Sample dataset not found. Generating sample data...")
        from scripts.generate_sample_data import main as gen_sample
        gen_sample()
        loader = DataLoader(str(SAMPLE_DATA_PATH))
        df_raw = loader.load()
        st.session_state["df_loaded"] = True
else:
    if "raw_df" in st.session_state:
        df_raw = st.session_state["raw_df"]
        loader = st.session_state["loader"]

if df_raw is not None:
    st.session_state["raw_df"] = df_raw
    st.session_state["loader"] = loader
else:
    st.error("Failed to load dataset. Please upload a valid CSV or Excel file.")
    st.stop()


# --- CONFIGURATION PARAMETERS ---
db_settings = db.get_settings()

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Detection Controls")

date_col = loader.date_col
numeric_cols = loader.numeric_cols

if not numeric_cols:
    st.sidebar.error("No numeric metrics detected in the dataset!")
    st.stop()

# Metric selection
selected_metrics = st.sidebar.multiselect(
    "Select Metrics to Monitor",
    options=numeric_cols,
    default=numeric_cols
)

detection_method = st.sidebar.selectbox(
    "Detection Method",
    options=["Moving Average", "Percentage Change", "Z-Score", "Isolation Forest"],
    index=["Moving Average", "Percentage Change", "Z-Score", "Isolation Forest"].index(
        db_settings.get("detection_method", DEFAULT_DETECTION_METHOD)
    )
)

baseline_window = st.sidebar.selectbox(
    "Baseline Period (Window)",
    options=[7, 14, 21, 30, 60],
    index=[7, 14, 21, 30, 60].index(
        int(db_settings.get("baseline_window", DEFAULT_BASELINE_WINDOW))
    )
)

threshold_pct = st.sidebar.slider(
    "Threshold (% Deviation)",
    min_value=5.0,
    max_value=50.0,
    value=float(db_settings.get("threshold", DEFAULT_THRESHOLD_PERCENT)),
    step=1.0
)

# --- RUN CLEANING & ANOMALY DETECTION ENGINE ---
cleaner = DataCleaner(df_raw, date_col, numeric_cols)
clean_df, audit_summary = cleaner.clean_and_audit()

anomaly_results = {}
all_detected_anomalies = []

for metric in selected_metrics:
    res_df = AnomalyDetector.analyze_metric(
        df=clean_df,
        date_col=date_col,
        metric_col=metric,
        method=detection_method,
        window=baseline_window,
        threshold_pct=threshold_pct
    )
    anomaly_results[metric] = res_df

    # Extract anomalies for database logging & emails
    anom_rows = res_df[res_df["is_anomaly"]].copy()
    for idx, r in anom_rows.iterrows():
        # Build multi-metric row snapshot
        row_dict = {f"{m}_dev": anomaly_results[m].iloc[idx]["deviation_pct"] for m in anomaly_results if idx < len(anomaly_results[m])}
        exp = InsightGenerator.generate_single_anomaly_explanation(
            metric, r["actual"], r["baseline"], r["deviation_pct"], r["severity"], row_dict
        )
        all_detected_anomalies.append({
            "date": str(r["date"])[:10],
            "metric_name": metric,
            "current_value": float(r["actual"]),
            "baseline": float(r["baseline"]),
            "deviation_pct": float(r["deviation_pct"]),
            "anomaly_score": float(r.get("anomaly_score", 0.0)),
            "severity": r["severity"],
            "is_anomaly": True,
            "explanation": exp["explanation"],
            "possible_impact": exp["possible_impact"],
            "recommended_check": exp["recommended_check"]
        })

# Auto-save batch alerts to SQLite database
if all_detected_anomalies and not st.session_state.get("alerts_saved"):
    db.save_alerts_batch(all_detected_anomalies)
    st.session_state["alerts_saved"] = True


# --- ROUTE TO PAGE VIEW ---
if page_selection == "📊 Overview":
    render_overview_page(clean_df, date_col, anomaly_results, audit_summary)
elif page_selection == "🔍 Anomaly Monitor":
    render_anomaly_monitor_page(anomaly_results, db, email_service)
elif page_selection == "📈 Metric Trends":
    render_trends_page(anomaly_results)
elif page_selection == "🤖 AI Insights":
    render_ai_insights_page(
        anomaly_results,
        baseline_window,
        gemini_key=st.session_state.get("gemini_key", ""),
        openai_key=st.session_state.get("openai_key", "")
    )
elif page_selection == "📜 Alert History":
    render_alert_history_page(db)
elif page_selection == "⚙️ Settings":
    render_settings_page(db, email_service)
