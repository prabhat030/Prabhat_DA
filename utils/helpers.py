"""
Helper functions for formatting numbers, dates, currency, and UI elements.
"""

from typing import Union, Optional
from utils.config import SEVERITY_COLORS


def format_value(value: Union[int, float], fmt_type: str = "number", currency_symbol: str = "₹") -> str:
    """Format a numeric value based on its metric type."""
    if value is None or (isinstance(value, float) and float('nan') == value):
        return "N/A"
        
    if fmt_type == "currency":
        if abs(value) >= 1_000_000:
            return f"{currency_symbol}{value / 1_000_000:,.2f}M"
        elif abs(value) >= 1_000:
            return f"{currency_symbol}{value:,.2f}"
        else:
            return f"{currency_symbol}{value:,.2f}"
    elif fmt_type == "percentage":
        return f"{value:.2f}%"
    elif fmt_type == "integer":
        return f"{int(round(value)):,}"
    else:
        return f"{value:,.2f}"


def format_delta(delta_pct: float) -> str:
    """Format percentage change with plus sign and direction icon."""
    if delta_pct is None:
        return "N/A"
    prefix = "+" if delta_pct > 0 else ""
    return f"{prefix}{delta_pct:.2f}%"


def get_severity_badge_html(severity: str) -> str:
    """Generate HTML snippet for a stylized severity badge."""
    color = SEVERITY_COLORS.get(severity, "#6B7280")
    return (
        f'<span style="background-color: {color}22; color: {color}; '
        f'border: 1px solid {color}; padding: 3px 10px; border-radius: 12px; '
        f'font-weight: 600; font-size: 0.85rem; display: inline-block;">'
        f'{severity.upper()}'
        f'</span>'
    )


def get_status_indicator_html(status: str) -> str:
    """Generate HTML snippet for status badge (e.g., Anomaly vs Normal)."""
    if status.lower() == "anomaly":
        return (
            '<span style="background-color: #EF444422; color: #EF4444; '
            'border: 1px solid #EF4444; padding: 3px 8px; border-radius: 6px; font-weight: 600;">'
            '⚠️ Anomaly</span>'
        )
    else:
        return (
            '<span style="background-color: #10B98122; color: #10B981; '
            'border: 1px solid #10B981; padding: 3px 8px; border-radius: 6px; font-weight: 600;">'
            '✅ Normal</span>'
        )
