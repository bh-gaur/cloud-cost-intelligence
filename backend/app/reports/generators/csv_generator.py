"""
CSV Report Generator
Emits structured, tabular CSV data formatted for clean spreadsheet rendering in Excel and Google Sheets.
"""

import csv
import io
from typing import Any, Dict


class CSVReportGenerator:
    def generate(self, data: Dict[str, Any]) -> str:
        """Serializes report data to formatted CSV string with consistent 8-column layout."""
        output = io.StringIO()
        writer = csv.writer(output)

        TOTAL_COLS = 8

        def row(cells):
            # Pad or slice to exactly TOTAL_COLS for consistent spreadsheet columns
            padded = list(cells) + [""] * (TOTAL_COLS - len(cells))
            writer.writerow(padded[:TOTAL_COLS])

        def empty_row():
            writer.writerow([""] * TOTAL_COLS)

        def section_banner(title: str):
            row([f"=== {title} ==="])

        # Executive Summary Block
        row(["AWS COST INTELLIGENCE EXECUTIVE REPORT"])
        row(["Generated At", data.get("generated_at", "")])
        row(["Billing Period", f"{data.get('start_date', '')} to {data.get('end_date', '')}"])
        row(["Account Scope", data.get("account_id", "All Accounts")])
        row(["Total Period Spend", f"${data.get('total_cost', 0):,.2f} USD"])
        row(["Prior Period Spend", f"${data.get('previous_cost', 0):,.2f} USD"])
        diff_val = data.get('difference', 0)
        diff_prefix = "+" if diff_val > 0 else ""
        row(["Variance", f"{diff_prefix}${diff_val:,.2f} ({data.get('percentage_change', 0):.2f}%)"])
        row(["Potential Monthly Savings", f"${data.get('potential_monthly_savings', 0):,.2f} USD"])
        empty_row()

        # Service Breakdown
        section_banner("SERVICE BREAKDOWN")
        row(["Service Name", "Category", "Cost (USD)", "% of Total", "Trend"])
        for svc in data.get("services", []):
            row([
                svc.get("service", "Unknown"),
                svc.get("category", "Other"),
                f"${svc.get('current_cost', 0):,.2f}",
                f"{svc.get('percentage_of_total', 0):.2f}%",
                svc.get("trend", "FLAT"),
            ])
        empty_row()

        # Account Breakdown
        section_banner("ACCOUNT BREAKDOWN")
        row(["Account Name", "Account ID", "Cost (USD)", "% of Total"])
        for acc in data.get("accounts", []):
            row([
                acc.get("account_name", "AWS Account"),
                acc.get("account_id", ""),
                f"${acc.get('monthly_cost', 0):,.2f}",
                f"{acc.get('percentage_of_total', 0):.2f}%",
            ])
        empty_row()

        # FinOps Optimization Recommendations
        section_banner("FINOPS OPTIMIZATION RECOMMENDATIONS")
        row(["Rule ID", "Service", "Resource ID", "Est Monthly Savings", "Priority", "Confidence", "Status", "Recommendation"])
        recs = data.get("recommendations", [])
        if recs:
            for rec in recs:
                row([
                    rec.get("rule_id", ""),
                    rec.get("service", ""),
                    rec.get("resource_id", ""),
                    f"${rec.get('estimated_monthly_savings', 0):,.2f}",
                    rec.get("priority", "MEDIUM"),
                    rec.get("confidence", "Observed"),
                    rec.get("validation_status", "Requires validation"),
                    rec.get("recommendation", ""),
                ])
        else:
            row(["No active optimization recommendations identified for this period."])

        empty_row()
        row(["END OF REPORT", "Cloud Cost Intelligence Platform"])

        return output.getvalue()
