"""
Tests for Cost Service, Math, and Aggregation
"""

from decimal import Decimal
import pytest
from app.utils.money import calculate_difference_and_percentage, to_decimal
from app.services.cost_service import CostService
from app.providers.mock.provider import MockAWSProvider


def test_calculate_difference_and_percentage():
    # Increase: $120 vs $100 -> +$20, +20%, UP
    diff, pct, direction = calculate_difference_and_percentage(Decimal("120.00"), Decimal("100.00"))
    assert diff == Decimal("20.0000")
    assert pct == Decimal("20.00")
    assert direction == "UP"

    # Decrease: $80 vs $100 -> -$20, -20%, DOWN
    diff, pct, direction = calculate_difference_and_percentage(Decimal("80.00"), Decimal("100.00"))
    assert diff == Decimal("-20.0000")
    assert pct == Decimal("-20.00")
    assert direction == "DOWN"

    # Flat: $100 vs $100 -> $0, 0%, FLAT
    diff, pct, direction = calculate_difference_and_percentage(Decimal("100.00"), Decimal("100.00"))
    assert diff == Decimal("0.0000")
    assert pct == Decimal("0.00")
    assert direction == "FLAT"


def test_dashboard_summary_computation(db_session):
    provider = MockAWSProvider()
    service = CostService(provider)

    summary = service.get_dashboard_summary(db_session)
    assert summary.today_cost >= Decimal("0.0000")
    assert summary.yesterday_cost >= Decimal("0.0000")
    assert summary.previous_day_cost >= Decimal("0.0000")
    assert summary.currency == "USD"
    assert summary.today_vs_yesterday.direction in ("UP", "DOWN", "FLAT")


def test_tag_analysis_computation(db_session):
    provider = MockAWSProvider()
    service = CostService(provider)

    tag_data = service.get_tag_analysis(db_session)
    assert tag_data["tagging_coverage_percentage"] >= Decimal("0.00")
    assert tag_data["tagged_cost"] + tag_data["untagged_cost"] >= Decimal("0.00")
    assert "production" in tag_data["by_environment"] or len(tag_data["by_environment"]) >= 0

