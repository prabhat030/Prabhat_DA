"""
Unit tests for DataLoader and DataCleaner modules.
"""

import unittest
import pandas as pd
import numpy as np
from src.data_loader import DataLoader
from src.data_cleaner import DataCleaner


class TestDataLoaderAndCleaner(unittest.TestCase):

    def setUp(self):
        # Create a sample synthetic DataFrame
        self.raw_data = {
            "Date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"],
            "Revenue": [1000.0, 1050.0, None, 1200.0, 800.0],
            "Orders": [50, 52, 55, 60, 40],
            "Traffic": [2000, 2100, 2050, 2200, 1800]
        }
        self.df = pd.DataFrame(self.raw_data)

    def test_column_type_detection(self):
        loader = DataLoader.__new__(DataLoader)
        loader.df = self.df.copy()
        loader._detect_column_types()

        self.assertEqual(loader.date_col, "Date")
        self.assertIn("Revenue", loader.numeric_cols)
        self.assertIn("Orders", loader.numeric_cols)
        self.assertIn("Traffic", loader.numeric_cols)

    def test_data_cleaner_imputation_and_audit(self):
        cleaner = DataCleaner(self.df, date_col="Date", numeric_cols=["Revenue", "Orders", "Traffic"])
        clean_df, audit = cleaner.clean_and_audit()

        self.assertEqual(len(clean_df), 5)
        self.assertFalse(clean_df["Revenue"].isnull().any())
        self.assertEqual(audit["total_missing_values"], 1)


if __name__ == "__main__":
    unittest.main()
