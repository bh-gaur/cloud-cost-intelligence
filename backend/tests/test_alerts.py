"""
Tests for Anomaly Detection Engine & Alerts
"""

import uuid
import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.models.cost import CostRecord
from app.models.organization import Organization
from app.models.alert import AlertRule, AlertEvent, BudgetRecord
from app.alerts.detector import AnomalyDetector
from app.utils.money import to_decimal


def test_anomaly_detection_rolling_baseline(db_session):
    """Verifies that a service with sudden spike over rolling 7-day baseline is flagged as an anomaly."""
    org = db_session.query(Organization).first()
    assert org is not None
    org_id = org.id
    detector = AnomalyDetector()

    # Seed 7 days of normal spend ($10.00/day for EC2)
    today = date(2026, 9, 10)
    for i in range(7, 0, -1):
        d = today - timedelta(days=i)
        rec = CostRecord(
            organization_id=org_id,
            date=d,
            service="Amazon Elastic Compute Cloud - Compute",
            account_id="111122223333",
            cost=Decimal("10.0000"),
            currency="USD",
            idempotency_key=f"test-base-{org_id}-{d}-{uuid.uuid4()}",
        )
        db_session.add(rec)

    # Seed sudden spike on target date ($85.00)
    spike_rec = CostRecord(
        organization_id=org_id,
        date=today,
        service="Amazon Elastic Compute Cloud - Compute",
        account_id="111122223333",
        cost=Decimal("85.0000"),
        currency="USD",
        idempotency_key=f"test-spike-{org_id}-{today}-{uuid.uuid4()}",
    )
    db_session.add(spike_rec)
    db_session.commit()

    events = detector.detect_daily_anomalies(db_session, target_date=today, organization_id=org_id)
    assert len(events) >= 1

    ec2_event = next((e for e in events if e.service == "Amazon Elastic Compute Cloud - Compute"), None)
    assert ec2_event is not None
    assert ec2_event.detected_value == Decimal("85.0000")
    assert ec2_event.severity in ("WARNING", "CRITICAL")
    assert ec2_event.difference_percentage > Decimal("100.00")


def test_anomaly_detection_new_service_surge(db_session):
    """Verifies that an unexpected new service appearing with significant cost is detected."""
    org = db_session.query(Organization).first()
    assert org is not None
    org_id = org.id
    detector = AnomalyDetector()

    today = date(2026, 9, 10)
    # Seed new service spend ($15.00) with no prior baseline
    rec = CostRecord(
        organization_id=org_id,
        date=today,
        service="Amazon Bedrock",
        account_id="111122223333",
        cost=Decimal("15.0000"),
        currency="USD",
        idempotency_key=f"test-bedrock-{org_id}-{today}-{uuid.uuid4()}",
    )
    db_session.add(rec)
    db_session.commit()

    events = detector.detect_daily_anomalies(db_session, target_date=today, organization_id=org_id)
    bedrock_event = next((e for e in events if e.service == "Amazon Bedrock"), None)
    assert bedrock_event is not None
    assert bedrock_event.detected_value == Decimal("15.0000")
    assert "New Service" in bedrock_event.title


def test_anomaly_detection_alert_rule_breach(db_session):
    """Verifies that configured AlertRules evaluate properly against daily spending."""
    org = db_session.query(Organization).first()
    assert org is not None
    org_id = org.id
    detector = AnomalyDetector()

    # Create daily threshold alert rule for RDS $50.00
    rule = AlertRule(
        organization_id=org_id,
        name="RDS Daily Limit $50",
        alert_type="DAILY_THRESHOLD",
        account_id="111122223333",
        service="Amazon Relational Database Service",
        threshold_value=Decimal("50.0000"),
        is_enabled=True,
    )
    db_session.add(rule)

    today = date(2026, 9, 12)
    rec = CostRecord(
        organization_id=org_id,
        date=today,
        service="Amazon Relational Database Service",
        account_id="111122223333",
        cost=Decimal("65.0000"),
        currency="USD",
        idempotency_key=f"test-rds-{org_id}-{today}-{uuid.uuid4()}",
    )
    db_session.add(rec)
    db_session.commit()

    events = detector.detect_daily_anomalies(db_session, target_date=today, organization_id=org_id)
    rule_event = next((e for e in events if e.alert_rule_id == rule.id), None)
    assert rule_event is not None
    assert rule_event.detected_value == Decimal("65.0000")
    assert "Alert Rule Breached" in rule_event.title


def test_alerts_scan_api(client, user_headers):
    """Verifies the /api/v1/alerts/scan endpoint returns valid anomaly counts."""
    response = client.post("/api/v1/alerts/scan", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "anomalies_count" in data["data"]
    assert "new_anomalies_count" in data["data"]
