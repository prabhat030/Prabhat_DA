"""
Business metrics definition, aliases, and metric relationships module.
"""

from typing import Dict, List, Optional
from utils.config import SUPPORTED_METRICS


class MetricRegistry:
    """Registry for business metrics, column matching, formatting, and relations."""

    @staticmethod
    def get_supported_metrics() -> Dict[str, dict]:
        return SUPPORTED_METRICS

    @staticmethod
    def match_column_name(col_name: str) -> Optional[str]:
        """
        Match a dataframe column name to a standard business metric name.
        Example: 'revenue_inr' -> 'Revenue', 'marketing_spend' -> 'Cost'.
        """
        normalized = col_name.strip().lower().replace(" ", "_").replace("-", "_")

        for standard_name, meta in SUPPORTED_METRICS.items():
            if normalized == standard_name.lower():
                return standard_name
            for alias in meta["aliases"]:
                if alias in normalized:
                    return standard_name
        return None

    @staticmethod
    def get_format_type(metric_name: str) -> str:
        """Get formatting type (currency, percentage, integer, float) for metric."""
        if metric_name in SUPPORTED_METRICS:
            return SUPPORTED_METRICS[metric_name]["format"]
        
        # Heuristics for custom metrics
        lower_name = metric_name.lower()
        if any(kw in lower_name for kw in ["revenue", "cost", "spend", "profit", "aov", "cac", "refund", "price"]):
            return "currency"
        elif any(kw in lower_name for kw in ["rate", "ratio", "percent", "cvr", "%"]):
            return "percentage"
        elif any(kw in lower_name for kw in ["count", "orders", "traffic", "users", "sessions"]):
            return "integer"
        return "number"

    @staticmethod
    def get_related_metrics(metric_name: str) -> List[str]:
        """
        Return related metrics to investigate when a given metric shows an anomaly.
        """
        relationships = {
            "Revenue": ["Orders", "Average_Order_Value", "Traffic", "Conversion_Rate", "Refunds"],
            "Orders": ["Traffic", "Conversion_Rate", "Revenue", "Average_Order_Value"],
            "Traffic": ["Conversion_Rate", "Orders", "Cost"],
            "Conversion_Rate": ["Traffic", "Orders", "Revenue"],
            "Cost": ["Customer_Acquisition_Cost", "Traffic", "Revenue", "Profit"],
            "Refunds": ["Revenue", "Orders"],
            "Average_Order_Value": ["Revenue", "Orders"],
            "Customer_Acquisition_Cost": ["Cost", "Traffic", "Orders"],
            "Profit": ["Revenue", "Cost", "Refunds"]
        }
        return relationships.get(metric_name, [])
