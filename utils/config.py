"""
Configuration management module for AI Anomaly Agent.
Loads environment variables, default settings, and app-wide constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATABASE_DIR / "anomaly_agent.db"))

# Data directory
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DATA_PATH = DATA_DIR / "sample_business_data.xlsx"
SAMPLE_DATA_CSV = DATA_DIR / "sample_business_data.csv"

# Detection Defaults
DEFAULT_BASELINE_WINDOW = 14  # Days/observations
DEFAULT_DETECTION_METHOD = "Moving Average"
DEFAULT_THRESHOLD_PERCENT = 20.0  # % deviation for flagging
DEFAULT_Z_THRESHOLD = 2.0  # Z-score threshold
DEFAULT_ISOLATION_CONTAMINATION = 0.05  # Isolation Forest contamination

# Severity Levels & Color Schemes
SEVERITY_LEVELS = ["Normal", "Low", "Medium", "High", "Critical"]

SEVERITY_COLORS = {
    "Normal": "#10B981",    # Emerald Green
    "Low": "#3B82F6",       # Blue
    "Medium": "#F59E0B",    # Amber/Yellow
    "High": "#EF4444",      # Red
    "Critical": "#8B5CF6"   # Purple/Dark Red
}

SEVERITY_THRESHOLDS_PERCENT = {
    "Normal": (0.0, 10.0),
    "Low": (10.0, 20.0),
    "Medium": (20.0, 30.0),
    "High": (30.0, 50.0),
    "Critical": (50.0, float("inf"))
}

# Standard Business Metrics List & Aliases
SUPPORTED_METRICS = {
    "Revenue": {"aliases": ["revenue", "sales", "turnover", "total_revenue", "gross_revenue"], "format": "currency"},
    "Orders": {"aliases": ["orders", "order_count", "transactions", "total_orders"], "format": "integer"},
    "Traffic": {"aliases": ["traffic", "visitors", "sessions", "page_views", "users"], "format": "integer"},
    "Conversion_Rate": {"aliases": ["conversion_rate", "conversion", "cvr", "conv_rate", "conversion%"], "format": "percentage"},
    "Cost": {"aliases": ["cost", "marketing_cost", "spend", "expenses", "ad_spend"], "format": "currency"},
    "Refunds": {"aliases": ["refunds", "refund_amount", "returns", "refund_count"], "format": "currency"},
    "Average_Order_Value": {"aliases": ["average_order_value", "aov", "avg_order_value"], "format": "currency"},
    "Customer_Acquisition_Cost": {"aliases": ["customer_acquisition_cost", "cac", "avg_cac"], "format": "currency"},
    "Profit": {"aliases": ["profit", "net_profit", "margin", "earnings"], "format": "currency"}
}

# SMTP Email Alert Settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_SENDER_EMAIL = os.getenv("ALERT_SENDER_EMAIL", "")
ALERT_DEFAULT_RECIPIENT = os.getenv("ALERT_DEFAULT_RECIPIENT", "")

# AI API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
