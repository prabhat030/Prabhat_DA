"""
Script to generate a realistic 180+ day sample business metrics dataset
with inserted synthetic business anomalies for testing and demonstration.
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Create data directory
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def generate_business_dataset(num_days: int = 180) -> pd.DataFrame:
    """Generate 180-day realistic e-commerce/business metrics dataset."""
    np.random.seed(42)
    start_date = datetime(2026, 4, 1)

    dates = [start_date + timedelta(days=i) for i in range(num_days)]
    
    # Baseline trends
    day_of_week = np.array([d.weekday() for d in dates])
    seasonality = 1.0 + 0.15 * np.sin(2 * np.pi * day_of_week / 7) # Weekly wave

    # Base Metrics
    traffic = np.random.normal(loc=12000, scale=800, size=num_days) * seasonality
    cvr = np.random.normal(loc=3.2, scale=0.2, size=num_days) # 3.2% conversion rate
    cvr = np.clip(cvr, 1.5, 6.0)

    orders = (traffic * (cvr / 100.0)).astype(int)
    aov = np.random.normal(loc=1450.0, scale=50.0, size=num_days) # ₹1,450 AOV
    
    revenue = orders * aov
    cost = np.random.normal(loc=45000.0, scale=3000.0, size=num_days) * seasonality
    refunds = revenue * np.random.uniform(low=0.02, high=0.04, size=num_days) # 2-4% refund rate
    profit = revenue - cost - refunds

    df = pd.DataFrame({
        "Date": [d.strftime("%Y-%m-%d") for d in dates],
        "Revenue": np.round(revenue, 2),
        "Orders": orders,
        "Traffic": np.round(traffic).astype(int),
        "Conversion_Rate": np.round(cvr, 2),
        "Marketing_Cost": np.round(cost, 2),
        "Refunds": np.round(refunds, 2),
        "Average_Order_Value": np.round(aov, 2),
        "Profit": np.round(profit, 2)
    })

    # --- ARTIFICIAL ANOMALIES INSERTION ---

    # Anomaly 1: Day 45 - Large Revenue Drop (-35%) & Order Drop
    df.loc[45, "Revenue"] = df.loc[45, "Revenue"] * 0.65
    df.loc[45, "Orders"] = int(df.loc[45, "Orders"] * 0.65)
    df.loc[45, "Profit"] = df.loc[45, "Revenue"] - df.loc[45, "Marketing_Cost"] - df.loc[45, "Refunds"]

    # Anomaly 2: Day 80 - Viral Marketing Traffic Surge (+65%) & CVR Drop
    df.loc[80, "Traffic"] = int(df.loc[80, "Traffic"] * 1.65)
    df.loc[80, "Conversion_Rate"] = round(df.loc[80, "Conversion_Rate"] * 0.6, 2)

    # Anomaly 3: Day 110 - Payment Gateway Outage (Conversion Rate -45% & Revenue -42%)
    df.loc[110, "Conversion_Rate"] = round(df.loc[110, "Conversion_Rate"] * 0.55, 2)
    df.loc[110, "Orders"] = int(df.loc[110, "Traffic"] * (df.loc[110, "Conversion_Rate"] / 100.0))
    df.loc[110, "Revenue"] = round(df.loc[110, "Orders"] * df.loc[110, "Average_Order_Value"], 2)
    df.loc[110, "Profit"] = df.loc[110, "Revenue"] - df.loc[110, "Marketing_Cost"] - df.loc[110, "Refunds"]

    # Anomaly 4: Day 135 - Refund Surge (+160% due to damaged inventory)
    df.loc[135, "Refunds"] = round(df.loc[135, "Refunds"] * 2.6, 2)
    df.loc[135, "Profit"] = df.loc[135, "Revenue"] - df.loc[135, "Marketing_Cost"] - df.loc[135, "Refunds"]

    # Anomaly 5: Day 160 - Ad Campaign Overspend (Marketing Cost +75%, Revenue flat)
    df.loc[160, "Marketing_Cost"] = round(df.loc[160, "Marketing_Cost"] * 1.75, 2)
    df.loc[160, "Profit"] = df.loc[160, "Revenue"] - df.loc[160, "Marketing_Cost"] - df.loc[160, "Refunds"]

    # Anomaly 6: Day 175 - Severe Shipping Interruption (Orders -50%)
    df.loc[175, "Orders"] = int(df.loc[175, "Orders"] * 0.5)
    df.loc[175, "Revenue"] = round(df.loc[175, "Orders"] * df.loc[175, "Average_Order_Value"], 2)
    df.loc[175, "Profit"] = df.loc[175, "Revenue"] - df.loc[175, "Marketing_Cost"] - df.loc[175, "Refunds"]

    return df


def main():
    print("Generating sample business dataset with realistic anomalies...")
    df = generate_business_dataset(num_days=180)
    
    excel_path = DATA_DIR / "sample_business_data.xlsx"
    csv_path = DATA_DIR / "sample_business_data.csv"

    df.to_excel(excel_path, index=False, engine="openpyxl")
    df.to_csv(csv_path, index=False)

    print(f"Sample dataset saved successfully to:\n - {excel_path}\n - {csv_path}")
    print(f"Total Rows: {len(df)}, Columns: {list(df.columns)}")


if __name__ == "__main__":
    main()
