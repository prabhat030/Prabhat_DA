"""
Data loading and auto-detection module for Excel and CSV business files.
"""

import io
from typing import Dict, List, Tuple, Union, Optional
import pandas as pd
import numpy as np
from src.metrics import MetricRegistry


class DataLoader:
    """Handles file reading, date column identification, and metric detection."""

    def __init__(self, file_path_or_buffer: Union[str, io.BytesIO], filename: Optional[str] = None):
        self.source = file_path_or_buffer
        self.filename = filename if filename else (file_path_or_buffer if isinstance(file_path_or_buffer, str) else "uploaded_file.csv")
        self.df: Optional[pd.DataFrame] = None
        self.date_col: Optional[str] = None
        self.numeric_cols: List[str] = []
        self.metric_mapping: Dict[str, str] = {}
        self.load_errors: List[str] = []

    def load(self) -> pd.DataFrame:
        """Read CSV or Excel into Pandas DataFrame."""
        try:
            if isinstance(self.source, str):
                if self.source.endswith(".xlsx") or self.source.endswith(".xls"):
                    self.df = pd.read_excel(self.source)
                else:
                    self.df = pd.read_csv(self.source)
            else:
                if self.filename.endswith(".xlsx") or self.filename.endswith(".xls"):
                    self.df = pd.read_excel(self.source)
                else:
                    self.df = pd.read_csv(self.source)

            # Strip column whitespace
            self.df.columns = [str(col).strip() for col in self.df.columns]
            
            # Detect Date and Numeric columns
            self._detect_column_types()
            return self.df
        except Exception as e:
            self.load_errors.append(f"Failed to load file: {str(e)}")
            raise ValueError(f"Error loading business dataset: {str(e)}")

    def _detect_column_types(self):
        """Identify date column and numeric metric columns automatically."""
        if self.df is None or self.df.empty:
            return

        # 1. Identify Date Column
        date_candidates = []
        for col in self.df.columns:
            col_lower = str(col).lower()
            if any(kw in col_lower for kw in ["date", "time", "day", "dt", "period", "timestamp"]):
                date_candidates.append(col)

        # Try parsing date candidates first, or attempt all object/string columns
        selected_date_col = None
        if date_candidates:
            for cand in date_candidates:
                try:
                    pd.to_datetime(self.df[cand], errors='raise')
                    selected_date_col = cand
                    break
                except Exception:
                    continue

        if not selected_date_col:
            # Fallback check all columns
            for col in self.df.columns:
                if self.df[col].dtype == 'object' or 'datetime' in str(self.df[col].dtype):
                    try:
                        converted = pd.to_datetime(self.df[col], errors='coerce')
                        if converted.notnull().sum() / len(self.df) > 0.7:
                            selected_date_col = col
                            break
                    except Exception:
                        continue

        self.date_col = selected_date_col

        # 2. Identify Numeric Metric Columns
        self.numeric_cols = []
        self.metric_mapping = {}

        for col in self.df.columns:
            if col == self.date_col:
                continue

            # Check if column is numeric or can be coerced to numeric
            numeric_series = pd.to_numeric(self.df[col], errors='coerce')
            non_null_ratio = numeric_series.notnull().sum() / len(self.df)

            if non_null_ratio > 0.5 and self.df[col].nunique() > 1:
                self.numeric_cols.append(col)
                # Map to standard metric if available
                standard_name = MetricRegistry.match_column_name(col)
                if standard_name:
                    self.metric_mapping[col] = standard_name
                else:
                    # Clean title
                    self.metric_mapping[col] = col.replace("_", " ").title()

    def get_summary(self) -> dict:
        """Return dataset structure summary."""
        if self.df is None:
            return {}

        return {
            "filename": self.filename,
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "date_column": self.date_col,
            "numeric_metrics": self.numeric_cols,
            "metric_mapping": self.metric_mapping,
            "columns": list(self.df.columns)
        }
