"""
Data cleaning and validation module for business datasets.
"""

from typing import Dict, Tuple, List, Any, Optional
import pandas as pd
import numpy as np


class DataCleaner:
    """Cleans business datasets safely and provides Data Quality Audit statistics."""

    def __init__(self, df: pd.DataFrame, date_col: Optional[str], numeric_cols: List[str]):
        self.raw_df = df.copy()
        self.date_col = date_col
        self.numeric_cols = numeric_cols
        self.clean_df: Optional[pd.DataFrame] = None
        self.audit_results: Dict[str, Any] = {}

    def clean_and_audit(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Executes data cleaning pipeline:
        1. Date parsing and sorting
        2. Numeric type coercion
        3. Missing value analysis and imputation
        4. Duplicate row removal
        5. Quality audit compilation
        """
        df = self.raw_df.copy()
        initial_rows = len(df)

        # 1. Audit missing and duplicate info before cleaning
        missing_by_col = df.isnull().sum().to_dict()
        total_missing = sum(missing_by_col.values())
        duplicate_rows = int(df.duplicated().sum())

        # Drop exact duplicate rows
        df = df.drop_duplicates().reset_index(drop=True)

        # 2. Date Column Processing
        date_start = None
        date_end = None
        if self.date_col and self.date_col in df.columns:
            df[self.date_col] = pd.to_datetime(df[self.date_col], errors='coerce')
            # Drop rows where date could not be parsed
            df = df.dropna(subset=[self.date_col])
            df = df.sort_values(by=self.date_col).reset_index(drop=True)
            if not df.empty:
                date_start = df[self.date_col].min().strftime('%Y-%m-%d')
                date_end = df[self.date_col].max().strftime('%Y-%m-%d')

        # 3. Numeric Metrics Cleaning
        negative_values_found = {}
        for col in self.numeric_cols:
            if col in df.columns:
                # Coerce to numeric
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Check negative values
                neg_count = int((df[col] < 0).sum())
                if neg_count > 0:
                    negative_values_found[col] = neg_count

                # Forward fill then backward fill missing values to maintain time-series continuity
                df[col] = df[col].ffill().bfill()
                # If still null (e.g. all NaNs), fill with 0
                df[col] = df[col].fillna(0)

        self.clean_df = df

        # 4. Construct Quality Audit Report
        self.audit_results = {
            "total_rows_raw": initial_rows,
            "total_rows_clean": len(self.clean_df),
            "total_columns": len(self.clean_df.columns),
            "duplicate_rows_removed": duplicate_rows,
            "total_missing_values": total_missing,
            "missing_by_column": missing_by_col,
            "negative_values_found": negative_values_found,
            "date_range_start": date_start,
            "date_range_end": date_end,
            "date_column_used": self.date_col,
            "metrics_detected": self.numeric_cols
        }

        return self.clean_df, self.audit_results
