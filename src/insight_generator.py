"""
AI & Rule-Based Natural Language Insight Generator.
Considers multi-metric correlations to generate actionable business explanations
and executive summaries without claiming unproven causation.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import requests
from utils.config import GEMINI_API_KEY, OPENAI_API_KEY
from utils.helpers import format_value
from src.metrics import MetricRegistry


class InsightGenerator:
    """Generates natural language business insights and executive summaries."""

    @staticmethod
    def generate_single_anomaly_explanation(
        target_metric: str,
        current_val: float,
        baseline_val: float,
        dev_pct: float,
        severity: str,
        row_data: Dict[str, float]
    ) -> Dict[str, str]:
        """
        Generate a multi-metric explanation structure for a single detected anomaly.
        """
        fmt_type = MetricRegistry.get_format_type(target_metric)
        curr_str = format_value(current_val, fmt_type)
        base_str = format_value(baseline_val, fmt_type)
        direction = "decreased" if dev_pct < 0 else "increased"
        abs_pct = abs(dev_pct)

        # Related metric analysis
        related_observations = []
        possible_impact = ""
        recommended_check = ""

        # Check related metrics in row_data
        rev_change = row_data.get("Revenue_dev", 0.0)
        orders_change = row_data.get("Orders_dev", 0.0)
        traffic_change = row_data.get("Traffic_dev", 0.0)
        cvr_change = row_data.get("Conversion_Rate_dev", 0.0)
        cost_change = row_data.get("Cost_dev", 0.0)
        refunds_change = row_data.get("Refunds_dev", 0.0)
        aov_change = row_data.get("Average_Order_Value_dev", 0.0)

        t_clean = target_metric.lower()

        if "revenue" in t_clean:
            if dev_pct < 0:
                if abs(traffic_change) < 5.0 and cvr_change < -5.0:
                    related_observations.append("website traffic remained stable while conversion rate declined")
                    explanation_core = f"Revenue dropped {abs_pct:.1f}% ({curr_str} vs baseline {base_str}). At the same time, website traffic remained stable while conversion rate declined by {abs(cvr_change):.1f}%. This suggests the revenue decline may be related to weaker conversion rather than lower traffic."
                    possible_impact = "Loss of sales efficiency and reduced revenue realization per visitor."
                    recommended_check = "Review conversion funnel, checkout flow, payment gateway failure rates, and pricing changes."
                elif traffic_change < -10.0:
                    related_observations.append(f"traffic declined by {abs(traffic_change):.1f}%")
                    explanation_core = f"Revenue fell {abs_pct:.1f}%, coinciding with a {abs(traffic_change):.1f}% reduction in traffic. This points toward a potential top-of-funnel customer acquisition bottleneck."
                    possible_impact = "Lower overall store throughput and reduced customer acquisition volume."
                    recommended_check = "Check active ad channels, SEO rankings, link integrity, and marketing campaign delivery."
                elif orders_change < -10.0 and abs(aov_change) < 5.0:
                    explanation_core = f"Revenue dropped {abs_pct:.1f}% driven primarily by a {abs(orders_change):.1f}% fall in order volume, while Average Order Value remained steady."
                    possible_impact = "Declining customer purchase frequency or lower demand."
                    recommended_check = "Investigate promotional offers, competitor activity, and customer segment activity."
                else:
                    explanation_core = f"Revenue dropped {abs_pct:.1f}% compared with the recent baseline of {base_str}."
                    possible_impact = "Top-line revenue contraction."
                    recommended_check = "Conduct a complete breakdown of sales channels, top products, and conversion metrics."
            else: # Revenue increased
                if orders_change > 10.0:
                    explanation_core = f"Revenue increased {abs_pct:.1f}% ({curr_str} vs baseline {base_str}), supported by a {orders_change:.1f}% rise in total order volume."
                    possible_impact = "Positive demand expansion and higher top-line growth."
                    recommended_check = "Evaluate inventory levels to prevent stockouts and sustain high demand."
                elif aov_change > 10.0:
                    explanation_core = f"Revenue surged {abs_pct:.1f}% while order volume remained stable, pointing toward an increase in Average Order Value (AOV)."
                    possible_impact = "Higher basket size and improved customer spend efficiency."
                    recommended_check = "Analyze upsell performance, premium product sales, and cross-sell promotions."
                else:
                    explanation_core = f"Revenue increased {abs_pct:.1f}% above the historical baseline."
                    possible_impact = "Revenue acceleration."
                    recommended_check = "Identify key contributing marketing channels or campaign drivers."

        elif "conversion" in t_clean or "cvr" in t_clean:
            if dev_pct < 0:
                if traffic_change > 10.0:
                    explanation_core = f"Conversion rate dropped {abs_pct:.1f}% while traffic increased by {traffic_change:.1f}%. This suggests recent traffic quality may have decreased or campaign targeting shifted."
                    possible_impact = "Wasted marketing spend on low-intent traffic."
                    recommended_check = "Audit new ad copy, audience targeting parameters, and landing page relevance."
                else:
                    explanation_core = f"Conversion rate experienced a {abs_pct:.1f}% drop compared with baseline."
                    possible_impact = "Reduced conversion efficiency."
                    recommended_check = "Check website page load times, checkout page errors, and cart abandonment rates."
            else:
                explanation_core = f"Conversion rate improved by {abs_pct:.1f}% over the baseline."
                possible_impact = "Enhanced store UX and purchase intent."
                recommended_check = "Document recent UI changes or promotional drivers to replicate success."

        elif "cost" in t_clean or "spend" in t_clean:
            if dev_pct > 0:
                if rev_change < 5.0:
                    explanation_core = f"Marketing Cost surged {abs_pct:.1f}% ({curr_str} vs {base_str}) while Revenue remained relatively flat. This points toward lower marketing ROI and margin compression."
                    possible_impact = "Profitability degradation and inflated Customer Acquisition Cost (CAC)."
                    recommended_check = "Pause underperforming ad sets, inspect bidding strategy, and re-allocate budget."
                else:
                    explanation_core = f"Marketing Cost increased {abs_pct:.1f}%, aligned with increased campaign scaling."
                    possible_impact = "Increased expense commitment."
                    recommended_check = "Ensure return on ad spend (ROAS) remains above target efficiency threshold."
            else:
                explanation_core = f"Cost decreased {abs_pct:.1f}% below baseline."
                possible_impact = "Short-term expense savings."
                recommended_check = "Verify whether budget caps or campaign pauses led to unintended volume drops."

        elif "refund" in t_clean:
            if dev_pct > 0:
                explanation_core = f"Refunds spiked {abs_pct:.1f}% ({curr_str} vs baseline {base_str}). This could be associated with product quality issues, shipping delays, or incorrect billing."
                possible_impact = "Margin erosion, revenue clawbacks, and risk of customer churn."
                recommended_check = "Inspect recent refund reason codes, customer support tickets, and fulfillment logs."
            else:
                explanation_core = f"Refunds decreased by {abs_pct:.1f}%."
                possible_impact = "Reduced return liabilities."
                recommended_check = "Maintain current fulfillment and quality standard."

        elif "traffic" in t_clean:
            if dev_pct < 0:
                explanation_core = f"Traffic dropped {abs_pct:.1f}% ({curr_str} vs baseline {base_str}), indicating a potential decline in incoming audience volume."
                possible_impact = "Smaller sales funnel top and risk of lower downstream orders."
                recommended_check = "Verify organic search positions, active PPC campaigns, and referral links."
            else:
                explanation_core = f"Traffic surged {abs_pct:.1f}% above historical average."
                possible_impact = "Increased store exposure."
                recommended_check = "Check server performance and monitor conversion rates for new visitors."

        else:
            # Generic Metric Explanation
            explanation_core = (
                f"{target_metric} {direction} by {abs_pct:.1f}% compared with the recent baseline. "
                f"Observed value: {curr_str}, Baseline: {base_str}. "
                f"This shift represents a {severity.lower()} severity anomaly worth investigating."
            )
            possible_impact = f"Potential shift in overall business performance regarding {target_metric}."
            recommended_check = f"Audit contributing factors and cross-metric metrics related to {target_metric}."

        return {
            "explanation": explanation_core,
            "possible_impact": possible_impact,
            "recommended_check": recommended_check
        }

    @classmethod
    def generate_executive_summary(
        cls,
        detected_anomalies: List[Dict[str, Any]],
        baseline_period: int,
        gemini_key: str = GEMINI_API_KEY,
        openai_key: str = OPENAI_API_KEY
    ) -> str:
        """
        Generate 3-6 sentence executive summary of detected anomalies.
        Attempts Gemini/OpenAI API call if key is provided; falls back to rule-based summary automatically.
        """
        if not detected_anomalies:
            return "Executive Monitoring Summary: All monitored business metrics are performing within normal baseline parameters. No significant metric anomalies or operational deviations were detected during this analysis window."

        # Filter significant anomalies (High, Critical, Medium)
        key_anomalies = [a for a in detected_anomalies if a.get("severity") in ["Critical", "High", "Medium"]]
        if not key_anomalies:
            key_anomalies = detected_anomalies

        # 1. Try Gemini API if key is present
        if gemini_key:
            try:
                summary = cls._call_gemini_api(key_anomalies, baseline_period, gemini_key)
                if summary:
                    return summary
            except Exception:
                pass  # Graceful fallback to rule-based engine

        # 2. Rule-Based Natural Language Executive Summary
        return cls._generate_rule_based_executive_summary(key_anomalies, baseline_period)

    @staticmethod
    def _generate_rule_based_executive_summary(anomalies: List[Dict[str, Any]], window: int) -> str:
        """Rule-based 3-6 sentence executive summary generator."""
        count = len(anomalies)
        critical_count = sum(1 for a in anomalies if a.get("severity") == "Critical")
        high_count = sum(1 for a in anomalies if a.get("severity") == "High")

        sentences = []
        
        # Sentence 1: Overview
        if critical_count > 0:
            sentences.append(
                f"Today's automated monitoring identified {count} metric anomalies, including {critical_count} CRITICAL severity alert(s) requiring immediate operational attention."
            )
        elif high_count > 0:
            sentences.append(
                f"Today's automated monitoring flagged {count} significant anomaly event(s) across key business metrics evaluated against a {window}-day baseline."
            )
        else:
            sentences.append(
                f"Monitoring analysis identified {count} minor-to-moderate metric deviation(s) compared with the historical {window}-day baseline."
            )

        # Sentence 2 & 3: Highlight top anomalies
        top_anomalies = sorted(anomalies, key=lambda x: abs(x.get("deviation_pct", 0)), reverse=True)[:3]
        metric_bullets = []
        for a in top_anomalies:
            m = a.get("metric_name", "Metric")
            dev = a.get("deviation_pct", 0)
            curr = a.get("current_value", 0)
            base = a.get("baseline", 0)
            fmt = MetricRegistry.get_format_type(m)
            curr_str = format_value(curr, fmt)
            base_str = format_value(base, fmt)
            direction = "declined" if dev < 0 else "increased"
            metric_bullets.append(f"{m} {direction} {abs(dev):.1f}% ({curr_str} vs baseline {base_str})")

        sentences.append("Key deviations include: " + ", ".join(metric_bullets) + ".")

        # Sentence 4: Cross-metric insights
        has_rev_drop = any("revenue" in a.get("metric_name", "").lower() and a.get("deviation_pct", 0) < 0 for a in anomalies)
        has_cvr_drop = any("conversion" in a.get("metric_name", "").lower() and a.get("deviation_pct", 0) < 0 for a in anomalies)
        has_refund_spike = any("refund" in a.get("metric_name", "").lower() and a.get("deviation_pct", 0) > 0 for a in anomalies)

        if has_rev_drop and has_cvr_drop:
            sentences.append(
                "Revenue contraction appears correlated with a simultaneous drop in conversion rate, suggesting store checkout or pricing friction rather than traffic loss."
            )
        elif has_refund_spike:
            sentences.append(
                "The surge in refunds indicates potential customer satisfaction or product delivery issues that may further impact net earnings."
            )
        else:
            sentences.append(
                "Cross-metric evaluation suggests monitoring contributing traffic and order channels to isolate the root cause."
            )

        # Sentence 5: Call to action
        sentences.append(
            "It is recommended to inspect product campaign parameters, conversion funnels, and payment gateways for the flagged periods."
        )

        return " ".join(sentences)

    @staticmethod
    def _call_gemini_api(anomalies: List[Dict[str, Any]], window: int, api_key: str) -> Optional[str]:
        """Call Gemini API REST endpoint for executive summary generation."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        prompt = (
            f"You are an expert executive business data analyst. Summarize these detected business metric anomalies in 3 to 5 clear, professional sentences for executive leadership:\n"
            f"Baseline period: {window} days.\n"
            f"Anomalies: {anomalies}\n\n"
            f"Rules:\n"
            f"1. Do not claim unproven causation. Use terms like 'may indicate', 'suggests', 'worth investigating'.\n"
            f"2. Mention the primary metric shifts and potential business impact.\n"
            f"3. Recommend specific area to check."
        )

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return None
