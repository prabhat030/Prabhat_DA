"""
Dashboard Page 6: Settings Page
Configures baseline window, detection technique, anomaly threshold, email notification credentials, and AI API keys.
"""

import streamlit as st
from typing import Dict, Any
from src.database import DatabaseManager
from src.email_service import EmailService
from utils.config import SEVERITY_LEVELS


def render_settings_page(db: DatabaseManager, email_service: EmailService):
    st.markdown("## ⚙️ System Settings & Configuration")
    st.markdown("Tune detection algorithms, alert sensitivity, SMTP email notifications, and AI API integrations.")

    current_settings = db.get_settings()

    with st.form("settings_form"):
        st.markdown("### 🧮 Anomaly Detection Parameters")
        col1, col2 = st.columns(2)

        with col1:
            baseline_window = st.select_slider(
                "Baseline Period (Observations / Days)",
                options=[7, 14, 21, 30, 60, 90],
                value=int(current_settings.get("baseline_window", 14)),
                help="Number of historical data points used to compute baseline average."
            )

            detection_method = st.selectbox(
                "Default Anomaly Detection Method",
                options=["Moving Average", "Percentage Change", "Z-Score", "Isolation Forest"],
                index=["Moving Average", "Percentage Change", "Z-Score", "Isolation Forest"].index(
                    current_settings.get("detection_method", "Moving Average")
                )
            )

        with col2:
            threshold = st.slider(
                "Anomaly Sensitivity Threshold (% Deviation)",
                min_value=5.0,
                max_value=50.0,
                value=float(current_settings.get("threshold", 20.0)),
                step=1.0,
                help="Percentage deviation from baseline required to flag an anomaly."
            )

            min_email_severity = st.selectbox(
                "Minimum Email Alert Severity",
                options=["Low", "Medium", "High", "Critical"],
                index=["Low", "Medium", "High", "Critical"].index(
                    current_settings.get("min_email_severity", "High")
                )
            )

        st.markdown("---")
        st.markdown("### 📧 SMTP Email Notification Settings")

        email_enabled = st.checkbox(
            "Enable Automated Email Notifications",
            value=bool(current_settings.get("email_enabled", True))
        )

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            email_recipient = st.text_input(
                "Default Alert Recipient Email",
                value=current_settings.get("email_recipient", "") or "",
                placeholder="analytics-alerts@company.com"
            )
            smtp_server = st.text_input("SMTP Server", value=email_service.server, placeholder="smtp.gmail.com")
            smtp_port = st.number_input("SMTP Port", value=email_service.port, step=1)

        with col_m2:
            smtp_username = st.text_input("SMTP Username / Email", value=email_service.username, placeholder="your_email@gmail.com")
            smtp_password = st.text_input("SMTP Password / App Password", value=email_service.password, type="password")

        st.markdown("---")
        st.markdown("### 🤖 Optional AI Explanation Layer")
        gemini_key_input = st.text_input("Gemini API Key (Optional)", value=st.session_state.get("gemini_key", ""), type="password")
        openai_key_input = st.text_input("OpenAI API Key (Optional)", value=st.session_state.get("openai_key", ""), type="password")

        save_btn = st.form_submit_button("💾 Save Settings", use_container_width=True)

        if save_btn:
            new_settings = {
                "baseline_window": baseline_window,
                "detection_method": detection_method,
                "threshold": threshold,
                "email_recipient": email_recipient,
                "email_enabled": email_enabled,
                "min_email_severity": min_email_severity
            }
            db.save_settings(new_settings)

            # Update email service runtime credentials
            email_service.server = smtp_server
            email_service.port = smtp_port
            email_service.username = smtp_username
            email_service.password = smtp_password

            st.session_state["gemini_key"] = gemini_key_input
            st.session_state["openai_key"] = openai_key_input

            st.success("✅ Settings updated successfully!")

    st.markdown("---")
    st.markdown("### 🧪 Test Email Alert Connection")
    test_email_target = st.text_input("Test Recipient Address", value=current_settings.get("email_recipient", ""))
    
    if st.button("📨 Send Test Alert Email"):
        if not test_email_target:
            st.error("Please enter a valid recipient email address.")
        else:
            with st.spinner("Sending test email alert..."):
                success, msg = email_service.send_test_email(test_email_target)
                if success:
                    st.success(f"🎉 {msg}")
                else:
                    st.error(f"❌ {msg}")
