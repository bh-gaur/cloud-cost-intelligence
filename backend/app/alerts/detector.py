"""
Anomaly Detection & Alert Processing Engine
Evaluates cost records against rolling statistical baselines, relative day-over-day spikes,
and configured threshold alert rules.
"""

import json
import logging
import statistics
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.alert import AlertRule, AlertEvent, BudgetRecord
from app.models.cost import CostRecord
from app.models.notification import NotificationIntegration
from app.utils.money import calculate_difference_and_percentage, to_decimal
from app.providers.base import CloudProvider

logger = logging.getLogger(__name__)


class AnomalyDetector:
    def __init__(self, provider: Optional[CloudProvider] = None):
        self.provider = provider

    def detect_daily_anomalies(
        self,
        db: Session,
        target_date: Optional[date] = None,
        organization_id: Optional[str] = None,
    ) -> List[AlertEvent]:
        """
        Scans cost history for statistical anomalies and alert rule breaches:
        1. Multi-day rolling statistical baseline (z-score >= 2.0 and delta >= $0.05).
        2. Day-over-day relative surge (>= 40% and delta >= $0.05).
        3. Unexpected new service spend surges.
        4. Account-level total daily spend anomalies.
        5. User-configured AlertRule thresholds.
        6. Native cloud provider anomalies (if enabled).
        """
        if not organization_id:
            from app.models.organization import Organization
            default_org = db.query(Organization).filter(Organization.slug == "default-org").first()
            if default_org:
                organization_id = default_org.id

        # Determine dates to evaluate
        dates_to_eval: List[date] = []
        if target_date:
            dates_to_eval = [target_date]
        else:
            # Evaluate all recent distinct dates with cost records (up to last 30 days)
            q_dates = (
                db.query(CostRecord.date)
                .filter(CostRecord.organization_id == organization_id)
                .distinct()
                .order_by(CostRecord.date.asc())
            )
            all_dates = [r[0] for r in q_dates.all()]
            dates_to_eval = all_dates[-30:] if len(all_dates) > 30 else all_dates

        if not dates_to_eval:
            logger.info("No cost records found to evaluate for organization %s", organization_id)
            return []

        # Load active alert rules for this organization
        active_rules = (
            db.query(AlertRule)
            .filter(
                AlertRule.organization_id == organization_id,
                AlertRule.is_enabled == True,
            )
            .all()
        )

        new_events: List[AlertEvent] = []

        for eval_date in dates_to_eval:
            baseline_start = eval_date - timedelta(days=7)
            
            # Fetch baseline records (previous 7 days before eval_date)
            baseline_q = db.query(
                CostRecord.service,
                CostRecord.cost,
                CostRecord.account_id,
            ).filter(
                CostRecord.organization_id == organization_id,
                CostRecord.date >= baseline_start,
                CostRecord.date < eval_date,
            ).all()

            # Fetch today's records
            today_q = db.query(
                CostRecord.service,
                func.sum(CostRecord.cost).label("cost"),
                CostRecord.account_id,
            ).filter(
                CostRecord.organization_id == organization_id,
                CostRecord.date == eval_date,
            ).group_by(CostRecord.service, CostRecord.account_id).all()

            # Build history lookup per service
            svc_history: Dict[str, List[float]] = {}
            for svc, cost, acc in baseline_q:
                svc_history.setdefault(svc, []).append(float(cost or 0.0))

            # Yesterday's cost per service
            yesterday_date = eval_date - timedelta(days=1)
            yesterday_q = db.query(
                CostRecord.service,
                func.sum(CostRecord.cost).label("cost"),
            ).filter(
                CostRecord.organization_id == organization_id,
                CostRecord.date == yesterday_date,
            ).group_by(CostRecord.service).all()
            yesterday_map = {r[0]: float(r[1] or 0.0) for r in yesterday_q}

            for svc_name, svc_cost_raw, acc_id in today_q:
                curr_cost = float(svc_cost_raw or 0.0)
                if curr_cost <= 0.01:
                    continue

                hist = svc_history.get(svc_name, [])
                event_data: Optional[Dict[str, Any]] = None

                # 1. New Service Surge
                if not hist and curr_cost >= 0.05:
                    sev = "CRITICAL" if curr_cost >= 10.0 else ("WARNING" if curr_cost >= 0.50 else "INFO")
                    event_data = {
                        "title": f"New Service Spend: {svc_name}",
                        "severity": sev,
                        "account_id": acc_id or "all",
                        "service": svc_name,
                        "detected_value": to_decimal(curr_cost),
                        "expected_value": Decimal("0.0000"),
                        "difference_percentage": Decimal("100.00"),
                        "message": f"New spend detected for {svc_name} (${curr_cost:.4f}) with no prior activity in 7-day baseline.",
                    }

                # 2. Statistical Baseline Z-Score Spike
                elif hist:
                    mean_val = statistics.mean(hist)
                    stdev_val = statistics.stdev(hist) if len(hist) > 1 else 0.0
                    delta = curr_cost - mean_val

                    if stdev_val > 0:
                        z_score = delta / stdev_val
                        if z_score >= 2.0 and delta >= 0.05:
                            pct = ((curr_cost - mean_val) / mean_val * 100.0) if mean_val > 0 else 100.0
                            sev = "CRITICAL" if z_score >= 3.5 or delta >= 5.0 else "WARNING"
                            event_data = {
                                "title": f"Cost Spike Detected: {svc_name}",
                                "severity": sev,
                                "account_id": acc_id or "all",
                                "service": svc_name,
                                "detected_value": to_decimal(curr_cost),
                                "expected_value": to_decimal(mean_val),
                                "difference_percentage": to_decimal(round(pct, 2)),
                                "message": f"{svc_name} spend spiked to ${curr_cost:,.2f} on {eval_date} (7-day baseline: ${mean_val:,.2f}, z-score: {z_score:.1f}, +{pct:.1f}%).",
                            }

                    # 3. Day-over-Day Relative Surge Fallback
                    if not event_data and svc_name in yesterday_map:
                        y_val = yesterday_map[svc_name]
                        if y_val > 0:
                            dod_diff = curr_cost - y_val
                            dod_pct = (dod_diff / y_val) * 100.0
                            if dod_pct >= 40.0 and dod_diff >= 0.05:
                                sev = "CRITICAL" if dod_pct >= 100.0 or dod_diff >= 5.0 else "WARNING"
                                event_data = {
                                    "title": f"Day-over-Day Surge: {svc_name}",
                                    "severity": sev,
                                    "account_id": acc_id or "all",
                                    "service": svc_name,
                                    "detected_value": to_decimal(curr_cost),
                                    "expected_value": to_decimal(y_val),
                                    "difference_percentage": to_decimal(round(dod_pct, 2)),
                                    "message": f"{svc_name} spend increased by ${dod_diff:,.2f} (+{dod_pct:.1f}%) compared to yesterday on {eval_date}.",
                                }

                if event_data:
                    # Deduplicate: check if event already recorded for this service, date, and org
                    event_dt = datetime.combine(eval_date, datetime.min.time(), tzinfo=timezone.utc)
                    existing = (
                        db.query(AlertEvent)
                        .filter(
                            AlertEvent.organization_id == organization_id,
                            AlertEvent.service == svc_name,
                            AlertEvent.title == event_data["title"],
                            func.date(AlertEvent.created_at) == eval_date,
                        )
                        .first()
                    )
                    if not existing:
                        ev = AlertEvent(
                            organization_id=organization_id,
                            title=event_data["title"],
                            severity=event_data["severity"],
                            account_id=event_data["account_id"],
                            service=event_data["service"],
                            detected_value=event_data["detected_value"],
                            expected_value=event_data["expected_value"],
                            difference_percentage=event_data["difference_percentage"],
                            message=event_data["message"],
                            status="OPEN",
                            created_at=event_dt,
                        )
                        db.add(ev)
                        new_events.append(ev)

            # 4. User-Configured AlertRule Evaluation
            for rule in active_rules:
                match_service = rule.service in ("all", None, "")
                match_account = rule.account_id in ("all", None, "")

                if rule.alert_type == "DAILY_THRESHOLD":
                    # Total daily spend check
                    total_spend_q = db.query(func.sum(CostRecord.cost)).filter(
                        CostRecord.organization_id == organization_id,
                        CostRecord.date == eval_date,
                    )
                    if not match_service:
                        total_spend_q = total_spend_q.filter(CostRecord.service == rule.service)
                    if not match_account:
                        total_spend_q = total_spend_q.filter(CostRecord.account_id == rule.account_id)

                    spend_val = to_decimal(total_spend_q.scalar() or 0.0)
                    if spend_val >= rule.threshold_value:
                        rule_title = f"Alert Rule Breached: {rule.name}"
                        existing_rule_ev = (
                            db.query(AlertEvent)
                            .filter(
                                AlertEvent.organization_id == organization_id,
                                AlertEvent.alert_rule_id == rule.id,
                                func.date(AlertEvent.created_at) == eval_date,
                            )
                            .first()
                        )
                        if not existing_rule_ev:
                            ev = AlertEvent(
                                organization_id=organization_id,
                                alert_rule_id=rule.id,
                                title=rule_title,
                                severity="CRITICAL" if spend_val >= rule.threshold_value * Decimal("1.5") else "WARNING",
                                account_id=rule.account_id,
                                service=rule.service,
                                detected_value=spend_val,
                                expected_value=rule.threshold_value,
                                difference_percentage=Decimal("0.00"),
                                message=f"Daily spend of ${spend_val:,.2f} on {eval_date} exceeded configured threshold of ${rule.threshold_value:,.2f}.",
                                status="OPEN",
                                created_at=datetime.combine(eval_date, datetime.min.time(), tzinfo=timezone.utc),
                            )
                            db.add(ev)
                            new_events.append(ev)

        # 5. Cloud-Native Provider Anomalies (if available)
        if self.provider and hasattr(self.provider, "get_anomalies"):
            try:
                min_eval_date = min(dates_to_eval)
                max_eval_date = max(dates_to_eval)
                native_anomalies = self.provider.get_anomalies(min_eval_date, max_eval_date)
                for na in native_anomalies:
                    anom_q = db.query(AlertEvent).filter(
                        AlertEvent.service == na["service"],
                        AlertEvent.account_id == na["account_id"],
                        AlertEvent.detected_value == na["impact_cost"],
                        AlertEvent.organization_id == organization_id,
                    )
                    existing = anom_q.first()
                    if not existing:
                        event = AlertEvent(
                            organization_id=organization_id,
                            title=f"AWS Anomaly: {na['service']}",
                            severity=na.get("severity", "WARNING"),
                            account_id=na.get("account_id", "all"),
                            service=na.get("service"),
                            detected_value=na.get("impact_cost", Decimal("0.0000")),
                            expected_value=Decimal("0.0000"),
                            difference_percentage=Decimal("0.00"),
                            message=na.get("root_cause", f"Cloud anomaly detected in {na.get('service')}"),
                            status="OPEN",
                        )
                        db.add(event)
                        new_events.append(event)
            except Exception as e:
                logger.warning("Cloud-native anomaly check skipped: %s", e)

        db.commit()

        # 6. Dispatch Notifications to Active Channels
        if new_events:
            self._dispatch_anomaly_notifications(db, organization_id, new_events)

        return new_events

    def _dispatch_anomaly_notifications(
        self, db: Session, organization_id: str, events: List[AlertEvent]
    ) -> None:
        """Sends webhook and email alerts to all active NotificationIntegration channels for the organization."""
        try:
            from app.models.organization import Organization
            from app.notifications.slack import SlackNotificationProvider

            org = db.query(Organization).filter(Organization.id == organization_id).first()
            org_name = org.name if org else "Your Organization"

            integrations = (
                db.query(NotificationIntegration)
                .filter(
                    NotificationIntegration.organization_id == organization_id,
                    NotificationIntegration.is_active == True,
                )
                .all()
            )
            if not integrations:
                return

            critical_count = sum(1 for e in events if e.severity == "CRITICAL")
            summary_text = (
                f"🚨 *Cloud Cost Intelligence Alert*\n"
                f"Detected *{len(events)}* cost anomalies ({critical_count} Critical) for *{org_name}*.\n\n"
            )
            for e in events[:5]:
                summary_text += f"• *[{e.severity}] {e.title}*: ${float(e.detected_value or 0.0):,.2f} ({e.message})\n"

            if len(events) > 5:
                summary_text += f"\n_...and {len(events) - 5} more incidents in the dashboard._"

            anomaly_items = [
                {
                    "title": e.title,
                    "severity": e.severity,
                    "service": e.service,
                    "account_id": e.account_id,
                    "detected_value": float(e.detected_value or 0.0),
                    "expected_value": float(e.expected_value or 0.0),
                    "difference_percentage": float(e.difference_percentage or 0.0),
                    "message": e.message,
                }
                for e in events
            ]

            payload_dict = {
                "text": summary_text,
                "event": "ANOMALY_DETECTED",
                "org_name": org_name,
                "organization_id": organization_id,
                "anomalies": anomaly_items,
                "anomalies_count": len(events),
                "critical_count": critical_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            for integ in integrations:
                webhook_url = (integ.config or {}).get("webhook_url")
                if not webhook_url or not str(webhook_url).startswith("http"):
                    continue

                if integ.channel_type == "slack":
                    provider = SlackNotificationProvider(webhook_url=webhook_url)
                    ok = provider.send(payload_dict)
                    if ok:
                        integ.test_status = "SUCCESS"
                        integ.last_tested_at = datetime.now(timezone.utc)
                elif integ.channel_type == "webhook":
                    try:
                        raw_body = json.dumps(payload_dict).encode("utf-8")
                        req = urllib.request.Request(
                            webhook_url,
                            data=raw_body,
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        )
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            if resp.status in (200, 201, 204):
                                integ.test_status = "SUCCESS"
                                integ.last_tested_at = datetime.now(timezone.utc)
                    except Exception as ex:
                        logger.error("Failed to dispatch webhook alert to %s: %s", integ.name, ex)
                        integ.last_error = str(ex)

            db.commit()
        except Exception as e:
            logger.error("Error dispatching anomaly notifications: %s", e)

    def sync_budgets(
        self, db: Session, organization_id: Optional[str] = None
    ) -> List[BudgetRecord]:
        """Synchronizes budget limits and utilization statuses from the provider."""
        if not organization_id:
            from app.models.organization import Organization
            default_org = db.query(Organization).filter(Organization.slug == "default-org").first()
            if default_org:
                organization_id = default_org.id

        if not self.provider or not hasattr(self.provider, "get_budgets"):
            return []

        provider_budgets = self.provider.get_budgets()
        synced: List[BudgetRecord] = []

        for b in provider_budgets:
            b_q = db.query(BudgetRecord).filter(
                BudgetRecord.budget_name == b["budget_name"],
                BudgetRecord.account_id == b["account_id"],
            )
            if organization_id:
                b_q = b_q.filter(BudgetRecord.organization_id == organization_id)
            existing = b_q.first()

            if existing:
                existing.budget_limit = b["budget_limit"]
                existing.current_spend = b["current_spend"]
                existing.forecasted_spend = b["forecasted_spend"]
                existing.remaining_budget = b["remaining_budget"]
                existing.percentage_consumed = b["percentage_consumed"]
                existing.status = b["status"]
                existing.period_start = b["period_start"]
                existing.period_end = b["period_end"]
                synced.append(existing)
            else:
                new_budget = BudgetRecord(
                    organization_id=organization_id,
                    budget_name=b["budget_name"],
                    account_id=b["account_id"],
                    budget_limit=b["budget_limit"],
                    current_spend=b["current_spend"],
                    forecasted_spend=b["forecasted_spend"],
                    remaining_budget=b["remaining_budget"],
                    percentage_consumed=b["percentage_consumed"],
                    status=b["status"],
                    currency=b.get("currency", "USD"),
                    period_start=b["period_start"],
                    period_end=b["period_end"],
                )
                db.add(new_budget)
                synced.append(new_budget)

        db.commit()
        return synced
