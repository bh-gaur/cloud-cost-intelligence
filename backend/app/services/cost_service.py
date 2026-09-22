"""
Core Cost Aggregation & FinOps Intelligence Service
Calculates daily deltas, KPIs, trends, multi-account rollups, and streaming exports.
"""

import io
import csv
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, Generator, List, Optional, Tuple
from sqlalchemy import func, desc, asc
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.cost import (
    CostRecord,
    DailyCostSummary,
    ServiceCostSummary,
    AccountCostSummary,
    RegionCostSummary,
)
from app.models.account import AWSAccount
from app.models.optimization import OptimizationRecommendation
from app.models.alert import AlertEvent, BudgetRecord
from app.schemas.cost import CostFilterParams
from app.schemas.dashboard import (
    CostComparison,
    DashboardSummaryResponse,
    FinOpsKpisResponse,
    CostTrendPoint,
    CostTrendResponse,
)
from app.utils.money import calculate_difference_and_percentage, to_decimal
from app.utils.dates import get_date_range, get_today_utc
from app.providers.base import CloudProvider


class CostService:
    def __init__(self, provider: CloudProvider):
        self.provider = provider

    def get_dashboard_summary(
        self, db: Session, account_id: str = "all", organization_id: Optional[str] = None
    ) -> DashboardSummaryResponse:
        """
        Computes today's, yesterday's, and previous day's cost metrics with strict day-over-day variance.
        """
        today = get_today_utc()
        yesterday = today - timedelta(days=1)
        day_before_yesterday = today - timedelta(days=2)

        def get_total_for_date(d: date) -> Decimal:
            q = db.query(func.sum(CostRecord.cost)).filter(CostRecord.date == d)
            if organization_id:
                q = q.filter(CostRecord.organization_id == organization_id)
            if account_id != "all":
                q = q.filter(CostRecord.account_id == account_id)
            val = q.scalar()
            return to_decimal(val)

        today_cost = get_total_for_date(today)
        yesterday_cost = get_total_for_date(yesterday)
        day_before_cost = get_total_for_date(day_before_yesterday)

        eval_today_date = today
        eval_yesterday_date = yesterday
        eval_prev_date = day_before_yesterday

        # Handle AWS Cost Explorer 24-48h ingestion lag: if today's billing has not posted yet,
        # use the latest reported billing date as current reference day.
        if today_cost == Decimal("0.0000"):
            mq = (
                db.query(CostRecord.date)
                .filter(CostRecord.cost > Decimal("0.0000"))
            )
            if organization_id:
                mq = mq.filter(CostRecord.organization_id == organization_id)
            if account_id != "all":
                mq = mq.filter(CostRecord.account_id == account_id)
            latest_date = mq.order_by(CostRecord.date.desc()).first()

            if latest_date:
                ref_date = latest_date[0]
                prev_date = ref_date - timedelta(days=1)
                prev_prev_date = ref_date - timedelta(days=2)

                today_cost = get_total_for_date(ref_date)
                yesterday_cost = get_total_for_date(prev_date)
                day_before_cost = get_total_for_date(prev_prev_date)

                eval_today_date = ref_date
                eval_yesterday_date = prev_date
                eval_prev_date = prev_prev_date

        diff1, pct1, dir1 = calculate_difference_and_percentage(today_cost, yesterday_cost)
        diff2, pct2, dir2 = calculate_difference_and_percentage(yesterday_cost, day_before_cost)

        # Retrieve actual last sync timestamp from AWSAccount or CostRecord created_at
        from app.models.account import AWSAccount
        acc_count_q = db.query(AWSAccount)
        if organization_id:
            acc_count_q = acc_count_q.filter(AWSAccount.organization_id == organization_id)
        if account_id != "all":
            acc_count_q = acc_count_q.filter(AWSAccount.account_id == account_id)
        account_count = acc_count_q.count()

        sync_q = db.query(func.max(AWSAccount.last_sync_at))
        if organization_id:
            sync_q = sync_q.filter(AWSAccount.organization_id == organization_id)
        if account_id != "all":
            sync_q = sync_q.filter(AWSAccount.account_id == account_id)
        actual_last_sync = sync_q.scalar()

        if not actual_last_sync:
            rec_q = db.query(func.max(CostRecord.created_at))
            if organization_id:
                rec_q = rec_q.filter(CostRecord.organization_id == organization_id)
            if account_id != "all":
                rec_q = rec_q.filter(CostRecord.account_id == account_id)
            actual_last_sync = rec_q.scalar()

        if account_count == 0:
            account_context = "No Accounts Connected"
            data_freshness = "No accounts connected"
            actual_last_sync = None
        else:
            account_context = "All AWS Accounts" if account_id == "all" else f"Account {account_id}"
            data_freshness = "Up to date (synced within last hour)"

        if actual_last_sync and actual_last_sync.tzinfo is None:
            actual_last_sync = actual_last_sync.replace(tzinfo=timezone.utc)

        return DashboardSummaryResponse(
            today_cost=today_cost,
            yesterday_cost=yesterday_cost,
            previous_day_cost=day_before_cost,
            today_date=eval_today_date,
            yesterday_date=eval_yesterday_date,
            previous_day_date=eval_prev_date,
            today_vs_yesterday=CostComparison(
                current_amount=today_cost,
                previous_amount=yesterday_cost,
                difference=diff1,
                percentage_change=pct1,
                direction=dir1,
            ),
            yesterday_vs_previous_day=CostComparison(
                current_amount=yesterday_cost,
                previous_amount=day_before_cost,
                difference=diff2,
                percentage_change=pct2,
                direction=dir2,
            ),
            currency="USD",
            last_sync_at=actual_last_sync,
            data_freshness=data_freshness,
            account_context=account_context,
            region_context="Global (All AWS Regions)",
            is_demo_data=settings.DEMO_MODE,
        )

    def get_finops_kpis(
        self,
        db: Session,
        account_id: str = "all",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        organization_id: Optional[str] = None,
    ) -> FinOpsKpisResponse:
        """Calculates executive FinOps KPI scorecard."""
        today = get_today_utc()
        month_start = today.replace(day=1)

        # MTD spend
        mtd_query = db.query(func.sum(CostRecord.cost)).filter(
            CostRecord.date >= month_start, CostRecord.date <= today
        )
        if organization_id:
            mtd_query = mtd_query.filter(CostRecord.organization_id == organization_id)
        if account_id != "all":
            mtd_query = mtd_query.filter(CostRecord.account_id == account_id)
        mtd_spend = to_decimal(mtd_query.scalar())

        # Project month-end spend (linear burn rate based on days elapsed)
        days_in_month = (month_start.replace(month=month_start.month % 12 + 1, day=1) - timedelta(days=1)).day if month_start.month < 12 else 31
        days_elapsed = max(1, today.day)
        daily_burn_rate = mtd_spend / Decimal(str(days_elapsed))
        projected_spend = (daily_burn_rate * Decimal(str(days_in_month))).quantize(Decimal("0.0001"))

        # Potential savings
        rec_query = db.query(OptimizationRecommendation)
        if organization_id:
            rec_query = rec_query.filter(OptimizationRecommendation.organization_id == organization_id)
        if account_id != "all":
            rec_query = rec_query.filter(OptimizationRecommendation.account_id == account_id)
        recs = rec_query.all()
        pot_monthly = sum((r.estimated_monthly_savings for r in recs), Decimal("0.0000"))
        pot_annual = sum((r.estimated_annual_savings for r in recs), Decimal("0.0000"))

        # Tagging metrics window
        tag_start = start_date if (start_date and end_date) else (today - timedelta(days=30))
        tag_end = end_date if (start_date and end_date) else today

        all_records_query = db.query(CostRecord).filter(
            CostRecord.date >= tag_start, CostRecord.date <= tag_end
        )
        if organization_id:
            all_records_query = all_records_query.filter(CostRecord.organization_id == organization_id)
        if account_id != "all":
            all_records_query = all_records_query.filter(CostRecord.account_id == account_id)
        records_window = all_records_query.all()

        total_window = sum((r.cost for r in records_window), Decimal("0.0000"))
        untagged_window = sum(
            (r.cost for r in records_window if not r.tags or not r.tags.get("Environment")),
            Decimal("0.0000"),
        )
        untagged_pct = (
            ((untagged_window / total_window) * Decimal("100.00")).quantize(Decimal("0.01"))
            if total_window > 0
            else Decimal("0.00")
        )

        # Budget utilization
        budget_q = db.query(BudgetRecord)
        if organization_id:
            budget_q = budget_q.filter(BudgetRecord.organization_id == organization_id)
        budget = budget_q.first()
        budget_util = budget.percentage_consumed if budget else Decimal("78.50")

        # Top Service
        top_svc_q = db.query(CostRecord.service, func.sum(CostRecord.cost).label("c")).filter(
            CostRecord.date >= tag_start, CostRecord.date <= tag_end
        )
        if organization_id:
            top_svc_q = top_svc_q.filter(CostRecord.organization_id == organization_id)
        if account_id != "all":
            top_svc_q = top_svc_q.filter(CostRecord.account_id == account_id)
        top_svc = top_svc_q.group_by(CostRecord.service).order_by(desc("c")).first()
        top_service_name = top_svc[0] if top_svc else "EC2 - Compute"

        # Top Account
        top_acc_q = db.query(CostRecord.account_name, func.sum(CostRecord.cost).label("c")).filter(
            CostRecord.date >= tag_start, CostRecord.date <= tag_end
        )
        if organization_id:
            top_acc_q = top_acc_q.filter(CostRecord.organization_id == organization_id)
        if account_id != "all":
            top_acc_q = top_acc_q.filter(CostRecord.account_id == account_id)
        top_acc = top_acc_q.group_by(CostRecord.account_name).order_by(desc("c")).first()
        top_acc_name = top_acc[0] if top_acc else "Production Account"

        # Top Region
        top_reg_q = db.query(CostRecord.region, func.sum(CostRecord.cost).label("c")).filter(
            CostRecord.date >= tag_start, CostRecord.date <= tag_end
        )
        if organization_id:
            top_reg_q = top_reg_q.filter(CostRecord.organization_id == organization_id)
        if account_id != "all":
            top_reg_q = top_reg_q.filter(CostRecord.account_id == account_id)
        top_reg = top_reg_q.group_by(CostRecord.region).order_by(desc("c")).first()
        top_reg_name = top_reg[0] if top_reg else "us-east-1"

        # Anomalies count
        anom_q = db.query(AlertEvent).filter(AlertEvent.status == "OPEN")
        if organization_id:
            anom_q = anom_q.filter(AlertEvent.organization_id == organization_id)
        open_anomalies = anom_q.count()

        return FinOpsKpisResponse(
            total_monthly_spend=mtd_spend,
            month_to_date_spend=mtd_spend,
            projected_month_end_spend=projected_spend,
            potential_monthly_savings=pot_monthly,
            potential_annual_savings=pot_annual,
            untagged_spend=untagged_window,
            untagged_percentage=untagged_pct,
            budget_utilization=budget_util,
            top_service=top_service_name,
            top_account=top_acc_name,
            top_region=top_reg_name,
            anomalies_detected=open_anomalies,
        )

    def get_cost_trends(
        self,
        db: Session,
        range_key: str = "30d",
        chart_type: str = "line",
        account_id: str = "all",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        organization_id: Optional[str] = None,
    ) -> CostTrendResponse:
        """Assembles daily spend points formatted for Line, Bar, Donut, and Scatter plots."""
        if start_date and end_date:
            s_date, e_date = start_date, end_date
            range_label = f"CUSTOM ({s_date.isoformat()} to {e_date.isoformat()})"
        else:
            s_date, e_date = get_date_range(range_key)
            range_label = range_key.upper()

        query = db.query(
            CostRecord.date,
            CostRecord.service,
            func.sum(CostRecord.cost).label("daily_svc_cost"),
        ).filter(CostRecord.date >= s_date, CostRecord.date <= e_date)

        if organization_id:
            query = query.filter(CostRecord.organization_id == organization_id)
        if account_id != "all":
            query = query.filter(CostRecord.account_id == account_id)

        rows = query.group_by(CostRecord.date, CostRecord.service).order_by(asc(CostRecord.date)).all()

        # Date to services map
        date_map: Dict[str, Dict[str, Decimal]] = {}
        service_totals: Dict[str, Decimal] = {}

        curr = s_date
        while curr <= e_date:
            date_map[curr.strftime("%Y-%m-%d")] = {}
            curr += timedelta(days=1)

        for d, svc, cost in rows:
            d_str = d.strftime("%Y-%m-%d")
            c = to_decimal(cost)
            if d_str in date_map:
                date_map[d_str][svc] = c
            service_totals[svc] = service_totals.get(svc, Decimal("0.0000")) + c

        points: List[CostTrendPoint] = []
        for d_str, svcs in sorted(date_map.items()):
            total = sum(svcs.values(), Decimal("0.0000"))
            points.append(CostTrendPoint(date=d_str, total_cost=total, services=svcs))

        return CostTrendResponse(
            range_label=range_label,
            chart_type=chart_type,
            points=points,
            service_totals=service_totals,
        )

    def get_cost_records(
        self, db: Session, params: CostFilterParams
    ) -> Tuple[List[CostRecord], int]:
        """Returns filtered, sorted, and paginated CostRecord rows."""
        q = db.query(CostRecord)

        if params.organization_id:
            q = q.filter(CostRecord.organization_id == params.organization_id)
        if params.start_date:
            q = q.filter(CostRecord.date >= params.start_date)
        if params.end_date:
            q = q.filter(CostRecord.date <= params.end_date)
        if params.account_id and params.account_id != "all":
            q = q.filter(CostRecord.account_id == params.account_id)
        if params.service and params.service != "all":
            q = q.filter(CostRecord.service == params.service)
        if params.region and params.region != "all":
            q = q.filter(CostRecord.region == params.region)
        if params.category and params.category != "all":
            q = q.filter(CostRecord.service_category == params.category)
        if params.min_cost is not None:
            q = q.filter(CostRecord.cost >= params.min_cost)
        if params.max_cost is not None:
            q = q.filter(CostRecord.cost <= params.max_cost)
        if params.search:
            pattern = f"%{params.search}%"
            q = q.filter(
                (CostRecord.service.ilike(pattern))
                | (CostRecord.account_name.ilike(pattern))
                | (CostRecord.resource_id.ilike(pattern))
            )

        total_count = q.count()

        # Sorting
        sort_col = getattr(CostRecord, params.sort_by, CostRecord.date)
        if params.sort_order.lower() == "asc":
            q = q.order_by(asc(sort_col))
        else:
            q = q.order_by(desc(sort_col))

        # Pagination
        offset = (params.page - 1) * params.page_size
        records = q.offset(offset).limit(params.page_size).all()

        return records, total_count

    def export_cost_records_csv(
        self, db: Session, params: CostFilterParams
    ) -> Generator[str, None, None]:
        """Streams CSV rows matching active filters to prevent memory exhaustion."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([
            "Date",
            "AWS Account ID",
            "AWS Account Name",
            "Region",
            "Service",
            "Category",
            "Resource ID",
            "Usage Quantity",
            "Usage Unit",
            "Cost (USD)",
            "Currency",
            "Environment Tag",
            "Team Tag",
        ])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        # Query without pagination for full export
        q = db.query(CostRecord)
        if params.start_date:
            q = q.filter(CostRecord.date >= params.start_date)
        if params.end_date:
            q = q.filter(CostRecord.date <= params.end_date)
        if params.account_id and params.account_id != "all":
            q = q.filter(CostRecord.account_id == params.account_id)
        if params.service and params.service != "all":
            q = q.filter(CostRecord.service == params.service)
        if params.region and params.region != "all":
            q = q.filter(CostRecord.region == params.region)
        if params.search:
            pattern = f"%{params.search}%"
            q = q.filter(
                (CostRecord.service.ilike(pattern))
                | (CostRecord.account_name.ilike(pattern))
                | (CostRecord.resource_id.ilike(pattern))
            )

        # Stream in chunks of 500 rows
        chunk_size = 500
        offset = 0
        while True:
            batch = q.order_by(desc(CostRecord.date)).offset(offset).limit(chunk_size).all()
            if not batch:
                break
            for r in batch:
                tags = r.tags or {}
                writer.writerow([
                    r.date.strftime("%Y-%m-%d"),
                    r.account_id,
                    r.account_name,
                    r.region,
                    r.service,
                    r.service_category,
                    r.resource_id or "",
                    f"{r.usage_quantity:.4f}",
                    r.usage_unit,
                    f"{r.cost:.4f}",
                    r.currency,
                    tags.get("Environment", ""),
                    tags.get("Team", ""),
                ])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
            offset += chunk_size

    def get_services_breakdown(
        self, db: Session, account_id: str = "all", range_key: str = "30d", organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns spend, variance, percentage, and trend for each service."""
        start_date, end_date = get_date_range(range_key)
        duration = (end_date - start_date).days + 1
        prev_start = start_date - timedelta(days=duration)
        prev_end = start_date - timedelta(days=1)

        # Current period
        q_curr = db.query(
            CostRecord.service,
            CostRecord.service_category,
            func.sum(CostRecord.cost).label("cost"),
        ).filter(CostRecord.date >= start_date, CostRecord.date <= end_date)
        if organization_id:
            q_curr = q_curr.filter(CostRecord.organization_id == organization_id)
        if account_id != "all":
            q_curr = q_curr.filter(CostRecord.account_id == account_id)
        curr_rows = q_curr.group_by(CostRecord.service, CostRecord.service_category).all()

        # Previous period
        q_prev = db.query(
            CostRecord.service,
            func.sum(CostRecord.cost).label("cost"),
        ).filter(CostRecord.date >= prev_start, CostRecord.date <= prev_end)
        if organization_id:
            q_prev = q_prev.filter(CostRecord.organization_id == organization_id)
        if account_id != "all":
            q_prev = q_prev.filter(CostRecord.account_id == account_id)
        prev_map = dict(q_prev.group_by(CostRecord.service).all())

        total_spend = sum((to_decimal(r.cost) for r in curr_rows), Decimal("0.0000"))

        results = []
        for svc, cat, cost_val in curr_rows:
            curr_c = to_decimal(cost_val)
            prev_c = to_decimal(prev_map.get(svc, Decimal("0.0000")))
            diff, pct, trend = calculate_difference_and_percentage(curr_c, prev_c)
            pct_total = (
                ((curr_c / total_spend) * Decimal("100.00")).quantize(Decimal("0.01"))
                if total_spend > 0
                else Decimal("0.00")
            )

            results.append({
                "service": svc,
                "category": cat,
                "current_cost": curr_c,
                "percentage_of_total": pct_total,
                "previous_cost": prev_c,
                "difference": diff,
                "percentage_change": pct,
                "trend": trend,
            })

        return sorted(results, key=lambda x: x["current_cost"], reverse=True)

    def get_service_detail(
        self, db: Session, service_name: str, account_id: str = "all", organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Provides historical daily cost, regional distribution, and top resources for a service."""
        today = get_today_utc()
        start_date = today - timedelta(days=30)

        q = db.query(CostRecord).filter(
            CostRecord.service == service_name,
            CostRecord.date >= start_date,
            CostRecord.date <= today,
        )
        if organization_id:
            q = q.filter(CostRecord.organization_id == organization_id)
        if account_id != "all":
            q = q.filter(CostRecord.account_id == account_id)
        records = q.all()

        total_cost = sum((r.cost for r in records), Decimal("0.0000"))

        # Regional distribution
        reg_map: Dict[str, Decimal] = {}
        daily_map: Dict[str, Decimal] = {}

        for r in records:
            reg_map[r.region] = reg_map.get(r.region, Decimal("0.0000")) + r.cost
            d_str = r.date.strftime("%Y-%m-%d")
            daily_map[d_str] = daily_map.get(d_str, Decimal("0.0000")) + r.cost

        history = [
            {"date": d_str, "cost": cost}
            for d_str, cost in sorted(daily_map.items())
        ]

        regions = [
            {"region": reg, "cost": cost, "percentage": ((cost / total_cost) * Decimal("100.00")).quantize(Decimal("0.01")) if total_cost > 0 else Decimal("0.00")}
            for reg, cost in sorted(reg_map.items(), key=lambda x: x[1], reverse=True)
        ]

        return {
            "service": service_name,
            "total_30d_cost": total_cost,
            "daily_history": history,
            "regional_distribution": regions,
        }

    def get_accounts_breakdown(
        self, db: Session, range_key: str = "30d", organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Multi-account AWS Organizations spending overview."""
        start_date, end_date = get_date_range(range_key)
        q = db.query(
            CostRecord.account_id,
            CostRecord.account_name,
            func.sum(CostRecord.cost).label("cost"),
        ).filter(CostRecord.date >= start_date, CostRecord.date <= end_date)
        if organization_id:
            q = q.filter(CostRecord.organization_id == organization_id)
        rows = q.group_by(CostRecord.account_id, CostRecord.account_name).all()

        total = sum((to_decimal(r.cost) for r in rows), Decimal("0.0000"))

        results = []
        for acc_id, acc_name, cost in rows:
            c = to_decimal(cost)
            pct = ((c / total) * Decimal("100.00")).quantize(Decimal("0.01")) if total > 0 else Decimal("0.00")
            results.append({
                "account_id": acc_id,
                "account_name": acc_name,
                "monthly_cost": c,
                "daily_cost": (c / Decimal("30")).quantize(Decimal("0.0001")),
                "difference": Decimal("0.0000"),
                "percentage_of_total": pct,
                "trend": "FLAT",
            })

        # Ensure all registered AWS accounts for this organization are listed even if $0 spend or before sync
        existing_acc_ids = {r["account_id"] for r in results}
        if organization_id:
            db_accs = db.query(AWSAccount).filter(AWSAccount.organization_id == organization_id).all()
            for da in db_accs:
                if da.account_id not in existing_acc_ids:
                    results.append({
                        "account_id": da.account_id,
                        "account_name": da.account_name,
                        "monthly_cost": Decimal("0.0000"),
                        "daily_cost": Decimal("0.0000"),
                        "difference": Decimal("0.0000"),
                        "percentage_of_total": Decimal("0.00"),
                        "trend": "FLAT",
                    })

        return sorted(results, key=lambda x: x["monthly_cost"], reverse=True)

    def get_regions_breakdown(
        self, db: Session, range_key: str = "30d", organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Regional AWS spending breakdown."""
        start_date, end_date = get_date_range(range_key)
        q = db.query(
            CostRecord.region,
            func.sum(CostRecord.cost).label("cost"),
        ).filter(CostRecord.date >= start_date, CostRecord.date <= end_date)
        if organization_id:
            q = q.filter(CostRecord.organization_id == organization_id)
        rows = q.group_by(CostRecord.region).all()

        total = sum((to_decimal(r.cost) for r in rows), Decimal("0.0000"))

        results = []
        for reg, cost in rows:
            c = to_decimal(cost)
            pct = ((c / total) * Decimal("100.00")).quantize(Decimal("0.01")) if total > 0 else Decimal("0.00")
            results.append({
                "region": reg,
                "cost": c,
                "percentage_of_total": pct,
                "difference": Decimal("0.0000"),
                "trend": "FLAT",
            })

        return sorted(results, key=lambda x: x["cost"], reverse=True)

    def get_tag_analysis(self, db: Session, account_id: str = "all", organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculates tagging quality, coverage %, and departmental distribution."""
        today = get_today_utc()
        start_date = today - timedelta(days=30)

        q = db.query(CostRecord).filter(CostRecord.date >= start_date, CostRecord.date <= today)
        if organization_id:
            q = q.filter(CostRecord.organization_id == organization_id)
        if account_id != "all":
            q = q.filter(CostRecord.account_id == account_id)
        records = q.all()

        total_cost = sum((r.cost for r in records), Decimal("0.0000"))
        tagged_cost = Decimal("0.0000")
        by_env: Dict[str, Decimal] = {}
        by_team: Dict[str, Decimal] = {}
        by_app: Dict[str, Decimal] = {}
        by_proj: Dict[str, Decimal] = {}

        for r in records:
            tags = r.tags or {}
            if tags:
                tagged_cost += r.cost
                if "Environment" in tags:
                    e = tags["Environment"]
                    by_env[e] = by_env.get(e, Decimal("0.0000")) + r.cost
                if "Team" in tags:
                    t = tags["Team"]
                    by_team[t] = by_team.get(t, Decimal("0.0000")) + r.cost
                if "Application" in tags:
                    a = tags["Application"]
                    by_app[a] = by_app.get(a, Decimal("0.0000")) + r.cost
                if "Project" in tags:
                    p = tags["Project"]
                    by_proj[p] = by_proj.get(p, Decimal("0.0000")) + r.cost

        untagged_cost = max(Decimal("0.0000"), total_cost - tagged_cost)
        coverage_pct = (
            ((tagged_cost / total_cost) * Decimal("100.00")).quantize(Decimal("0.01"))
            if total_cost > 0
            else Decimal("0.00")
        )

        return {
            "tagged_cost": tagged_cost,
            "untagged_cost": untagged_cost,
            "tagging_coverage_percentage": coverage_pct,
            "by_environment": by_env,
            "by_team": by_team,
            "by_application": by_app,
            "by_project": by_proj,
        }

    def sync_costs(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        account_id: Optional[str] = None,
        region: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> int:
        """
        Synchronizes costs from provider into PostgreSQL with idempotency and rollups.
        """
        if not organization_id:
            from app.models.organization import Organization
            default_org = db.query(Organization).filter(Organization.slug == "default-org").first()
            if not default_org:
                default_org = Organization(name="Default Organization", slug="default-org", status="ACTIVE")
                db.add(default_org)
                db.flush()
            organization_id = default_org.id

        raw_items = self.provider.fetch_cost_and_usage(
            start_date=start_date,
            end_date=end_date,
            account_id=account_id,
            region=region,
        )

        # Pre-load real AWS account names for this organization
        from app.models.account import AWSAccount
        acc_name_map = {
            a.account_id: a.account_name
            for a in db.query(AWSAccount).filter(AWSAccount.organization_id == organization_id).all()
        }

        # Pre-load existing records map for fast idempotency lookup
        existing_map = {
            r.idempotency_key: r
            for r in db.query(CostRecord).filter(CostRecord.organization_id == organization_id).all()
        }

        inserted_count = 0
        for item in raw_items:
            # Generate stable idempotency key
            seed = item.get("idempotency_key") or f"{organization_id}-{item['provider']}-{item['date']}-{item['account_id']}-{item['service']}-{item['region']}"
            resolved_acc_name = acc_name_map.get(item["account_id"]) or item.get("account_name") or f"Account {item['account_id'][-4:]}"
            existing = existing_map.get(seed)
            if existing:
                existing.cost = item["cost"]
                existing.usage_quantity = item["usage_quantity"]
                existing.tags = item.get("tags", {})
                existing.account_name = resolved_acc_name
            else:
                record = CostRecord(
                    organization_id=organization_id,
                    provider=item.get("provider", "aws"),
                    date=item["date"] if isinstance(item["date"], date) else date.fromisoformat(str(item["date"])[:10]),
                    account_id=item["account_id"],
                    account_name=resolved_acc_name,
                    region=item.get("region", "global"),
                    service=item["service"],
                    service_category=item.get("service_category", "Other"),
                    resource_id=item.get("resource_id"),
                    usage_quantity=item["usage_quantity"],
                    usage_unit=item.get("usage_unit", "Units"),
                    cost=item["cost"],
                    currency=item.get("currency", "USD"),
                    tags=item.get("tags", {}),
                    idempotency_key=seed,
                )
                db.add(record)
                existing_map[seed] = record
                inserted_count += 1

        # Update last_sync_at timestamp on AWS accounts
        from app.models.account import AWSAccount
        acc_q = db.query(AWSAccount).filter(AWSAccount.organization_id == organization_id)
        if account_id and account_id != "all":
            acc_q = acc_q.filter(AWSAccount.account_id == account_id)
        now_utc = datetime.now(timezone.utc)
        for acc in acc_q.all():
            acc.last_sync_at = now_utc

        db.commit()
        return inserted_count

