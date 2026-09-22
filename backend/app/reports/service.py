"""
Report Orchestration and Retention Service
Handles compiling financial data, generating files (CSV, JSON, HTML), disk persistence, and 90-day retention cleanup.
"""

import os
import uuid
import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.report import Report
from app.models.cost import CostRecord, DailyCostSummary
from app.models.optimization import OptimizationRecommendation
from app.models.alert import AlertEvent
from app.reports.generators.csv_generator import CSVReportGenerator
from app.reports.generators.json_generator import JSONReportGenerator
from app.reports.generators.html_generator import HTMLReportGenerator
from app.reports.generators.pdf_generator import PDFReportGenerator
from app.utils.money import calculate_difference_and_percentage, to_decimal

logger = logging.getLogger(__name__)


class ReportService:
    def __init__(self):
        self.csv_generator = CSVReportGenerator()
        self.json_generator = JSONReportGenerator()
        self.html_generator = HTMLReportGenerator()
        self.pdf_generator = PDFReportGenerator()

        # Ensure base directories exist
        self.output_base = Path(settings.REPORT_OUTPUT_DIR)
        for sub in ("csv", "json", "html", "pdf", "archive"):
            (self.output_base / sub).mkdir(parents=True, exist_ok=True)


    def compile_report_data(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        account_id: str = "all",
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compiles cost metrics, service summaries, accounts, and recommendations."""
        # Query total spend for current period
        cost_query = db.query(CostRecord).filter(
            CostRecord.date >= start_date, CostRecord.date <= end_date
        )
        if organization_id:
            cost_query = cost_query.filter(CostRecord.organization_id == organization_id)
        if account_id != "all":
            cost_query = cost_query.filter(CostRecord.account_id == account_id)
        current_records = cost_query.all()

        total_cost = sum((r.cost for r in current_records), Decimal("0.0000"))

        # Query previous period of equal duration for comparison
        duration = (end_date - start_date).days + 1
        prev_start = start_date - timedelta(days=duration)
        prev_end = start_date - timedelta(days=1)
        prev_query = db.query(CostRecord).filter(
            CostRecord.date >= prev_start, CostRecord.date <= prev_end
        )
        if organization_id:
            prev_query = prev_query.filter(CostRecord.organization_id == organization_id)
        if account_id != "all":
            prev_query = prev_query.filter(CostRecord.account_id == account_id)
        prev_records = prev_query.all()
        prev_cost = sum((r.cost for r in prev_records), Decimal("0.0000"))

        diff, pct, trend = calculate_difference_and_percentage(total_cost, prev_cost)

        # Service breakdown
        service_map: Dict[str, Dict[str, Any]] = {}
        for r in current_records:
            if r.service not in service_map:
                service_map[r.service] = {
                    "service": r.service,
                    "category": r.service_category,
                    "current_cost": Decimal("0.0000"),
                    "percentage_of_total": Decimal("0.00"),
                    "trend": "FLAT",
                }
            service_map[r.service]["current_cost"] += r.cost

        for s in service_map.values():
            if total_cost > Decimal("0.0000"):
                s["percentage_of_total"] = (
                    (s["current_cost"] / total_cost) * Decimal("100.00")
                ).quantize(Decimal("0.01"))

        sorted_services = sorted(
            service_map.values(), key=lambda x: x["current_cost"], reverse=True
        )

        # Account breakdown
        from app.models.account import AWSAccount
        db_accs = {
            a.account_id: a.account_name
            for a in db.query(AWSAccount).all()
        }

        account_map: Dict[str, Dict[str, Any]] = {}
        for r in current_records:
            acc_display_name = db_accs.get(r.account_id) or r.account_name or f"Account {r.account_id[-4:]}"
            if r.account_id not in account_map:
                account_map[r.account_id] = {
                    "account_id": r.account_id,
                    "account_name": acc_display_name,
                    "monthly_cost": Decimal("0.0000"),
                    "percentage_of_total": Decimal("0.00"),
                }
            account_map[r.account_id]["monthly_cost"] += r.cost

        for a in account_map.values():
            if total_cost > Decimal("0.0000"):
                a["percentage_of_total"] = (
                    (a["monthly_cost"] / total_cost) * Decimal("100.00")
                ).quantize(Decimal("0.01"))

        sorted_accounts = sorted(
            account_map.values(), key=lambda x: x["monthly_cost"], reverse=True
        )

        # Recommendations
        rec_query = db.query(OptimizationRecommendation)
        if organization_id:
            rec_query = rec_query.filter(OptimizationRecommendation.organization_id == organization_id)
        if account_id != "all":
            rec_query = rec_query.filter(OptimizationRecommendation.account_id == account_id)
        recs = rec_query.all()
        potential_monthly_savings = sum((r.estimated_monthly_savings for r in recs), Decimal("0.0000"))

        # Anomalies
        anom_query = db.query(AlertEvent).filter(AlertEvent.status == "OPEN")
        if organization_id:
            anom_query = anom_query.filter(AlertEvent.organization_id == organization_id)
        anomalies = anom_query.all()

        return {
            "name": f"aws-cost-report-{end_date.strftime('%Y-%m-%d')}",
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "account_id": account_id,
            "total_cost": total_cost,
            "previous_cost": prev_cost,
            "difference": diff,
            "percentage_change": pct,
            "trend": trend,
            "services": sorted_services,
            "accounts": sorted_accounts,
            "recommendations": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "service": r.service,
                    "resource_id": r.resource_id,
                    "estimated_monthly_savings": r.estimated_monthly_savings,
                    "priority": r.priority,
                    "confidence": r.confidence,
                    "validation_status": r.validation_status,
                    "recommendation": r.recommendation,
                    "action_required": r.action_required,
                }
                for r in recs
            ],
            "potential_monthly_savings": potential_monthly_savings,
            "anomalies": [
                {"id": a.id, "title": a.title, "severity": a.severity, "message": a.message}
                for a in anomalies
            ],
        }

    def generate_report(
        self,
        db: Session,
        fmt: str,
        start_date: date,
        end_date: date,
        account_id: str = "all",
        user_id: Optional[str] = None,
        custom_name: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Report:
        """Generates report file and records metadata in database."""
        if not organization_id:
            from app.models.organization import Organization
            default_org = db.query(Organization).filter(Organization.slug == "default-org").first()
            if default_org:
                organization_id = default_org.id
            else:
                organization_id = str(uuid.uuid4())

        report_data = self.compile_report_data(
            db, start_date, end_date, account_id, organization_id=organization_id
        )
        fmt = fmt.lower()
        if fmt not in ("csv", "json", "html", "pdf"):
            raise ValueError(f"Unsupported report format: {fmt}")

        report_id = str(uuid.uuid4())
        date_stamp = end_date.strftime("%Y-%m-%d")
        base_name = custom_name or f"aws-cost-report-{date_stamp}"
        filename = f"{base_name}-{report_id[:8]}.{fmt}"
        
        # Tenant-isolated report storage path: reports/{org_id}/{year}/{month}/filename
        year_str = end_date.strftime("%Y")
        month_str = end_date.strftime("%m")
        tenant_dir = self.output_base / organization_id / year_str / month_str
        tenant_dir.mkdir(parents=True, exist_ok=True)
        file_path = tenant_dir / filename

        # Render and write content
        if fmt == "csv":
            content = self.csv_generator.generate(report_data)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        elif fmt == "json":
            content = self.json_generator.generate(report_data)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        elif fmt == "html":
            content = self.html_generator.generate(report_data)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        elif fmt == "pdf":
            pdf_bytes = self.pdf_generator.generate_bytes(report_data)
            with open(file_path, "wb") as f:
                f.write(pdf_bytes)

        file_size = os.path.getsize(file_path)

        report_record = Report(
            id=report_id,
            organization_id=organization_id,
            name=base_name,
            format=fmt,
            start_date=start_date,
            end_date=end_date,
            account_id=account_id,
            file_path=str(file_path),
            file_size_bytes=file_size,
            status="COMPLETED",
            summary_data={
                "total_cost": float(report_data["total_cost"]),
                "difference": float(report_data["difference"]),
                "percentage_change": float(report_data["percentage_change"]),
                "potential_monthly_savings": float(report_data["potential_monthly_savings"]),
            },
            created_by=user_id,
        )
        db.add(report_record)
        db.commit()
        db.refresh(report_record)

        return report_record

    def cleanup_old_reports(self, db: Session, retention_days: Optional[int] = None) -> int:
        """Purges report files and records older than the retention threshold (default: 90 days)."""
        days = retention_days or settings.REPORT_RETENTION_DAYS
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        old_reports = db.query(Report).filter(Report.created_at < cutoff).all()
        purged_count = 0

        for r in old_reports:
            try:
                path = Path(r.file_path)
                if path.is_file():
                    path.unlink()
                db.delete(r)
                purged_count += 1
            except Exception as e:
                logger.error("Error purging old report %s: %s", r.id, e)

        db.commit()
        return purged_count

    def resolve_safe_file_path(
        self, db: Session, report_id: str, organization_id: Optional[str] = None
    ) -> Path:
        """Sanitizes and safely resolves canonical path to avoid directory traversal and cross-tenant leakage."""
        query = db.query(Report).filter(Report.id == report_id)
        if organization_id:
            query = query.filter(Report.organization_id == organization_id)
        report = query.first()

        if not report:
            raise FileNotFoundError(f"Report {report_id} not found in database or access is unauthorized.")

        canonical_path = Path(report.file_path).resolve()
        canonical_base = self.output_base.resolve()

        if not str(canonical_path).startswith(str(canonical_base)):
            raise PermissionError("Directory traversal detected. Access denied.")

        if not canonical_path.is_file():
            raise FileNotFoundError("The requested report file does not exist on disk.")

        return canonical_path

